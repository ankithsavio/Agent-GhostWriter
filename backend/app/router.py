from fastapi import APIRouter, File, UploadFile, WebSocket, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from backend.engine import WriterEngine
from tests.test_engine import FakeEngine
import asyncio
import os


class TextInput(BaseModel):
    text: str


class EngineRouter:

    def __init__(self):
        self.router = APIRouter()
        self.engine = FakeEngine()

        self.active_websockets = {"personas": {}, "documents": {}}
        self.portfolio_event = asyncio.Event()
        self.document_event = asyncio.Event()
        self.persona_event = asyncio.Event()
        self.final_event = asyncio.Event()
        self.register_routes()

    def register_routes(self):
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
                bgtask.add_task(self.get_portfolios)
                bgtask.add_task(self.get_personas)
                bgtask.add_task(asyncio.run, monitor_queue()) # TODO fix
                return JSONResponse(
                    {
                        "message": "Text processed successfully",
                    }
                )

            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

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

        def monitor_queue():
            """
            Function to monitor a queue and send real time conversation updates through active websockets.
            """
            while True:
                try:
                    worker = self.engine.workflow.queue.get()
                    websocket = self.active_websockets["personas"][worker.persona]
                    asyncio.run(websocket.send_json(worker.conversation.get_messages()))
                    self.engine.workflow.queue.task_done()
                except Exception as e:
                    print(f"Error sending message from: {e}")
                    # del self.active_websockets["personas"][worker.persona]
                    # self.engine.workflow.queue.task_done()

        @self.router.websocket("/api/document/{number}")
        async def view_documents(websocket: WebSocket, number: int):
            """
            Websocket to retrieve the user documents, supports sending constant updates.

            Returns:
                JSONResponse: Response containing either:
                    - List[Message(role: str, content: str)]
                    - An error message with a 500 status code on failure
            """
            await self.document_event.wait()
            await websocket.accept()
            self.active_websockets["documents"][number - 1] = websocket
            await websocket.send_text(
                self.engine.user_knowledge_base.source[number - 1](deanonymize=True)
            )

        @self.router.websocket("/ws/suggestions/{persona_name}/{doc_number}")
        async def get_suggestions(
            websocket: WebSocket, persona_name: str, doc_number: int
        ):
            """
            Websocket endpoint to receive document suggestions from a specific persona.

            Returns:
                JSON objects containing Updates for DiffDocument.
            """
            await websocket.accept()

            if not self.final_event.is_set():
                await self.final_event.wait()

            try:
                for persona in self.personas:
                    if persona.persona == persona_name:
                        suggestions = self.engine.get_suggestions_from_persona(
                            persona, doc_number
                        )
                        for suggestion in suggestions:
                            await websocket.send_json(suggestion)
                        break

                while True:
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Suggestion connection closed for {persona_name}: {e}")

    def gen_user_kb(self, docs: List[bytes]):
        file_paths = []
        for doc, file_path in docs:
            content = doc
            with open(file_path, "wb") as file:
                file.write(content)
            file_paths.append(file_path)

        self.document_event.clear()
        self.engine.get_user_kb(file_paths)
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
        self.final_event.clear()
        self.final_event.set()
