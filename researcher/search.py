from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
import requests
import asyncio
from crawl4ai import AsyncWebCrawler
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from llms.basellm import EmbeddingModel, TogetherBaseLLM
from trafilatura import extract


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

        self.vectordb = QdrantClient(url="http://localhost:6333")
        self.collection_name = "WebSearch"

        if self.vectordb.collection_exists(self.collection_name):
            self.vectordb.delete_collection(self.collection_name)

        self.vectordb.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )

        self.embedding_model = EmbeddingModel()
        self.llm = TogetherBaseLLM()

        self.scraped_urls = []

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
                        "title": web_results[idx].get("title", ""),
                        "url": web_results[idx].get("url", ""),
                        "content": self.clean_html(result),
                    }
                    for idx, result in enumerate(results)
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
                    "chunk": chunk,
                }
                for chunk in chunks
            ]
            doc_list.extend(chunk_list)
        return doc_list

    def upsert_documents(self, doc_list):
        chunks_list = [doc["chunk"] for doc in doc_list]
        embeddings = self.embedding_model(chunks_list)
        points = [
            PointStruct(
                id=idx,
                vector=embedding,
                payload={
                    "title": doc["title"],
                    "url": doc["url"],
                    "text": doc["chunk"],
                },
            )
            for idx, (doc, embedding) in enumerate(zip(doc_list, embeddings))
        ]
        self.vectordb.upsert(collection_name=self.collection_name, points=points)

    def generate_fake_document(self, query):
        """
        HyDE Approach
        """
        prompt = """Given the question '{query}', generate a hypothetical article snippet that \
        directly answers this question. The article snippet should be detailed, in-depth and should directly \
        answer the question. The document size has to be exactly {chunk_size} characters."""

        hy_document = self.llm(prompt.format(query=query, chunk_size=self.chunk_size))

        return hy_document

    def query_documents(self, query):
        doc_query = self.generate_fake_document(query)
        # doc_query = query
        query_emb = self.embedding_model(doc_query)
        results = self.vectordb.query_points(
            collection_name=self.collection_name,
            query=query_emb[0],
            with_vectors=False,
            with_payload=True,
            limit=5,
        )
        return [
            {
                "title": result.payload["title"],
                "url": result.payload["url"],
                "text": result.payload["text"],
            }
            for result in results.points
        ]

    def run(self, query):
        results = self.get_urls(query)
        content_list = self.get_web_content(results)
        self.upsert_documents(self.split_documents(content_list))  # split here
        result = self.query_documents(query)
        return result

    def run_many(self, queries):
        url_list = []
        for query in queries:
            result = self.get_urls(query)
            url_list.extend(result)
        content_list = self.get_web_content(url_list)
        self.upsert_documents(self.split_documents(content_list))
        result_list = []
        for query in queries:
            result = self.query_documents(query)
            result_list.extend({"query": query, "result": result})
        return result_list
