from fastapi import APIRouter, File, UploadFile, WebSocket
from fastapi.responses import JSONResponse
from backend.app_.engine import WriterEngine
import asyncio
import os


class EngineRouter:

    def __init__(self):

        self.router = APIRouter()
        self.engine = WriterEngine()
        self.active_websockets = {}
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
        async def upload_text(text: str):
            try:
                self.engine.get_job_kb(text)
                return JSONResponse(
                    {
                        "message": "Text processed successfully",
                    }
                )

            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        @self.router.get("/research_doc")
        async def get_job_research():
            while not self.engine.company_portfolio:
                await asyncio.sleep(0.1)
            return JSONResponse(content={"content": self.engine.company_portfolio})

        @self.router.websocket("/ws/conversation/{persona_name}")
        async def get_conversations(websocket: WebSocket, persona_name: str):
            while not self.engine.personas:
                await asyncio.sleep(0.1)

            await websocket.accept()
            self.active_websockets["personas"][persona_name] = websocket
            for persona in self.engine.personas:
                if persona.persona == persona_name:
                    await websocket.send_json(persona.conversation.get_messages())
                    break

            try:
                while True:
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Connection closed for {persona_name}: {e}")
            finally:
                del self.active_websockets["personas"][persona_name]

        async def monitor_queue():
            while True:
                try:
                    worker = await self.engine.workflow.queue.get()
                    websocket = self.active_websockets["personas"][worker.persona]
                    await websocket.send_json(worker.conversation.get_messages())
                    self.engine.workflow.queue.task_done()
                except Exception as e:
                    print(f"Error sending message from {worker.persona}: {e}")
                    del self.active_websockets["personas"][worker.persona]
                    self.engine.workflow.queue.task_done()

        asyncio.create_task(monitor_queue())

        @self.router.websocket("/api/document/{number}")
        async def view_documents(websocket: WebSocket, number: int):
            await websocket.accept()
            self.active_websockets["documents"][number] = websocket
            await websocket.send_text(
                self.engine.user_knowledge_base.source[number](deanonymize=True)
            )
