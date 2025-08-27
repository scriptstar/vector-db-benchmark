"""
ChromaDB client for benchmarking using ChromaDB v2 HTTP API
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
from .base import VectorDB

class ChromaDB(VectorDB):
    def __init__(self, host: str = "localhost", port: int = 8001, collection_name: str = "music_embeddings"):
        """
        Initialize ChromaDB client with HTTP connection.
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.client = chromadb.HttpClient(
            host=self.host,
            port=self.port,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        # Test connection with v2 API
        response = self.client.heartbeat()
        if not isinstance(response, int):
            raise Exception("ChromaDB v2 connection failed")

    def close(self):
        """
        The chromadb HTTP client does not need to be explicitly closed.
        This method is a no-op to prevent issues with the benchmark script's
        calling order.
        """
        pass

    def setup(self, dim: int):
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass # Collection doesn't exist, which is fine
        
        # ChromaDB v2 API - create collection with embedding function
        self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
            # v2 handles dimensions automatically based on embeddings
        )

    def upsert(self, vectors: List[List[float]], payloads: List[Dict[str, Any]]):
        if len(vectors) != len(payloads):
            raise ValueError("Number of vectors must match number of payloads")
        
        collection = self.client.get_collection(self.collection_name)
        
        ids = [str(p.get("row_id", i)) for i, p in enumerate(payloads)]
        documents = [p.get("text", f"Track: {p.get('track', 'Unknown')}") for p in payloads]
        metadatas = []
        for payload in payloads:
            clean_metadata = {k: (str(v) if not isinstance(v, (str, int, float, bool)) else v) for k, v in payload.items() if v is not None}
            metadatas.append(clean_metadata)
        
        batch_size = 1000
        for i in range(0, len(vectors), batch_size):
            end_idx = min(i + batch_size, len(vectors))
            try:
                collection.upsert(
                    embeddings=vectors[i:end_idx],
                    documents=documents[i:end_idx],
                    metadatas=metadatas[i:end_idx],
                    ids=ids[i:end_idx]
                )
            except Exception:
                collection.add(
                    embeddings=vectors[i:end_idx],
                    documents=documents[i:end_idx],
                    metadatas=metadatas[i:end_idx],
                    ids=ids[i:end_idx]
                )

    def search(self, query: List[float], top_k: int) -> List[Dict[str, Any]]:
        collection = self.client.get_collection(self.collection_name)
        
        results = collection.query(
            query_embeddings=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        formatted_results = []
        if results and len(results.get("ids", [])) > 0:
            ids, distances, metadatas = results["ids"][0], results.get("distances", [[]])[0], results.get("metadatas", [[]])[0]
            for i in range(len(ids)):
                score = 1.0 - (distances[i] if i < len(distances) else 1.0)
                formatted_results.append({
                    "id": ids[i],
                    "score": score,
                    "payload": metadatas[i] if i < len(metadatas) else {}
                })
        return formatted_results

    def teardown(self):
        try:
            self.client.delete_collection(self.collection_name)
        except Exception as e:
            print(f"Warning: Error during ChromaDB teardown: {e}")
