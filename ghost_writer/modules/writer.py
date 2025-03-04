from typing import List
from llms.basellm import GeminiBaseStructuredLLM
from ghost_writer.utils.workers import Message
from ghost_writer.utils.prompt import Prompt
from ghost_writer.utils.diff import Updates, DiffDocument


def post_workflow(
    doc: DiffDocument,
    prompt: Prompt,
    conversation: List[Message],
    max_iter: int = 10,
):

    formatted_conv = "\n".join(
        f"role: {item.role}\ncontent: {item.content}" for item in conversation
    )
    updated_content = ""
    llm = GeminiBaseStructuredLLM()
    iteration = 0
    while iteration < max_iter:
        iteration += 1
        document_updates = llm(
            prompt=str(
                Prompt(
                    prompt=str(prompt),
                    document=doc(),
                    information_seeking_conversation=formatted_conv,
                    update_history=updated_content,
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
            break
        updated_content += document_updates.content
        doc.apply(document_updates)
        yield document_updates.model_dump()
