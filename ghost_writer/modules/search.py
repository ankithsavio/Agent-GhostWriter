import uuid
import time
import requests
import asyncio
import random
from typing import List
from trafilatura import extract
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler
from ghost_writer.modules.vectordb import Qdrant
from llms.basellm import TogetherBaseLLM
from langchain.text_splitter import RecursiveCharacterTextSplitter


class SearXNG:
    def __init__(self):
        """
        Initialize the search module.
        """
        self.instance = "http://localhost:8888/search"
        self.params = {
            "format": "json",
            "categories": "general",
            "language": "en",
        }
        self.chunk_size = 2000
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
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
        self.collection_name = "WebSearch" + str(uuid.uuid4())

        self.vectordb = Qdrant()
        self.vectordb.create_collection(self.collection_name)

        self.llm = TogetherBaseLLM()

        self.scraped_urls = []
        self.excluded_urls = ["linkedin.com"]

    def get_domain(self, url):
        """
        Extracts the domain name from a given URL.
        Args:
            url (str): The URL to parse.
        Returns:
            str: The domain name (netloc) portion of the URL.
        """

        parsed_url = urlparse(url)
        return parsed_url.netloc

    def get_urls(self, query, limit=3, **kwargs):
        """
        Fetch search results from a specified search engine instance based on the given query.
        Args:
            query (str): The search query string to be executed
            limit (int, optional): Maximum number of results to return. Defaults to 5.
            **kwargs: Additional parameters to be passed to the search request

        Returns:
            list: A list of dictionaries containing search results. Each dictionary contains:
                - title (str): Title of the search result
                - url (str): URL of the search result
                Results are filtered to exclude previously scraped URLs and excluded domains.
                Maximum length is determined by limit parameter.
        """
        self.params |= {"q": query, **kwargs}

        delay = random.uniform(1, 5)
        time.sleep(delay)

        try:
            response = requests.get(self.instance, params=self.params)
            response.raise_for_status()

            data = response.json()

            return [
                {"title": result.get("title", ""), "url": result.get("url", "")}
                for result in data["results"]
                if result["url"] not in self.scraped_urls
                and self.get_domain(result["url"]) not in self.excluded_urls
            ][:limit]

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        except KeyError as e:
            print(f"Unexpected JSON format: {e}")

    def clean_html(self, content):
        """
        Cleans HTML content by extracting plain text.
        Args:
            content: The HTML content to be cleaned. Expected to be a BeautifulSoup object with html attribute.

        Returns:
            str: The extracted plain text content with tables and comments removed.
        """

        return extract(
            content.html,
            include_tables=False,
            include_comments=False,
            output_format="txt",
        )

    def get_web_content(self, web_results: List[dict]) -> str:
        """
        Extracts and processes web content from a list of URLs using asynchronous web crawling.
        This method crawls multiple web pages simultaneously, extracts their content based on
        specified CSS selectors and filters, and returns the cleaned results.
        Args:
            web_results (List[dict]): A list of dictionaries containing web search results.
                Each dictionary should have 'url' and optionally 'title' keys.

        Returns:
            List[dict]: A list of dictionaries containing processed web content.
            Each dictionary contains:
                - title (str): The title of the webpage
                - url (str): The URL of the webpage
                - content (str): The cleaned and processed content from the webpage
        """

        urls = [item["url"] for item in web_results]
        self.scraped_urls.extend(urls)

        async def _crawl():
            async with AsyncWebCrawler(headless=True, sleep_on_close=True) as crawler:
                results = await crawler.arun_many(
                    urls=urls,
                    css_selector="main.content",
                    word_count_threshold=50,
                    excluded_tags=[
                        "form",
                        "header",
                        "footer",
                        "nav",
                    ],
                    exclude_external_links=True,
                    exclude_social_media_links=True,
                    exclude_external_images=True,
                    html2text={
                        "escape_dot": False,
                    },
                )

                return [
                    {
                        "title": web_result.get("title", ""),
                        "url": web_result.get("url", ""),
                        "content": self.clean_html(result),
                    }
                    for web_result, result in zip(web_results, results)
                    if result
                ]

        return asyncio.run(_crawl())

    def split_documents(self, content_list):
        """
        Split documents into smaller chunks for processing.
        Args:
            content_list (list): A list of dict containing document content.
                                Each dict should have 'content', 'title' (optional),
                                and 'url' (optional) keys.

        Returns:
            list: A list of dictionaries, each containing:
                  - title (str): The original document's title
                  - url (str): The original document's URL
                  - text (str): A chunk of the original document's content

        """

        doc_list = []
        for content in content_list:
            chunks = self.text_splitter.split_text(content.get("content"))
            chunk_list = [
                {
                    "title": content.get("title", ""),
                    "url": content.get("url", ""),
                    "text": chunk,
                }
                for chunk in chunks
            ]
            doc_list.extend(chunk_list)
        return doc_list

    def generate_fake_document(self, query):
        """
        Generates a hypothetical document using the HyDE (Hypothetical Document Embedding) approach.
        Args:
            query (str): The query or question for which a hypothetical document needs to be generated.

        Returns:
            str: A hypothetical document snippet that answers the query, with length equal to chunk_size.
        """
        prompt = """Given the question '{query}', generate a hypothetical article snippet that \
        directly answers this question. The article snippet should be detailed, in-depth and should directly \
        answer the question. The document size has to be exactly {chunk_size} characters."""

        hy_document = self.llm(prompt.format(query=query, chunk_size=self.chunk_size))

        return hy_document

    def format_payloads(self, payloads):
        """
        Format a list of search result payloads into a simplified list of dict for vector database.
        Args:
            payloads: An iterable of search result objects containing payload data with title, url and text fields.

        Returns:
            list: A list of dict, where each dict contains:
                - title (str): The title of the search result
                - url (str): The URL of the search result
                - text (str): The text content of the search result
        """

        list_of_payload = [
            {
                "title": result.payload["doc"]["title"],
                "url": result.payload["doc"]["url"],
                "text": result.payload["doc"]["text"],
            }
            for result in payloads
        ]
        return list_of_payload

    def run(self, query):
        """
        Executes a web search, retrieves content, and performs vector database operations.
        Args:
            query (str): The search query string to be processed

        Returns:
            list: A list of relevant document matches from the vector database query
        """

        results = self.get_urls(query)
        content_list = self.get_web_content(results)
        self.vectordb.upsert_documents(
            self.collection_name, self.split_documents(content_list)
        )
        result = self.vectordb.query_documents(
            self.collection_name, self.generate_fake_document(query)
        )
        return result

    def run_many(self, queries):
        """
        Process multiple search queries, fetch web content, and store in vector database.
        See run method.
        """

        url_list = []
        for query in queries:
            result = self.get_urls(query)
            url_list.extend(result)
        content_list = self.get_web_content(url_list)
        self.vectordb.upsert_documents(
            self.collection_name, self.split_documents(content_list)
        )
        result_list = []
        for query in queries:
            result = self.vectordb.query_documents(
                self.collection_name, self.generate_fake_document(query)
            )
            result_list.append({"query": query, "result": self.format_payloads(result)})
        return result_list
