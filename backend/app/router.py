from fastapi import APIRouter, File, UploadFile, WebSocket, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List
from backend.engine import WriterEngine
import asyncio
import os


class EngineRouter:

    def __init__(self):
        self.router = APIRouter()
        self.engine = WriterEngine()

        self.active_websockets = {"personas": {}, "documents": {}}
        self.portfolio_event = asyncio.Event()
        self.document_event = asyncio.Event()
        self.persona_event = asyncio.Event()
        self.register_routes()

    def register_routes(self):
        @self.router.post("/api/upload_documents")
        async def upload_files(
            bgtask: BackgroundTasks,
            doc1: UploadFile = File(...),
            doc2: UploadFile = File(...),
        ):
            try:

                bgtask.add_task(self.gen_user_kb([doc1, doc2]))

                return JSONResponse(
                    {
                        "message": "Files processed successfully",
                        "filenames": [doc1.filename, doc2.filename],
                    }
                )
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        @self.router.post("/api/upload_text")
        async def upload_text(bgtask: BackgroundTasks, text: str):
            try:
                bgtask.add_task(self.engine.get_job_kb(text))
                bgtask.add_task(self.get_portfolios())
                bgtask.add_task(self.get_personas())
                return JSONResponse(
                    {
                        "message": "Text processed successfully",
                    }
                )

            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        @self.router.get("/research_doc")
        async def get_job_research():
            try:
                if not self.portfolio_event.is_set():
                    await self.portfolio_event.wait()

                return JSONResponse(content={"content": self.engine.company_portfolio})
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        @self.router.get("/conversations")
        async def get_conversation_list():
            try:
                if not self.persona_event.is_set():
                    await self.persona_event.wait()

                return JSONResponse(content={"content": self.personas})
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        @self.router.websocket("/ws/conversation/{persona_name}")
        async def get_conversations(websocket: WebSocket, persona_name: str):
            if not self.persona_event.is_set():
                await self.persona_event.wait()

            await websocket.accept()
            self.active_websockets["personas"][persona_name] = websocket
            for persona in self.personas:
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
            await self.document_event.wait()
            await websocket.accept()
            self.active_websockets["documents"][number] = websocket
            await websocket.send_text(
                self.engine.user_knowledge_base.source[number](deanonymize=True)
            )

    def gen_user_kb(self, docs: List[UploadFile]):
        file_paths = []
        for doc in docs:
            content = asyncio.create_task(doc.read())
            file_path = os.path.join("./", doc.filename)

            with open(file_path, "wb") as file:
                file.write(content)

            file_paths.append(file_path)
        self.document_event.clear()
        self.engine.get_job_kb(file_paths)
        self.document_event.set()

    def get_portfolios(self):
        self.portfolio_event.clear()
        self.engine.create_portfolios()
        self.portfolio_event.set()

    def get_personas(self):
        self.persona_event.clear()
        self.engine.set_prompts()
        self.personas = self.engine.generate_personas()
        self.persona_event.set()
