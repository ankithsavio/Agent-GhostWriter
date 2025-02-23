import os
import re
from typing import Union, List, Dict
import pymupdf4llm as pymupdf
from pydantic import BaseModel
from ghost_writer.utils.diff import DiffDocument
from ghost_writer.utils.prompt import Prompt
from ghost_writer.modules.search import SearXNG
from ghost_writer.modules.vectordb import Qdrant
from llms.basellm import TogetherBaseLLM, GeminiBaseStructuredLLM
from langchain_experimental.data_anonymizer import PresidioReversibleAnonymizer
from langchain.text_splitter import RecursiveCharacterTextSplitter


class KnowledgeBaseBuilder:

    def __init__(
        self,
        source: Union[str, List[str]],
        source_name: str,
        model: BaseModel,
        anonymize: bool,
    ):
        self.anonymizer = PresidioReversibleAnonymizer(
            analyzed_fields=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "URL"]
        )
        self.struct_llm = GeminiBaseStructuredLLM()
        self.llm = TogetherBaseLLM()
        self.model = model
        self.search = SearXNG()
        self.vectordb = Qdrant()
        self.collection_name = source_name
        self.vectordb.create_collection(self.collection_name)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=0,
            length_function=len,
            is_separator_regex=False,
            separators=[
                "\n\n",
                "\n",
                ".",
                "\uff0e",
                "\u3002",
                ",",
                "\uff0c",
                "\u3001",
                " ",
                "\u200B",
                "",
            ],
        )
        self.source = self.load_files(source, anonymize=anonymize)

    def load_files(self, items, anonymize=True):
        """
        Load provided pdf file as markdown and remove personal information
        """

        def post_process(doc):
            if anonymize:
                return self.anonymizer.anonymize(doc)
            else:
                return doc

        def load_file(path):
            md = pymupdf.to_markdown(path)
            # hacky fix
            clean_md = re.sub(r"^#\s*", "", md)
            anonymized_md = post_process(clean_md)
            md = f"# {anonymized_md}"

            return DiffDocument(md)

        def load_txt(doc):
            return DiffDocument(post_process(doc))

        if isinstance(items, str):
            if os.path.isfile(items):
                return [load_file(items)]
            else:
                return [load_txt(items)]
        elif isinstance(items, list):
            results = []
            for item in items:
                results.append(*self.load_files(item))
            return results

    def structured_document(self, prompt: Prompt):
        """
        Return structured result for a document
        """
        response = self.struct_llm(
            prompt=str(prompt),
            format=self.model,
        )
        return response

    def query_vectordb(self, queries: List[str]):
        """
        Search your knowledge base
        """
        result_list = []
        for query in queries:
            results = self.vectordb.query_documents(
                self.collection_name, query, limit=2
            )
            result_list.append(
                {
                    "query": query,
                    "result": [result.payload["text"] for result in results],
                }
            )

        return result_list

    def split_and_upload_document(self, doc):
        """
        Turn document into chunks and upload to qdrant collection
        """
        list_chunks = self.text_splitter.split_text(doc)
        list_of_payloads = [{"text": chunk} for chunk in list_chunks]
        self.vectordb.upsert_documents(self.collection_name, list_of_payloads)

    def summarize_search_results(self, results: List[Dict[str, str]]):
        """
        Summarizing content from web search, to avoid context window problem.
        """
        summarized_results = []
        for result in results:
            combined_results = "\n\n".join(str(item) for item in result["result"])
            response = self.llm(
                str(
                    Prompt(
                        prompt="You are a helpful researcher. You are provided with the user query and a list of web search results.",
                        instructions="""
                        1. Summarize the search results into clear and concise overview that directly address the search query.
                        2. Synthesize information from multiple results where appropriate.
                        3. Include citations for key facts and claims. For each piece of information you present, indicate which search result(s) it came from.
                        4. Prioritize information relevance, omit irrelevant or tangential details.
                        5. Maintain a neutral and objective tone.
                        6. If a source is repeated, reuse the same source number.
                        7. The summary should be no more than 500 words followed by Sources.
                        """,
                        user_query=result["query"],
                        result_list=combined_results,
                    )
                )
            )
            summarized_results.append({"summary": response} | result)
        return summarized_results

    def create_knowledge_document(self, gen_prompt: Prompt):
        """
        Create knowledge base document without research / web search
        """

        outline = self.llm(
            str(
                Prompt(
                    prompt=f"Generate an portfolio outline with only the topic headers and sources by following the pydantic config : {str(self.model.model_fields)}",
                    example="""
                    # Title\n
                    ## Subsection Title\n
                    ### Subsubsection Title\n
                    # Sources
                    """,
                )
            )
        )

        self.knowledge_document = self.llm(
            str(gen_prompt) + str(Prompt(prompt="\n", outline=outline))
        )
        self.split_and_upload_document(self.knowledge_document)
        return self.knowledge_document

    def create_knowledge_document_with_research(
        self,
        search_model: BaseModel,
        search_prompt: Prompt,
        gen_prompt: Prompt,
    ):
        """
        Create knowledge base document with research / web search
        """
        outline = self.llm(
            str(
                Prompt(
                    prompt=f"Generate an portfolio outline with only the topic headers and sources by following the pydantic config : {str(self.model.model_fields)}",
                    example="""
                    # Title\n
                    ## Subsection Title\n
                    ### Subsubsection Title\n
                    # Sources
                    """,
                )
            )
        )
        result = self.struct_llm(
            prompt=str(search_prompt),
            format=search_model,
        )

        search_queires = [query for item in result for query in item[1].queries[:2]]
        search_results = self.summarize_search_results(
            self.search.run_many(queries=search_queires)
        )

        self.knowledge_document = outline

        for item in search_results:
            search_results_formatted = f"""<Query>\n{item['query']}\n</Query>\n<Result>\n{item['summary']}\n</Result>"""
            self.knowledge_document = self.llm(
                str(gen_prompt)
                + str(
                    Prompt(
                        promtp="\n",
                        outline=self.knowledge_document,
                        search_results=search_results_formatted,
                    )
                )
            )

        self.split_and_upload_document(self.knowledge_document)
        return self.knowledge_document
