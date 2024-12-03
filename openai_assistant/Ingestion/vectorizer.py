import os
import chromadb
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()

class VectorDB:
    def __init__(self, chroma_data_path, collection_name) -> None:
        self.client = chromadb.PersistentClient(path=chroma_data_path)
        self.collection = self.client.get_or_create_collection(name=collection_name,
                                                               metadata={"hnsw:space": "cosine"},)
        self.openai_client = OpenAI()
        
    def get_text_embedding(self, text):
        response = self.openai_client.embeddings.create(model="text-embedding-ada-002", input=[text])
        return response.data[0].embedding
    
    def search(self, query, n_results):
        query_results = self.collection.query(query_texts=[query],n_results=n_results,)
        
        return query_results
    
    def get_doc(self, id):
        result = self.collection.get([id])
        print(f"get doc of {id} and {result}")
        
        return result
    
    def add(self, ids, docs, meta_datas, embeddings):
        print(f"Inserting data into chromadb {ids}")
        result = self.collection.add(
            documents= docs,
            embeddings= embeddings,
            ids=ids,
            metadatas=meta_datas)
        print(f"added {result}")
        
        return result
    
    def delete(self, ids):
        result = self.collection.delete(ids=ids)
        print(f"deleted {result}")
        
        return result
    
    def get_ids(self, filter_name):
        ids = self.collection.get()["ids"]
        doc_id = []
        for id in ids:
            if filter_name in id:
                doc_id.append(id)
                
        return doc_id