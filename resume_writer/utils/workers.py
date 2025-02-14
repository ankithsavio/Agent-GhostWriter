from llms.conversation import ConversationHistory, Message


class Worker:
    def __init__(self, persona: str, short_summary: str, description: str):
        self.persona = persona
        self.short_summary = short_summary
        self.description = description
        self.conversation = ConversationHistory(name=self.persona)
