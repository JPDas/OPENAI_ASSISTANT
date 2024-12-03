import os

from multiprocessing.pool import ThreadPool
from Ingestion.data_extraction import DataExtract
from Ingestion.vectorizer import VectorDB
from langchain.text_splitter import RecursiveCharacterTextSplitter

from dotenv import load_dotenv

load_dotenv()

class Ingestion:
    def __init__(self, data_path, collection_name, chroma_dir) -> None:
        self.data_path = data_path
        self.extractor = DataExtract(data_path)
        self.vector = VectorDB(chroma_dir, collection_name)

    def split_texts(self, texts, meta):
        embeddings, metadatas, docs = [], [], []
        for page_num, text in texts:
            text_splitter = RecursiveCharacterTextSplitter(
                # Set a really small chunk size, just to show.
                chunk_size=1500,
                chunk_overlap=100,
                separators=["\n\n", "\n", " ", ".", "?", "!", ",", ""]
                )
            
            chunks = text_splitter.split_text(text)
            for i, chunk in enumerate(chunks):
                meta_data = {
                    "page_number": page_num,
                    "chunk_number": i+1,
                    **meta
                    }

                embeddings.append(self.vector.get_text_embedding(chunk))

                metadatas.append(meta_data)
                docs.append(chunk)

        print(f"No of chunks splited {len(docs)}")

        return embeddings, metadatas, docs

    def add_or_update_docs(self, embeddings, metadatas, texts):
        filename = metadatas[0]["Name"].replace(" ", "")
        
        print(f"add or update document of {filename}")
        doc_id = metadatas[0]["Name"].replace(" ", "")+"_"+str(0)
        
        if self.is_doc_id_present(doc_id):
            print(f"add or update document of {doc_id} is present in chromadb")
            doc_ids = self.vector.get_ids(filename)
            #delete all documents
            
            print(f"deleteing {doc_ids} to update in chromadb")
            self.vector.delete(doc_ids)
        
        ids = [filename +"_"+str(i) for i in range(len(metadatas))]
        
        print(f"Inserting {ids} into chromadb")
        result = self.vector.add(ids, texts, metadatas, embeddings)
        
        return result

    def is_doc_id_present(self, doc_id):
        result = self.vector.get_doc(doc_id)
        if len(result['ids']) > 0:
            return True
        return False

    def has_newer_version(self, meta):
        id = meta["Name"].replace(" ", "") + "_"+ str(0)
        
        result = self.vector.get_doc(id)
        
        if len(result['ids']) > 0:
            # get the metadata and check the version, if version is same then ignore
            
            if result['metadatas'][0]['Version'] == meta['Version']:
                print(f"Already same meta version exist in chromadb, hence ignoring {id}")
                return False

        return True

    def fetch_document(self, meta):
        pages = None
        
        check = self.has_newer_version(meta)

        print(f" newer version returned {check}")
        if check:
            
            print(f"fetch_document {meta}")
            if self.data_path.lower().endswith(".zip"):
                pages = self.extractor.read_from_zip_file(meta["Name"])
                return pages, meta
            
        return None, meta
            
    def download_documents(self, meta_json, processes = None):
        with ThreadPool(processes=processes) as pool:
            for doc, meta in pool.imap_unordered(self.fetch_document, meta_json):
                # couldn't be fetched
                if doc is None:
                    print(f" document is not fetched {meta}")
                    continue
                yield doc, meta

    def run(self):
        meta_json = self.extractor.read_meta_from_zip_file()
        result = []
        #step 1: read the pdf docs and clean the text
        
        for cleaned_text, meta_data in self.download_documents(meta_json, processes=3):

            print(f"cleaned text {len(cleaned_text)}")
            #Step 2: split and chunking the text
            if cleaned_text:
                embeddings, metadatas, texts = self.split_texts(cleaned_text, meta_data)

                #step 3: insert or update docs in chromadb
                result = self.add_or_update_docs(embeddings, metadatas, texts)

        print("Ingested doc succesfully")
        return result
        