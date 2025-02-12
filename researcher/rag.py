from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from llms.basellm import EmbeddingModel
from typing import List


class Qdrant:
    def __init__(self, collection_name):

        self.client = QdrantClient(url="http://localhost:6333")
        self.collection_name = collection_name
        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(self.collection_name)

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
        self.embedding_model = EmbeddingModel()

    def get_embeddings(self, text_list: List):
        embeddings_list = []
        for i in range(0, len(text_list), 100):
            valid_chunks = text_list[i : i + 100]
            embeddings = self.embedding_model(valid_chunks)
            embeddings_list.extend(embeddings)
        return embeddings_list

    def upsert_documents(self, doc_list):
        """
        Expects a list of payloads.
        """
        chunks_list = [doc["text"] for doc in doc_list]
        embeddings = self.get_embeddings(chunks_list)
        points = [
            PointStruct(
                id=idx,
                vector=embedding,
                payload=doc,
            )
            for idx, (doc, embedding) in enumerate(zip(doc_list, embeddings))
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)

    def query_documents(self, query):
        query_emb = self.embedding_model(query)
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_emb[0],
            with_vectors=False,
            with_payload=True,
            limit=5,
        )
        return [result for result in results.points]
