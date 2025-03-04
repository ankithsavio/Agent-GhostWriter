from fastapi import APIRouter, File, UploadFile, WebSocket, BackgroundTasks
from fastapi.responses import JSONResponse
from backend.engine import WriterEngine, Prompt, post_workflow, Worker
from ghost_writer.utils.logger import log_queue, logger
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
        self.active_websockets: Dict[str, Dict[str, WebSocket]] = {
            "personas": {},
            "documents": {},
        }
        self.document_event = asyncio.Event()
        self.portfolio_event = asyncio.Event()
        self.persona_event = asyncio.Event()
        self.apply_function_event = asyncio.Event()
        self.register_upload_routes()
        self.register_document_view_routes()
        self.register_conversation_view_routes()
        self.register_function_routes()
        self.register_logging_routes()

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

        @self.router.websocket("/api/document/{number}")
        async def view_documents(websocket: WebSocket, number: int):
            """
            Websocket to retrieve the user documents, supports sending constant updates.

            Returns:
                JSONResponse: Response containing either:
                    - List[Message(role: str, content: str)]
                    - An error message with a 500 status code on failure
            """
            await websocket.accept()
            self.active_websockets["documents"][number - 1] = websocket

            if not self.document_event.is_set():
                await self.document_event.wait()

            await websocket.send_text(
                self.engine.user_knowledge_base.source[number - 1](deanonymize=True)
            )

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
                    content={"content": [persona.persona for persona in self.personas]}
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
            self.active_websockets["personas"][persona_name] = websocket

            if not self.persona_event.is_set():
                await self.persona_event.wait()

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

    def register_function_routes(self):

        @self.router.websocket("/ws/suggestions/{persona_name}/{doc_number}")
        async def get_suggestions(
            websocket: WebSocket, persona_name: str, doc_number: int
        ):
            """
            Websocket endpoint to receive document suggestions from a specific persona.

            The client sends a message to request a suggestion, and the server responds
            with the next suggestion in the sequence.

            Returns:
                JSON objects containing Updates for DiffDocument.
            """
            await websocket.accept()
            suggestion_generator = None
            doc = self.engine.user_knowledge_base.source[doc_number - 1]
            prompt = Prompt(
                prompt="You are a Professional Resume Editor, meticulously utilize the information seeking conversation to provide tailored edits for the document."
            )

            try:
                if not self.apply_function_event.is_set():
                    await self.apply_function_event.wait()

                while True:
                    _ = await websocket.receive_json()

                    if suggestion_generator is None:
                        for persona in self.personas:
                            if persona.persona == persona_name:
                                suggestion_generator = post_workflow(
                                    doc,
                                    prompt,
                                    persona.conversation.get_messages(),
                                    10,
                                )
                                break
                    try:
                        next_suggestion = next(suggestion_generator)
                        await websocket.send_json(next_suggestion)
                    except StopIteration:
                        await websocket.send_json(
                            {
                                "message": "No more suggestions available",
                                "end": True,
                            }
                        )

                    await asyncio.sleep(0.1)

            except Exception as e:
                print(f"Suggestion connection closed for {persona_name}: {e}")

    def register_logging_routes(self):
        @self.router.websocket("/api/logs")
        async def send_logs(websocket: WebSocket):
            await websocket.accept()

            try:
                while True:
                    message = await log_queue.get()
                    log_message = f"{message.levelname}: {message.getMessage()}"
                    await websocket.send_json({"log": log_message})
            except Exception as e:
                print(f"Websocket error: {e}")

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
                websocket = self.active_websockets["personas"][worker.persona]
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
        self.apply_function_event.clear()
        self.engine.parallel_conversation(personas)
        self.apply_function_event.set()
