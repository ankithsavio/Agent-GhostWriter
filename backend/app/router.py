from fastapi import (
    APIRouter,
    File,
    UploadFile,
    WebSocket,
    BackgroundTasks,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse
from backend.engine import WriterEngine, Worker
from typing import List, Dict, Tuple
from pydantic import BaseModel
import queue
import asyncio
import os


class TextInput(BaseModel):
    text: str


class EngineRouter:

    def __init__(self):
        self.router = APIRouter()
        self.engine = WriterEngine()
        self.active_websockets: Dict[str, WebSocket] = {}
        self.document_event = asyncio.Event()
        self.portfolio_event = asyncio.Event()
        self.persona_event = asyncio.Event()
        self.post_workflow_event = asyncio.Event()
        self.register_upload_routes()
        self.register_document_view_routes()
        self.register_conversation_view_routes()
        self.register_restart_route()

    def register_upload_routes(self):

        @self.router.post("/api/upload_documents")
        async def upload_files(
            bgtask: BackgroundTasks,
            doc1: UploadFile = File(...),
            doc2: UploadFile = File(...),
        ):
            """
            Endpoint to handle file uploads and process documents in the background.

            Returns:
                JSONResponse: Response containing success message if successful,
                            or error message with 500 status code if processing fails
            """
            try:
                files = []
                for doc in [doc1, doc2]:
                    content = await doc.read()
                    file_path = os.path.join(
                        "backend/uploads/",
                        doc.filename,
                    )
                    files.append((content, file_path))
                bgtask.add_task(self.gen_user_kb, files)

                return JSONResponse(
                    {
                        "message": "Files processed successfully",
                    }
                )
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        @self.router.post("/api/upload_text")
        async def upload_text(text: TextInput, bgtask: BackgroundTasks):
            """
            Endpoint to handle uploading job description (text) and start application in the background.

            Returns:
                JSONResponse: Response containing success message if successful,
                            or error message with 500 status code if processing fails
            """
            try:
                bgtask.add_task(self.engine.get_job_kb, text.text)
                await self.document_event.wait()
                bgtask.add_task(self.run)
                asyncio.create_task(self.monitor_queue())

                return JSONResponse(
                    {
                        "message": "Text processed successfully",
                    }
                )

            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

    def register_document_view_routes(self):

        @self.router.get("/research_doc")
        async def get_job_research():
            """
            Retrieves the job research data from the agentic research.

            Returns:
                JSONResponse: Response containing either:
                    - The company portfolio data (str)
                    - An error message with a 500 status code on failure
            """

            try:
                if not self.portfolio_event.is_set():
                    await self.portfolio_event.wait()

                return JSONResponse(content={"content": self.engine.company_portfolio})
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        @self.router.get("/resume_report")
        async def get_resume_report():
            """
            Retrieves the resume report after post workflow.

            Returns:
                JSONResponse: Response containing either:
                    - The combined resume report from multiple workers (str)
                    - An error message with a 500 status code on failure
            """

            try:
                if not self.post_workflow_event.is_set():
                    await self.post_workflow_event.wait()

                return JSONResponse(content={"content": self.engine.reports["resume"]})
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        @self.router.get("/cover_letter_report")
        async def get_cover_letter_report():
            """
            Retrieves the cover letter report after post workflow.

            Returns:
                JSONResponse: Response containing either:
                    - The combined cover letter report from multiple workers (str)
                    - An error message with a 500 status code on failure
            """

            try:
                if not self.post_workflow_event.is_set():
                    await self.post_workflow_event.wait()

                return JSONResponse(
                    content={"content": self.engine.reports["cover_letter"]}
                )
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

    def register_conversation_view_routes(self):

        @self.router.get("/conversations")
        async def get_conversation_list(bgtask: BackgroundTasks):
            """
            Retrieves the list of personas from the storm workflow.

            Returns:
                JSONResponse: Response containing either:
                    - List[Persona(persona: str)]
                    - An error message with a 500 status code on failure
            """
            try:
                if not self.persona_event.is_set():
                    await self.persona_event.wait()

                return JSONResponse(
                    content={"content": [persona.role for persona in self.personas]}
                )
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        @self.router.websocket("/ws/conversation/{persona_name}")
        async def get_conversations(websocket: WebSocket, persona_name: str):
            """
            Websocket to retrieve the conversation histroy of a persona from the database.
            The Client uses the list of personas to dynamically create the websockets.

            Returns:
                JSONResponse: Response containing either:
                    - List[Message(role: str, content: str)]
                    - An error message with a 500 status code on failure
            """
            await websocket.accept()
            self.active_websockets[persona_name] = websocket

            if not self.persona_event.is_set():
                await self.persona_event.wait()

            try:
                # Send initial message
                for persona in self.personas:
                    if persona.role == persona_name:
                        messages = persona.conversation.get_messages() or []
                        await websocket.send_json(messages)
                        break

                while True:
                    await asyncio.sleep(0.1)

            except WebSocketDisconnect:
                print(f"Client disconnected: {persona_name}")

            except Exception as e:
                print(f"Error in WebSocket {persona_name}: {e}")

            finally:
                if persona_name in self.active_websockets:
                    del self.active_websockets[persona_name]
                await websocket.close()

    def register_restart_route(self):
        @self.router.post("/restart")
        async def restart():
            """
            Restarts the application by disconnecting websockets and re-initializing the engine.

            Returns:
                JSONResponse: Response containing either:
                    - Success message
                    - An error message with a 500 status code on failure
            """
            try:
                for persona, websocket in self.active_websockets.items():
                    try:
                        await websocket.close(reason="restart")
                        del self.active_websockets[persona]
                    except Exception as e:
                        print(f"Error closing websocket {persona}: {e}")

                for event in [
                    self.document_event,
                    self.portfolio_event,
                    self.persona_event,
                    self.post_workflow_event,
                ]:
                    event.clear()

                self.engine = WriterEngine()

                if hasattr(self, "personas"):
                    delattr(self, "personas")

                return JSONResponse(
                    {
                        "message": "Application restarted successfully",
                    }
                )
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

    async def monitor_queue(self):
        """
        Function to monitor a queue and send real time conversation updates through active websockets.
        """
        while True:
            try:
                try:
                    worker: Worker = self.engine.workflow.queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.1)
                    continue
                websocket = self.active_websockets[worker.role]
                await websocket.send_json(worker.conversation.get_messages())
            except Exception as e:
                print(f"Error sending message from: {e}")

    def gen_user_kb(self, docs: List[Tuple[bytes, os.PathLike]]):
        file_paths = []
        for doc, file_path in docs:
            content = doc
            with open(file_path, "wb") as file:
                file.write(content)
            file_paths.append(file_path)

        self.document_event.clear()
        self.engine.get_user_kb(file_paths)
        self.document_event.set()

    def run(self):
        self.portfolio_event.clear()
        self.engine.load_reports()
        self.engine.create_portfolios()
        self.portfolio_event.set()
        self.start_orchestration()

    def start_orchestration(self):
        self.persona_event.clear()
        self.engine.set_prompts()
        self.personas = self.engine.generate_personas()
        self.persona_event.set()
        self.knowledge_storm(self.personas)

    def knowledge_storm(self, personas: List[Worker]):
        self.post_workflow_event.clear()
        self.engine.parallel_conversation(personas)
        self.engine.post_workflow()
        self.post_workflow_event.set()
