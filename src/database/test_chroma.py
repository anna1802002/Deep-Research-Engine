from chroma_client import get_chroma_client

client = get_chroma_client()
collection = client.get_or_create_collection("test_collection")
collection.add(
    ids=["123"],
    embeddings=[[0.1]*768],
    documents=["This is a test document."],
    metadatas=[{"source": "test"}]
)

print("✅ Test embedding stored!")
