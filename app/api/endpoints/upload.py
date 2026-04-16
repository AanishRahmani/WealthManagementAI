from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
import uuid
import queue
import threading

from app.core.sqlite_db import get_connection, get_client, update_client
from app.core.chroma_db import add_document
from app.services.file_parser import extract_text


router = APIRouter()


UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

task_queue: queue.Queue = queue.Queue()


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".docx",
    ".csv",
    ".xlsx",
    ".xls",
}


def classify_document(filename: str) -> str:
    name = filename.lower()

    if "portfolio" in name:
        return "portfolio_statement"

    if "holding" in name:
        return "portfolio_statement"

    if "brokerage" in name:
        return "portfolio_statement"

    if "statement" in name:
        return "portfolio_statement"

    if "resume" in name:
        return "resume"

    if "tax" in name:
        return "tax_document"

    return "other"


def chunk_text(
    text: str,
    chunk_size: int = 1000,
):
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


def validate_upload(
    file: UploadFile | None,
    notes: str | None,
):
    has_notes = bool(notes and notes.strip())
    has_file = file is not None and bool(file.filename)

    if not has_notes and not has_file:
        raise HTTPException(
            status_code=400,
            detail="Provide notes or upload at least one document.",
        )

    if has_file:
        if file is None:
            raise HTTPException(
                status_code=400,
                detail="No file provided.",
            )

        if file.filename is None:
            raise HTTPException(
                status_code=400,
                detail="Missing filename.",
            )

        ext = Path(file.filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Allowed files: PDF, TXT, DOCX, CSV, XLSX, XLS.",
            )



def process_document(
    client_id: int,
    file_id: int,
    filename: str,
    file_path: str,
    document_type: str,
):
    """
    Parse -> chunk -> ChromaDB
    """
    try:
        text = extract_text(file_path)

        if not text or not text.strip():
            print(f"No extractable text found in {filename}")
            return

        chunks = chunk_text(text)

        ext = Path(filename).suffix.lower()

        for idx, chunk in enumerate(chunks):
            add_document(
                doc_id=f"{file_id}_{idx}_{uuid.uuid4()}",
                text=chunk,
                metadata={
                    "client_id": client_id,
                    "file_id": file_id,
                    "filename": filename,
                    "chunk_index": idx,
                    "source_type": ext.replace(".", ""),
                    "document_type": document_type,
                    "pipeline": "upload",
                },
            )

        print(f"Finished processing {filename}")

    except Exception as e:
        print(f"Processing failed for {filename}: {e}")


def worker():
    while True:
        task = task_queue.get()

        if task is None:
            task_queue.task_done()
            break

        try:
            (
                client_id,
                file_id,
                filename,
                file_path,
                document_type,
            ) = task

            process_document(
                client_id=client_id,
                file_id=file_id,
                filename=filename,
                file_path=file_path,
                document_type=document_type,
            )

        finally:
            task_queue.task_done()


threading.Thread(
    target=worker,
    daemon=True,
).start()


@router.post("/upload")
async def upload_file(
    client_id: int = Form(...),
    client_full_name: str | None = Form(default=None),
    client_goals: str | None = Form(default=None),
    client_notes: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
):
    print(f"DEBUG: Upload request received")
    print(f"DEBUG: client_id = {client_id}")
    print(f"DEBUG: client_full_name = {client_full_name}")
    print(f"DEBUG: client_goals = {client_goals}")
    print(f"DEBUG: client_notes = {client_notes}")
    print(f"DEBUG: file = {file}")
    print(f"DEBUG: file.filename = {file.filename if file else None}")
    print(f"DEBUG: file.content_type = {file.content_type if file else None}")
    
    validate_upload(file, client_notes)

    client_record = get_client(client_id)

    if client_record is None:
        raise HTTPException(
            status_code=404,
            detail="Client not found. Create a client record before uploading files.",
        )

    if client_full_name or client_goals:
        update_client(
            client_id=client_id,
            full_name=client_full_name,
            goals=client_goals,
            portfolio_path=str(Path("data/uploads")),
        )

    if file is None:
        notes_text = (client_notes or "").strip()

        with get_connection() as conn:
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO uploaded_files
                (
                    client_id,
                    filename,
                    filepath,
                    content_type,
                    document_type
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    client_id,
                    "notes_only.txt",
                    "",
                    "text/plain",
                    "notes",
                ),
            )

            file_id = cur.lastrowid

        add_document(
            doc_id=f"{file_id}_notes_{uuid.uuid4()}",
            text=notes_text,
            metadata={
                "client_id": client_id,
                "file_id": file_id,
                "filename": "notes_only.txt",
                "chunk_index": 0,
                "source_type": "notes",
                "document_type": "notes",
                "pipeline": "manual_input",
            },
        )

        return {
            "message": "Notes submitted successfully.",
            "client_id": client_id,
            "file_id": file_id,
            "status": "completed",
        }

    uploaded_file = file

    if uploaded_file.filename is None:
        raise HTTPException(
            status_code=400,
            detail="Missing filename.",
        )

    filename: str = uploaded_file.filename
    
    # Get content type from file or detect from extension
    content_type = uploaded_file.content_type
    if not content_type:
        # Fallback: detect content type from file extension
        ext = Path(filename).suffix.lower()
        content_type_map = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain', 
            '.csv': 'text/csv',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel'
        }
        content_type = content_type_map.get(ext, 'application/octet-stream')
        print(f"DEBUG: Content-type was None, detected from extension: {content_type}")

    file_path = UPLOAD_DIR / filename
    document_type = classify_document(filename)

    with open(file_path, "wb") as f:
        while chunk := await uploaded_file.read(1024 * 1024):
            f.write(chunk)

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO uploaded_files
            (
                client_id,
                filename,
                filepath,
                content_type,
                document_type
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                client_id,
                filename,
                str(file_path),
                content_type,
                document_type,
            ),
        )

        file_id = cur.lastrowid

    task_queue.put(
        (
            client_id,
            file_id,
            filename,
            str(file_path),
            document_type,
        )
    )

    return {
        "message": "File uploaded successfully. Processing queued.",
        "client_id": client_id,
        "file_id": file_id,
        "filename": filename,
        "content_type": content_type,
        "document_type": document_type,
        "status": "queued",
    }
