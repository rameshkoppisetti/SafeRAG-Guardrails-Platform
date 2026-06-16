from fastapi import APIRouter, Depends, Request

from app.models.requests import IngestDocumentRequest
from app.models.responses import IngestDocumentResponse
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/documents", tags=["documents"])


def get_ingestion_service(request: Request):
    return request.app.state.ingestion_service


@router.post("/ingest", response_model=IngestDocumentResponse)
def ingest_document(payload: IngestDocumentRequest, svc: IngestionService = Depends(get_ingestion_service)):
    accepted, blocked = svc.ingest(
        document_id=payload.document_id,
        tenant_id=payload.tenant_id,
        text=payload.text,
        acl=payload.acl,
    )
    return IngestDocumentResponse(
        document_id=payload.document_id,
        accepted_chunks=accepted,
        blocked_chunks=blocked,
    )
