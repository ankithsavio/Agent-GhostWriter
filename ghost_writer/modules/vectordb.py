import spacy
from typing import List, Union, Dict
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

    def create_collection(self, collection_name: str):
        """
        Creates a new collection in the vector database with specified parameters.
        If a collection with the same name already exists, it will be deleted first.
        Args:
            collection_name (str): Name of the collection to be created
        """
        if self.client.collection_exists(collection_name):
            self.client.delete_collection(collection_name)

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )

    def get_embeddings(self, text_list: List):
        """
        Generate embeddings for a list of text chunks using the embedding model.
        Args:
            text_list (List): A list of text chunks to generate embeddings for

        Returns:
            List: A list of embeddings where each embedding is a vector representation
                  of the corresponding text chunk
        """

        embeddings_list = []
        for i in range(0, len(text_list), 100):
            valid_chunks = text_list[i : i + 100]
            embeddings = self.embedding_model(valid_chunks)
            embeddings_list.extend(embeddings)
        return embeddings_list

    def get_entities(self, text: Union[str, List[str]]):
        """
        Extracts named entities from the input text using spaCy NLP model.
        Args:
            text (Union[str, List[str]]): Input text or list of texts to extract entities from.
                If a list is provided, entities will be extracted from each item.

        Returns:
            Union[List[str], List[List[str]]]: A list of unique named entities found in the text.
        """

        if isinstance(text, list):
            return [self.get_entities(item) for item in text]
        elif isinstance(text, str):
            doc = self.nlp(text)
            return list({ent.text for ent in doc.ents})

    def upsert_documents(self, collection_name: str, doc_list: List[Dict[str, str]]):
        """
        Upserts documents into a specified collection in the vector database.
        Args:
            collection_name (str): Name of the collection to upsert documents into
            doc_list (List[Dict[str, str]]): List of documents where each document is a dictionary
                containing at least a "text" key with the document content
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
        Queries the vector database for similar documents based on semantic similarity and named entities.
        Args:
            collection_name (str): Name of the collection to query in the vector database.
            query (str): The search query text.
            limit (int, optional): Maximum number of results to return. Defaults to 5.

        Returns:
            list: List of Point objects containing the matched documents and their metadata.
                 Each Point contains payload with document information.
        """

        query_emb = self.embedding_model(query)
        query_entities = self.get_entities(query)
        filter_conditions = [
            FieldCondition(key="entity", match=MatchValue(value=entity))
            for entity in query_entities
        ]
        query_filter = Filter(should=filter_conditions)
        results = self.client.query_points(
            collection_name=collection_name,
            query=query_emb[0],
            with_vectors=False,
            with_payload=True,
            query_filter=query_filter,
            limit=limit,
        )
        return [result for result in results.points]
