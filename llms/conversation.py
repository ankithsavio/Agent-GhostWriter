import os
import uuid
from typing import List
from pymongo import MongoClient
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(".env")


class Message(BaseModel):
    role: str
    content: str


class ConversationHistory:
    """
    Entity based conversation history.
    """

    def __init__(self, name: str):
        url = os.getenv("MONGO_URL")
        self.client = MongoClient(url)
        self.session_id = str(uuid.uuid4())  # entity unique id
        self.db = self.client["Ghost_Writer"]
        self.collection = self.db[name]
        self.collection.create_index("session_id")

    def add_message(self, message: Message):
        """
        Add single message to the database
        Args:
            message (Message): a pydantic model containing the role and the content of the message.
        """
        self.collection.insert_one(
            {
                "session_id": self.session_id,
                "data": {"role": message.role, "content": message.content},
            }
        )

    def add_messages(self, messages: List[Message]):
        """
        Add multiple messages to the database
        Args:
            messages (List[Message]): a list of pydantic model (Messsage).
        """
        for message in messages:
            self.add_message(message)

    def get_messages(self):
        """
        Retreive the entire conversation history of the entity.
        """
        messages = self.collection.find({"session_id": self.session_id})
        return [
            Message(
                role=message["data"]["role"], content=message["data"]["content"]
            ).model_dump()
            for message in messages
        ]

    def clear(self):
        self.collection.delete_many({"session_id": self.session_id})
