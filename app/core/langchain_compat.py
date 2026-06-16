from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Protocol

try:
    from langchain_core.documents import Document as LCDocument
    from langchain_core.embeddings import Embeddings as LCEmbeddings
    from langchain_core.prompts import ChatPromptTemplate as LCChatPromptTemplate
    from langchain_core.vectorstores import InMemoryVectorStore as LCInMemoryVectorStore
    from langchain_text_splitters import RecursiveCharacterTextSplitter as LCRecursiveCharacterTextSplitter

    Document = LCDocument
    Embeddings = LCEmbeddings
    ChatPromptTemplate = LCChatPromptTemplate
    InMemoryVectorStore = LCInMemoryVectorStore
    RecursiveCharacterTextSplitter = LCRecursiveCharacterTextSplitter
    LANGCHAIN_AVAILABLE = True
except ModuleNotFoundError:
    LANGCHAIN_AVAILABLE = False

    @dataclass
    class Document:
        page_content: str
        metadata: dict[str, Any] = field(default_factory=dict)

    class Embeddings(Protocol):
        def embed_documents(self, texts: List[str]) -> List[List[float]]: ...
        def embed_query(self, text: str) -> List[float]: ...

    class _PromptValue:
        def __init__(self, text: str):
            self.text = text

        def to_string(self) -> str:
            return self.text

    class ChatPromptTemplate:
        def __init__(self, messages):
            self.messages = messages

        @classmethod
        def from_messages(cls, messages):
            return cls(messages)

        def invoke(self, values: dict[str, str]):
            system = self.messages[0][1]
            human = self.messages[1][1].format(**values)
            return _PromptValue(f"System: {system}\n\nHuman: {human}")

    class RecursiveCharacterTextSplitter:
        def __init__(self, chunk_size: int, chunk_overlap: int, separators=None):
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap

        def split_text(self, text: str) -> list[str]:
            cleaned = " ".join(text.split())
            if not cleaned:
                return []
            chunks = []
            start = 0
            while start < len(cleaned):
                end = min(start + self.chunk_size, len(cleaned))
                chunks.append(cleaned[start:end])
                if end == len(cleaned):
                    break
                start = end - self.chunk_overlap
            return chunks
