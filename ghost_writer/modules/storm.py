from typing import List
from pydantic import BaseModel
from ghost_writer.utils.prompt import Prompt
from ghost_writer.utils.persona import Personas
from ghost_writer.utils.workers import Worker, Message
from ghost_writer.modules.vectordb import Qdrant
from ghost_writer.modules.knowledgebase import KnowledgeBaseBuilder
from llms.basellm import TogetherBaseLLM, GeminiBaseStructuredLLM


class Storm:

    def __init__(self):
        self.llm = TogetherBaseLLM()
        self.struct_llm = GeminiBaseStructuredLLM()

    def get_personas(self, prompt: Prompt):
        """
        Get personas as workers with conversation history
        """
        personas_result = self.struct_llm(
            prompt=str(prompt),
            format=Personas,
        )
        return [Worker(**persona.model_dump()) for persona in personas_result.editors]

    def get_questions(self, worker: Worker, prompt: Prompt):
        """
        Generate questions from the worker
        """
        response = self.llm(
            str(prompt)
            + str(
                Prompt(
                    prompy="\n",
                    persona=f"""
                        role: {worker.persona} 
                        description: {worker.description} 
                        """,
                    conversation_history="\n".join(
                        [
                            f"\nrole : {message.role}\ncontent: {message.content}"
                            for message in worker.conversation.get_messages()
                        ]
                    ),
                )
            )
        )
        message = Message(role=worker.persona, content=response)
        worker.conversation.add_message(message)
        return message

    def get_search_queries(self, worker: Worker, model: BaseModel, prompt: Prompt):
        """
        Get search results from the knowledge base.
        """
        last_message = worker.conversation.get_messages()[-1]
        response = self.struct_llm(
            str(
                Prompt(
                    prompt=f"You want to answer the {worker.persona}'s question by querying vector database. What queries would answer the question effectively?",
                    question=f"role: {last_message.role}\ncontent: {last_message.content}",
                )
            )
            + str(prompt),
            format=model,
        )
        return response

    def get_answers(self, worker: Worker, prompt: Prompt):
        """
        Get search results answered by the expert.
        """
        response = self.llm(str(prompt))
        message = Message(role="Expert", content=response)
        worker.conversation.add_message(message)
