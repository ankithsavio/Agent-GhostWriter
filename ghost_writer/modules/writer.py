from typing import List
from llms.basellm import StructLLM
from langfuse.decorators import observe
from ghost_writer.utils.workers import Message
from ghost_writer.utils.prompt import Prompt
from ghost_writer.utils.diff import Updates, DiffDocument


@observe()
def post_workflow(
    doc: DiffDocument,
    prompt: Prompt,
    conversation: List[Message],
):
    """
    Get suggestions from a particular persona based on their conversation with the expert.
    Args:
        doc (DiffDocument): Diff Document with update history.
        prompt (Prompt): specific prompt for suggestions.
        conversation (List[Message]): conversation history of a persona with an expert.

    """

    formatted_conv = "\n".join(
        f"role: {item['role']}\ncontent: {item['content']}" for item in conversation
    )
    llm = StructLLM(provider="google", temperature=0.7)
    document_updates = llm(
        prompt=str(
            Prompt(
                prompt=str(prompt),
                document=doc(),
                information_seeking_conversation=formatted_conv,
                update_history=doc.update_history,
                instructions="""
                        1. Content Relevance: Ensure added content is high priority and relevant. Focus on information that directly supports the document with the informative conversation.
                        2. New Content: The new information must adhere to the document structure and either replace the previous content or append it.
                        3. Concise Integration: Integrate the information from the conversation concisely and effectively into the document. 
                        4. Updates History: Content that have already been updated and do not need further processing. This content has to be excluded from processing.
                        5. No Further Updates: When there are no more relevant information available to update the document, return empty string for content i.e. {content : ""}
                        6. Important: Strictly adhere to the format provided. Aim for high priority short phrases that needs updates.
                    """,
                format="""
                        1. content: exact phrases from the document that needs to be replaced.
                        2. reason: brief reasoning for replacement based on the information seeking conversation.
                        3. replacement: phrases from the `content` with updates to be replaced.
                    """,
            )
        ),
        format=Updates,
    )
    if not document_updates.content:
        return Updates(
            content="", replacement="", reason="No Suggestions Available"
        ).model_dump()

    return document_updates.model_dump()
