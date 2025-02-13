from llms.conversation import ConversationHistory


class Worker:
    def __init__(self, persona: str, short_summary: str, description: str):
        self.persona = persona
        self.short_summary = short_summary
        self.description = description
        self.conversation_history = ConversationHistory(name=self.short_summary)
