import fitz                                      # For reading PDF
import os
from typing import List, Dict
from qdrant_client import QdrantClient           # Vector DB client
from qdrant_client.http import models            # Qdrant data structures
from openai import OpenAI                        # OpenAI API client
from config import settings                      # Your config (API keys, paths)


class IngestionPipeline:
    def __init__(self):
        self.client = QdrantClient(path=settings.QDRANT_PATH)
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self._ensure_collection()


    def _ensure_collection(self):
        collections = self.client.get_collections().collections
        exists = any(c.name == settings.QDRANT_COLLECTION_NAME for c in collections)
        if not exists:
            self.client.create_collection(
                collection_name = settings.QDRANT_COLLECTION_NAME,
                vectors_config= models.VectorParams(
                    size= 1536, # Size for text-embedding-3-small
                    distance=models.Distance.COSINE
                )
            )


    def extract_text_from_pdf(self, pdf_path: str) -> str:
        doc = fitz.open(pdf_path)  #PFD reager
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    
    def chunk_text(sefl, text: str, chun_size: int = settings.CHUNK_SIZE, overlap: int = settings.CHUNK_OVERLAP) -> List[str]:
        chunks = []
        for i in range(0, len(text), chun_size - overlap):
            chunks.append(text[i:i + chun_size])
        return chunks
    

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        response = self.openai_client.embeddings.create(
            input=texts,
            model=settings.EMBEDDING_MODEL
        )
        return [data.embedding for data in response.data]
    

    def process_pdf(self, pdf_path: str):
        filename = os.path.basename(pdf_path)
        print(f"Processing {filename}...")
        text = self.extract_text_from_pdf(pdf_path)
        chunks = self.chunk_text(text)

        if not chunks:
            return
        
        embeddings = self.get_embeddings(chunks)

        points = []    # This list will store all the data points (vectors + metadata) before sending them to Qdrant.

        '''
        chunks → small pieces of text (from document splitting)
        embeddings → vector representation of each chunk
        zip(chunks, embeddings) → pairs each chunk with its embedding
        enumerate(...) → gives an index i 

        chunks = ["text1", "text2"]
        embeddings = [[0.1, 0.2], [0.3, 0.4]]

        Example:
        → Loop becomes:
        i=0 → ("text1", [0.1,0.2])
        i=1 → ("text2", [0.3,0.4])  
        '''
        for i, (chunk , embedding) in enumerate(zip(chunks, embeddings)):
            points.append(models.PointStruct(
                
                # Creates a unique ID for each chunk
                # Combines:
                # filename
                # chunk index i
                # hash() → converts to a number
                # & 0xFFFFFFFFFFFFFFFF → ensures it stays within 64-bit range
                
                id=hash(f"{filename}_{i}") & 0xFFFFFFFFFFFFFFFF, # Simplified ID
                vector= embedding,
                # This is extra information stored with the vector
                payload={
                    'text': chunks,
                    'source': filename,
                    'page_chunk': i
                }
            ))

        # What is upsert? If point exists → update If not → insert
        self.client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=points

        )
        print (f"Upserted {len(points)} chunks from {filename}")


def run_ingestion(data_dir: str):
    pipeline = IngestionPipeline()
    for file in os.listdir(data_dir):
        if file.endswith(".pdf"):
            pipeline.process_pdf(os.path.join(data_dir, file))


if __name__ == "__main__":
    run_ingestion("data")




