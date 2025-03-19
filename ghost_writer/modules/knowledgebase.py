import os
import re
import pymupdf4llm as pymupdf
from pydantic import BaseModel
from typing import Union, List, Dict, Type, TypeVar
from ghost_writer.utils.diff import DiffDocument
from ghost_writer.utils.prompt import Prompt
from ghost_writer.modules.search import GoogleWeb
from ghost_writer.modules.vectordb import Qdrant
from concurrent.futures import ThreadPoolExecutor, as_completed
from llms.basellm import LLM, StructLLM
from langchain.text_splitter import RecursiveCharacterTextSplitter

T = TypeVar("T", bound=BaseModel)


class KnowledgeBaseBuilder:

    def __init__(
        self,
        source: Union[str, List[str]],
        source_name: str,
        model: BaseModel,
        research: bool,
    ):
        self.struct_llm = StructLLM(provider="google")
        self.llm = LLM(provider="togetherai")
        self.model = model
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
                "\u200b",
                "",
            ],
        )
        self.source = self.load_files(source)
        if research:
            self.search = GoogleWeb()

    def load_files(self, items: Union[str, List[str]]):
        """
        Load and process multiple files or text items into DiffDocument objects.
        Args:
            items (Union[str, List[str]]): File path(s) or text content to load.

        Returns:
            List[DiffDocument]: List of processed DiffDocument objects.
        """

        def load_file(path):
            md = pymupdf.to_markdown(path)
            return DiffDocument(md)

        def load_txt(doc):
            return DiffDocument(doc)

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
        Generates a structured document based on the provided prompt using a language model.
        Args:
            prompt (Prompt): The prompt object containing the text to be structured.

        Returns:
            str: The structured response from the language model following the specified format.

        """

        response = self.struct_llm(
            prompt=str(prompt),
            format=self.model,
        )
        return response

    def query_vectordb(self, queries: List[str]):
        """
        Queries the vector database with a list of queries and returns matching documents.
        Args:
            queries (List[str]): A list of query strings to search for in the vector database.

        Returns:
            List[Dict]: A list of dictionaries containing query results, where each dictionary has:
                - 'query': The original query string
                - 'result': A list of matching document texts (limited to 2 results per query)
        """

        result_list = []
        for query in queries:
            results = self.vectordb.query_documents(
                self.collection_name, query, limit=2
            )
            result_list.append(
                {
                    "query": query,
                    "result": [result.payload["doc"]["text"] for result in results],
                }
            )

        return result_list

    def split_and_upload_document(self, doc):
        """
        Splits a document into chunks and uploads them to the vector database.
        Args:
            doc (str): The document text to be split and uploaded
        """

        list_chunks = self.text_splitter.split_text(doc)
        list_of_payloads = [{"text": chunk} for chunk in list_chunks]
        self.vectordb.upsert_documents(self.collection_name, list_of_payloads)

    def summarize_search_results(self, results: List[Dict[str, str]]):
        """
        Summarizes search results using an LLM to generate concise overviews of web search data.
        Args:
            results (List[Dict[str, str]]): A list of dictionaries containing search results.
                Each dictionary should have:
                - "query": The search query string
                - "result": The raw search results to be summarized

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing the original search data augmented with summaries.
                Each dictionary contains:
                - All original keys from the input dictionary
                - "summary": The LLM-generated summary of the search results

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
        Create a knowledge document using an LLM based on the provided prompt and prepare for RAG.
        Args:
            gen_prompt (Prompt): A Prompt object containing the text prompt for knowledge base creation

        Returns:
            str: The generated knowledge document content.
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
        search_model: Type[T],
        search_prompt: Prompt,
        gen_prompt: Prompt,
    ) -> T:
        """
        Create a knowledge document using an LLM based on the provided prompt with web search and prepare for RAG.
        Args:
        search_model (BaseModel): Pydantic model defining the structure for search results
        search_prompt (Prompt): Prompt template for generating search queries
        gen_prompt (Prompt): Prompt template for generating content from search results

        Returns:
            str: The generated knowledge document
        """
        if not self.search:
            raise ValueError(
                "Research not enabled during the initialization of the knowledge base."
            )

        search_queries = self.struct_llm(
            prompt=str(search_prompt),
            format=search_model,
        )

        result_list = [
            {
                "topic": topic[0],
                "queries": topic[1].queries,
                "results": self.summarize_search_results(
                    self.search.run(query=topic[1].queries)
                ),
            }
            for topic in search_queries
        ]

        self.knowledge_document = ""

        def generate_article_section(topic, search_results):

            document_curation = f"#{topic}\n\n"

            for item in search_results:
                search_results_formatted = f"""<Query>\n{item['query']}\n</Query>\n<Result>\n{item['summary']}\n</Result>"""
                document_curation = self.llm(
                    str(gen_prompt)
                    + str(
                        Prompt(
                            prompt="\n",
                            section=topic,
                            outline=document_curation,
                            search_results=search_results_formatted,
                        )
                    )
                )
            return document_curation

        with ThreadPoolExecutor(len(search_model.model_fields)) as executor:

            future_topics = {
                executor.submit(
                    generate_article_section, result["topic"], result["results"]
                ): result["topic"]
                for result in result_list
            }

            article_dict = {}
            for future in as_completed(future_topics):
                topic = future_topics[future]
                section = future.result()
                article_dict[topic] = section

        for result in result_list:
            self.knowledge_document += article_dict[result["topic"]]

        self.split_and_upload_document(self.knowledge_document)
        return self.knowledge_document
