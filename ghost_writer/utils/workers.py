from llms.conversation import ConversationHistory


class Worker:
    def __init__(self, persona: str, role_name: str, description: str):
        self.persona = persona
        self.role = role_name
        self.description = description
        self.conversation = ConversationHistory(name=self.role)
