from Ingestion.vectorizer import VectorDB

collection_name = "RISK_AND_POLICY"
chroma_dir = "Chroma_Path"

def get_relevant_chunks(query):

    vector = VectorDB(chroma_dir, collection_name)

    query_results = vector.search(query, n_results=3)

    print(query_results)

    return query_results


    