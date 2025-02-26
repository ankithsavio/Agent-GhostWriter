from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from backend.app_.engine import WriterEngine
import asyncio
import os


class EngineRouter:

    def __init__(self):

        self.router = APIRouter()
        self.engine = WriterEngine()
        self.register_routes()

    def register_routes(self):
        @self.router.post("/api/upload_documents")
        async def upload_files(
            doc1: UploadFile = File(...), doc2: UploadFile = File(...)
        ):
            try:
                file_paths = []

                for doc in [doc1, doc1]:
                    content = await doc.read()
                    file_path = os.path.join("./", doc.filename)

                    with open(file_path, "wb") as file:
                        file.write(content)

                    file_paths.append(file_path)

                self.engine.get_user_kb(file_paths)

                return JSONResponse(
                    {
                        "message": "Files processed successfully",
                        "filenames": [doc1.filename, doc2.filename],
                    }
                )
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        @self.router.post("/api/upload_text")
        async def upload_file(text: str):
            try:
                self.engine.get_job_kb(text)
                return JSONResponse(
                    {
                        "message": "Text processed successfully",
                    }
                )

            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)
