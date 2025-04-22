import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

def insert_into_chroma(collection_name, documents, embeddings):
    collection = client.create_collection(collection_name)
    collection.add(
        documents=documents,
        metadatas=[{}] * len(documents),
        embeddings=embeddings,
        ids=[str(i) for i in range(len(documents))]
    )

def query_chroma(collection_name, query, n_results=5):
    collection = client.get_collection(collection_name)
    results = collection.query(query_embeddings=query, n_results=n_results)
    return results['documents']
