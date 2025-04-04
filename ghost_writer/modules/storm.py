import queue
from typing import Type, TypeVar

import yaml
from langfuse.decorators import langfuse_context, observe
from pydantic import BaseModel

from ghost_writer.utils.persona import Personas
from ghost_writer.utils.prompt import Prompt
from ghost_writer.utils.workers import Worker
from llms.basellm import LLM, StructLLM
from llms.conversation import Message

provider_config = yaml.safe_load(open("config/llms.yaml", "r"))

T = TypeVar("T", bound=BaseModel)


class Storm:
    def __init__(self):
        self.llm = LLM(
            provider=provider_config["llm"]["provider"],
            model=provider_config["llm"]["model"],
        )
        self.struct_llm = StructLLM(
            provider=provider_config["structllm"]["provider"],
            model=provider_config["structllm"]["model"],
        )
        self.queue = queue.Queue()

    @observe()
    def get_personas(self, prompt: Prompt):
        """
        Generates a list of worker personas based on the given prompt.
        Args:
            prompt (Prompt): The prompt object containing requirements for generating personas.

        Returns:
            List[Worker]: A list of Worker objects representing different editor personas,
                         each initialized with properties from the LLM response.
        """
        input_prompt = str(prompt)
        personas_result = self.struct_llm(
            prompt=input_prompt,
            format=Personas,
        )
        langfuse_context.update_current_observation(
            input=input_prompt, output=personas_result
        )
        return [Worker(**persona.model_dump()) for persona in personas_result.editors]

    @observe()
    def get_questions(self, worker: Worker, prompt: Prompt):
        """
        Generates questions based on the given worker and prompt.
        Args:
            worker (Worker): A worker object
            prompt (Prompt): The initial prompt to generate questions from.
        Returns:
            Message: A message object containing the generated response with the worker's persona as role.

        """
        input_prompt = str(prompt) + str(
            Prompt(
                prompt="\n",
                persona=f"""
                        role: {worker.persona} 
                        description: {worker.description} 
                        """,
                conversation_history=worker.conversation.get_messages_as_str(),
                watch=["conversation_history"],
                token_limit=8096,
            )
        )
        response = self.llm(input_prompt)
        message = Message(role=worker.persona, content=response)
        worker.conversation.add_message(message)
        self.push_update(worker)
        langfuse_context.update_current_observation(input=input_prompt, output=response)
        return message

    @observe()
    def get_search_queries(self, worker: Worker, model: Type[T], prompt: Prompt):
        """
        Generate search queries for a vector database based on a worker's conversation and prompt.
        Args:
            worker (Worker): The worker object
            model (BaseModel): The base model to format the response
            prompt (Prompt): Additional prompt parameters to guide query generation

        Returns:
            Response containing generated search queries formatted according to the specified model
        """

        last_message = worker.conversation.get_messages()[-1]
        input_prompt = str(
            Prompt(
                prompt=f"You want to answer the {worker.persona}'s question by querying vector database. What queries would answer the question effectively?",
                question=f"role: {last_message['role']}\ncontent: {last_message['content']}",
            )
        ) + str(prompt)
        response = self.struct_llm(
            input_prompt,
            format=model,
        )
        langfuse_context.update_current_observation(input=input_prompt, output=response)
        return response

    @observe()
    def get_answers(self, worker: Worker, prompt: Prompt):
        """
        Gets answers from the language model (LLM) based on the provided prompt and updates worker's conversation.
        Args:
            worker (Worker): The worker object
            prompt (Prompt): The prompt object containing the prompt for the LLM
        """
        input_prompt = str(prompt) + str(
            Prompt(
                prompt="\n",
                conversation_history=worker.conversation.get_messages(),
                watch=["conversation_history"],
                token_limit=8096,
            )
        )
        response = self.llm(input_prompt)
        message = Message(role="Expert", content=response)
        worker.conversation.add_message(message)
        self.push_update(worker)
        langfuse_context.update_current_observation(input=input_prompt, output=response)

    def push_update(self, worker: Worker):
        """
        Thread safe queue for live updates
        """
        self.queue.put(worker)
