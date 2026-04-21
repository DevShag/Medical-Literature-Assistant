from qdrant_client import QdrantClient
from openai import OpenAI
from backend.config import settings
from typing import List, Dict, Any
import json

class RAGEngine:
    def __init__(self):
        #self.client = QdrantClient(path=settings.QDRANT_PATH)
        self.client = QdrantClient(
            host = settings.QDRANT_HOST,
            port = settings.QDRANT_PORT
        )
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.cache = {}  # Simple in-memory cache for demonstration



    def get_embedding(self, text: str) -> List[float]:
        response = self.openai_client.embeddings.create(
            input= [text],
            model= settings.EMBEDDING_MODEL
        )
        return response.data[0].embedding
    

    def search(self, query_text: str, top_k: int = settings.TOP_K) -> List[Dict[str, Any]]:
        query_vector = self.get_embedding(query_text)

        search_result = self.client.query_points(
            collection_name = settings.QDRANT_COLLECTION_NAME,
            query = query_vector,
            limit = top_k
        )

        return[
            {
                'text': hit.payload['text'],
                'source': hit.payload['source'],
                'score': hit.score
            }
            for hit in search_result.points
        ]
    

    def generate_response(self, query: str, contexts: List[Dict[str, Any]]) -> str:
        # Check cache
        cache_key = f"{query}_{len(contexts)}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        context_str = "\n\n---\n\n".join([f"Source: {c['source']}\nContent: {c['text']}" for c in contexts])
        '''
        Example:
        contexts = [
            {"source": "doc1.pdf", "text": "Cancer treatment includes chemotherapy."},
            {"source": "doc2.pdf", "text": "Radiation therapy is another option."}
        ]
        '''

        system_prompt = """You are a highly advanced Medical Literature Assistant.
        Your goal is to provide accurate, evidence-based answers based ONLY on the provided context.
        If the answer is not in the context, say that you don't know.
        Always cite your sources by mentioning the filename.
        """

        user_prompt = f"Context:\n{context_str}\n\nQuestion: {query}"

        response = self.openai_client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            temperature=0
        )
        
        answer = response.choices[0].message.content
        self.cache[cache_key] = answer
        return answer
    



    def query(self, query_text: str) -> Dict[str, Any]:
        contexts = self.search(query_text)
        answer = self.generate_response(query_text, contexts)
        return{
            'answer': answer,
            'sources': list(set([c['source'] for c in contexts]))
        }