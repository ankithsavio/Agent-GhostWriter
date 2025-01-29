from langchain.text_splitter import RecursiveCharacterTextSplitter
import requests
import asyncio
from crawl4ai import AsyncWebCrawler
from qdrant_client import QdrantClient


class SearXNG:
    def __init__(self):
        self.instance = "http://localhost:8888/search"
        self.params = {
            "format": "json",
            "categories": "general",
            "language": "en",
        }
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50,
            length_function=len,
        )

        self.vectordb = QdrantClient(url="http://localhost:6333")
        self.collection_name = "WebSearch"

    def get_urls(self, query):
        self.params |= {"q": query}
        try:
            response = requests.get(self.instance, params=self.params)
            response.raise_for_status()

            data = response.json()

            return [result["url"] for result in data["results"]]

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        except KeyError as e:
            print(f"Unexpected JSON format: {e}")

    def get_web_content(self, url: str) -> str:

        async def _crawl():
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(
                    url=url,
                )
                return result

        return asyncio.run(_crawl())

    def process_documents(self, docs):
        # TODO
        pass
