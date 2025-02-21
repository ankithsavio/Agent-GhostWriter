from pydantic import BaseModel
from ghost_writer.utils.prompt import Prompt
from ghost_writer.utils.workers import Worker, Message
from ghost_writer.modules.knowledgebase import KnowledgeBaseBuilder
from llms.basellm import TogetherBaseLLM, GeminiBaseStructuredLLM


class Storm:

    def __init__(self):
        self.llm = TogetherBaseLLM()
        self.struct_llm = GeminiBaseStructuredLLM()

    def get_personas(self, model: BaseModel, prompt: Prompt):
        """
        Get personas as workers with conversation history
        """
        personas_result = self.struct_llm(
            prompt=str(prompt),
            format=model,
        )
        return [Worker(**persona.model_dump()) for persona in personas_result.editors]

    def get_questions(self, worker: Worker, prompt: Prompt):
        """
        Generate questions from the worker
        """
        response = self.llm(str(prompt))
        message = Message(role=worker.persona, content=response)
        worker.conversation.add_message(message)
        return message

    def get_search_result(
        self,
        model: BaseModel,
        knowledge_base: KnowledgeBaseBuilder,
        prompt: Prompt,
    ):
        """
        Get search results from the knowledge base.
        """
        response = self.struct_llm(
            str(prompt),
            format=model,
        )
        return knowledge_base.query_vectordb(**response.model_dump())

    def get_answers(self, worker: Worker, prompt: Prompt):
        """
        Get search results answered by the expert.
        """
        response = self.llm(str(prompt))
        message = Message(role="Expert", content=response)
        worker.conversation.add_message(message)
