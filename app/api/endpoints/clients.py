from __future__ import annotations

from pathlib import Path
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.sqlite_db import create_client

router = APIRouter(prefix="/clients", tags=["Clients"])

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
}


def validate_photo(file: UploadFile | None) -> None:
    if file is None:
        return

    if file.filename is None:
        raise HTTPException(status_code=400, detail="Missing photo filename.")

    ext = Path(file.filename).suffix.lower()

    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Allowed photo types: PNG, JPG, JPEG, GIF.",
        )


def save_photo_file(client_uuid: str, file: UploadFile) -> str:
    ext = Path(file.filename).suffix.lower()
    filename = f"{client_uuid}{ext}"
    file_path = UPLOAD_DIR / filename

    with open(file_path, "wb") as output_file:
        while chunk := file.file.read(1024 * 1024):
            output_file.write(chunk)

    return str(file_path)


class CreateClientResponse(BaseModel):
    client_id: int
    client_uuid: str
    full_name: str | None = None
    photo_filepath: str | None = None


@router.post("/", response_model=CreateClientResponse, status_code=201)
async def create_new_client(
    full_name: str | None = Form(default=None),
    photo: UploadFile | None = File(default=None),
):
    validate_photo(photo)

    client_uuid = str(uuid.uuid4())
    photo_path: str | None = None

    if photo is not None:
        photo_path = save_photo_file(client_uuid, photo)

    client_id = create_client(
        client_uuid=client_uuid,
        full_name=full_name,
        photo_filepath=photo_path,
    )

    return {
        "client_id": client_id,
        "client_uuid": client_uuid,
        "full_name": full_name,
        "photo_filepath": photo_path,
    }
