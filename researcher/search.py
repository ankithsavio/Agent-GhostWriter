from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
import requests
import asyncio
from crawl4ai import AsyncWebCrawler
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from llms.basellm import EmbeddingModel, HfBaseLLM


class SearXNG:
    def __init__(self):
        self.instance = "http://localhost:8888/search"
        self.params = {
            "format": "json",
            "categories": "general",
            "language": "en",
        }
        self.chunk_size = 1000
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=100,
            length_function=len,
        )

        self.vectordb = QdrantClient(url="http://localhost:6333")
        self.collection_name = "WebSearch"

        if not self.vectordb.collection_exists(self.collection_name):
            self.vectordb.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )

        self.embedding_model = EmbeddingModel()
        self.llm = HfBaseLLM()

    def get_urls(self, query, **kwargs):
        self.params |= {"q": query, **kwargs}
        try:
            response = requests.get(self.instance, params=self.params)
            response.raise_for_status()

            data = response.json()

            return [result["url"] for result in data["results"]]

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        except KeyError as e:
            print(f"Unexpected JSON format: {e}")

    def get_web_content(self, urls: List[str]) -> str:

        async def _crawl():
            async with AsyncWebCrawler() as crawler:
                result = []
                for url in urls:
                    res = await crawler.arun(
                        url=url,
                    )
                    result.append(res.markdown)
                return result

        return asyncio.run(_crawl())

    def upsert_documents(self, doc):
        chunks = self.text_splitter.split_text(doc)
        chunks_dict = [{"id": idx, "text": chunk} for idx, chunk in enumerate(chunks)]
        embeddings = self.embedding_model(chunks[:100])
        points = [
            PointStruct(id=doc["id"], vector=embedding, payload={"text": doc["text"]})
            for doc, embedding in zip(chunks_dict, embeddings)
        ]
        self.vectordb.upsert(collection_name=self.collection_name, points=points)

    def generate_fake_document(self, query):
        """
        HyDE Approach
        """
        prompt = """Given the question '{query}', generate a hypothetical document that \
        directly answers this question. The document should be detailed and in-depth.the \
        document size has to be exactly {chunk_size} characters."""

        hy_document = self.llm(prompt.format(query=query, chunk_size=self.chunk_size))

        return hy_document

    def search_web(self, query, **kwargs):
        urls = self.get_urls(query, **kwargs)
        docs = self.get_web_content(urls)
        self.upsert_documents("####".join(docs))

    def query_documents(self, query):
        doc_query = self.generate_fake_document(query)
        query_emb = self.embedding_model(doc_query)
        results = self.vectordb.query_points(
            collection_name=self.collection_name,
            query=query_emb[0],
            with_vectors=False,
            with_payload=True,
            limit=10,
        )
        return results
