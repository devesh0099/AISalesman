from dotenv import load_dotenv
import pinecone
import os
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
)
from llama_index.vector_stores.pinecone import PineconeVectorStore


load_dotenv()
pc = pinecone.Pinecone(api_key=os.environ.get("PINECONE_API"))
index_name = "short"
# pinecone.init(api_key="PINECONE_API")
# pc.create_index(index_name, dimension=384, metric="euclidean", spec=ServerlessSpec(cloud="aws", region="us-east-1"),)

embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-large-en-v1.5"
)

# construct vector store and customize storage context
storage_context = StorageContext.from_defaults(
    vector_store=PineconeVectorStore(pc.Index(index_name))
)

# Load documents and build index
documents = SimpleDirectoryReader(
    "data/coaching_materials"
).load_data()
index = VectorStoreIndex.from_documents(
    documents, storage_context=storage_context,embed_model=embed_model
)
