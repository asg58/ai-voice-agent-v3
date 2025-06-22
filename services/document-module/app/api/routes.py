from fastapi import APIRouter, UploadFile, File

router = APIRouter()

document_router = APIRouter()

@document_router.post("/process")
async def process_document(file: UploadFile = File(...)):
    """Dummy endpoint to process an uploaded document."""
    return {"filename": file.filename, "status": "processed"}
