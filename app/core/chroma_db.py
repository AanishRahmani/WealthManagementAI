import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from pathlib import Path
from datetime import datetime, UTC
from typing import Any, cast

CHROMA_DIR = Path("data/chroma")
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

client: ClientAPI | None = None
collection: Collection | None = None


# Init / Shutdown


def init_chroma() -> None:
    global client, collection

    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    client = chroma_client

    collection = chroma_client.get_or_create_collection(name="client_documents")


def close_chroma() -> None:
    global client, collection

    collection = None
    client = None


# Core Accessor


def get_collection() -> Collection:
    if collection is None:
        raise RuntimeError("ChromaDB not initialized.")

    return collection


# Insert


def add_document(
    doc_id: str,
    text: str,
    metadata: dict[str, Any],
) -> None:
    col = get_collection()

    payload = dict(metadata)

    payload.setdefault(
        "created_at",
        datetime.now(UTC).isoformat(),
    )

    col.add(
        ids=[doc_id],
        documents=[text],
        metadatas=[payload],
    )


# Semantic Search


def query_documents(
    query: str,
    n_results: int = 5,
) -> dict[str, Any]:
    col = get_collection()

    result = col.query(
        query_texts=[query],
        n_results=n_results,
    )

    return cast(dict[str, Any], result)


# Get by ID


def get_document(
    doc_id: str,
) -> dict[str, Any]:
    col = get_collection()

    result = col.get(
        ids=[doc_id],
        include=[
            "documents",
            "metadatas",
        ],
    )

    return cast(dict[str, Any], result)


# Get by Client


def get_documents_by_client(
    client_id: int,
) -> dict[str, Any]:
    col = get_collection()

    result = col.get(
        where={"client_id": client_id},
        include=[
            "documents",
            "metadatas",
        ],
    )

    return cast(dict[str, Any], result)


# Get by File


def get_documents_by_file(
    file_id: int,
) -> dict[str, Any]:
    col = get_collection()

    result = col.get(
        where={"file_id": file_id},
        include=[
            "documents",
            "metadatas",
        ],
    )

    return cast(dict[str, Any], result)


# Get by Document Type


def get_documents_by_type(
    client_id: int,
    document_type: str,
) -> dict[str, Any]:
    col = get_collection()

    result = col.get(
        where={
            "$and": [
                {"client_id": client_id},
                {"document_type": document_type},
            ]
        },
        include=[
            "documents",
            "metadatas",
        ],
    )

    return cast(dict[str, Any], result)


# Delete


def delete_document(
    doc_id: str,
) -> None:
    col = get_collection()

    col.delete(ids=[doc_id])


def delete_documents_by_client(
    client_id: int,
) -> None:
    col = get_collection()

    col.delete(where={"client_id": client_id})


# Debug / Stats


def count_documents() -> int:
    col = get_collection()

    return int(col.count())


def peek_documents(
    limit: int = 5,
) -> dict[str, Any]:
    col = get_collection()

    result = col.peek(limit=limit)

    return cast(dict[str, Any], result)
