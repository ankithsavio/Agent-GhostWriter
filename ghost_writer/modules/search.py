from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
import requests
import asyncio
from crawl4ai import AsyncWebCrawler
from llms.basellm import TogetherBaseLLM
from trafilatura import extract
from urllib.parse import urlparse
from researcher.vectordb import Qdrant


class SearXNG:
    def __init__(self):
        self.instance = "http://localhost:8888/search"
        self.params = {
            "format": "json",
            "categories": "general",
            "language": "en",
        }
        self.chunk_size = 2000
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
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
        self.collection_name = "WebSearch"

        self.vectordb = Qdrant()
        self.vectordb.create_collection(self.collection_name)

        self.llm = TogetherBaseLLM()

        self.scraped_urls = []
        self.excluded_urls = ["linkedin.com"]

    def get_domain(self, url):
        parsed_url = urlparse(url)
        return parsed_url.netloc

    def get_urls(self, query, limit=5, **kwargs):
        self.params |= {"q": query, **kwargs}
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
        return extract(
            content.html,
            include_tables=False,
            include_comments=False,
            output_format="txt",
        )

    def get_web_content(self, web_results: List[dict]) -> str:
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
        HyDE Approach
        """
        prompt = """Given the question '{query}', generate a hypothetical article snippet that \
        directly answers this question. The article snippet should be detailed, in-depth and should directly \
        answer the question. The document size has to be exactly {chunk_size} characters."""

        hy_document = self.llm(prompt.format(query=query, chunk_size=self.chunk_size))

        return hy_document

    def format_payloads(self, payloads):
        list_of_payload = [
            {
                "title": result.payload["title"],
                "url": result.payload["url"],
                "text": result.payload["text"],
            }
            for result in payloads
        ]
        return list_of_payload

    def run(self, query):
        results = self.get_urls(query)
        content_list = self.get_web_content(results)
        self.vectordb.upsert_documents(
            self.collection_name, self.split_documents(content_list)
        )  # split here
        result = self.vectordb.query_documents(
            self.collection_name, self.generate_fake_document(query)
        )
        return result

    def run_many(self, queries):
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
