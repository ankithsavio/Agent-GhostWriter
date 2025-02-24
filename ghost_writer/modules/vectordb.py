import spacy
from typing import List
from llms.basellm import EmbeddingModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)


class Qdrant:
    def __init__(self):

        self.client = QdrantClient(url="http://localhost:6333")
        self.embedding_model = EmbeddingModel()
        self.nlp = spacy.load("en_core_web_sm")

    def create_collection(self, collection_name):
        if self.client.collection_exists(collection_name):
            self.client.delete_collection(collection_name)

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )

    def get_embeddings(self, text_list: List):
        """
        Get embeddings from Gemini text-embedding
        """
        embeddings_list = []
        for i in range(0, len(text_list), 100):
            valid_chunks = text_list[i : i + 100]
            embeddings = self.embedding_model(valid_chunks)
            embeddings_list.extend(embeddings)
        return embeddings_list

    def get_entities(self, text):
        """
        NER from spacy
        """
        if isinstance(text, list):
            return [self.get_entities(item) for item in text]
        elif isinstance(text, str):
            doc = self.nlp(text)
            return list({ent.text for ent in doc.ents})

    def upsert_documents(self, collection_name, doc_list):
        """
        Expects a list of payloads.
        """
        chunks_list = [doc["text"] for doc in doc_list]
        embeddings = self.get_embeddings(chunks_list)
        entities_list = self.get_entities(chunks_list)
        points = [
            PointStruct(
                id=idx,
                vector=embedding,
                payload={"doc": doc, "entity": entity},
            )
            for idx, (doc, embedding, entity) in enumerate(
                zip(doc_list, embeddings, entities_list)
            )
        ]
        self.client.upsert(collection_name=collection_name, points=points)

    def query_documents(self, collection_name, query, limit=5):
        """
        query documents with metadata filtering of NER entities
        """
        query_emb = self.embedding_model(query)
        query_entities = self.get_entities(query)
        filter_conditions = [
            FieldCondition(key="entities", match=MatchValue(value=entity))
            for entity in query_entities
        ]
        query_filter = Filter(should=filter_conditions, minimum_should_match=1)
        results = self.client.query_points(
            collection_name=collection_name,
            query=query_emb[0],
            with_vectors=False,
            with_payload=True,
            query_filter=query_filter,
            limit=limit,
        )
        return [result for result in results.points]
