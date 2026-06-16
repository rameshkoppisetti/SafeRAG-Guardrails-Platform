from app.core.langchain_compat import Document, RecursiveCharacterTextSplitter

from app.repositories.langchain_vector_repository import LangChainVectorRepository
from app.services.audit_service import AuditService
from app.services.guardrail_service import GuardrailService
from app.services.pii_scanner import PiiScanner
from app.services.secret_scanner import SecretScanner
from app.utils.hashing import sha256_text


class IngestionService:
    def __init__(
        self,
        chunk_size: int,
        chunk_overlap: int,
        secret_scanner: SecretScanner,
        pii_scanner: PiiScanner,
        guardrail: GuardrailService,
        vector_repo: LangChainVectorRepository,
        audit: AuditService,
    ):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self.secret_scanner = secret_scanner
        self.pii_scanner = pii_scanner
        self.guardrail = guardrail
        self.vector_repo = vector_repo
        self.audit = audit

    def ingest(self, document_id: str, tenant_id: str, text: str, acl: list[str]) -> tuple[int, int]:
        accepted = 0
        blocked = 0
        chunks = self.text_splitter.split_text(text)
        docs_to_add: list[Document] = []
        ids_to_add: list[str] = []

        safe_acl = acl or ["__public__"]

        for idx, raw_chunk in enumerate(chunks):
            chunk_hash = sha256_text(raw_chunk)[:16]
            chunk_id = f"{document_id}:{idx}:{chunk_hash}"

            secret_result = self.secret_scanner.scan(raw_chunk)
            if secret_result.has_secret:
                blocked += 1
                self.audit.record(
                    "CHUNK_BLOCKED_SECRET",
                    document_id=document_id,
                    chunk_id=chunk_id,
                    secret_types=secret_result.types,
                )
                continue

            pii_result = self.pii_scanner.scan_and_redact(raw_chunk)
            guardrail_result = self.guardrail.validate_input(pii_result.redacted_text)
            if not guardrail_result.allowed:
                blocked += 1
                self.audit.record(
                    "CHUNK_BLOCKED_GUARDRAIL",
                    document_id=document_id,
                    chunk_id=chunk_id,
                    action=guardrail_result.action,
                )
                continue

            safe_text = guardrail_result.text
            docs_to_add.append(
                Document(
                    page_content=safe_text,
                    metadata={
                        "chunk_id": chunk_id,
                        "document_id": document_id,
                        "tenant_id": tenant_id,
                        "acl": safe_acl,
                        "chunk_index": idx,
                        "pii_detected": pii_result.has_pii,
                        "pii_types": pii_result.types,
                        "secret_detected": False,
                        "guardrail_checked": True,
                    },
                )
            )
            ids_to_add.append(chunk_id)
            accepted += 1
            self.audit.record(
                "CHUNK_READY_FOR_INDEX",
                document_id=document_id,
                chunk_id=chunk_id,
                pii_detected=pii_result.has_pii,
                pii_types=pii_result.types,
            )

        if docs_to_add:
            self.vector_repo.add_documents(docs_to_add, ids_to_add)
            for chunk_id in ids_to_add:
                self.audit.record("CHUNK_INDEXED", document_id=document_id, chunk_id=chunk_id)

        return accepted, blocked
