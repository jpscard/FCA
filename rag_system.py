import os
import json
import pandas as pd
from typing import List, Dict, Any
from langchain_core.documents import Document

from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from langchain_community.embeddings import HuggingFaceEmbeddings # Or GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Assuming utils has NCM loading
from utils import carregar_base_ncm, consultar_ncm

class RAGSystem:
    def __init__(self, embeddings_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.referencias_path = os.path.join(os.path.dirname(__file__), 'referencias')
        self.embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)
        self.qdrant_client = QdrantClient(host="localhost", port=6333) # Connect to Qdrant server running in Docker
        self.collection_name = "fiscal_rules_collection"
        self.vectorstore = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def _load_and_chunk_referencias(self) -> List[Document]:
        """Loads and chunks content from all files in the referencias directory."""
        all_docs = []
        for filename in os.listdir(self.referencias_path):
            file_path = os.path.join(self.referencias_path, filename)
            if filename.endswith(".md") or filename.endswith(".txt"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                metadata = {"source": filename}
                all_docs.extend(self.text_splitter.create_documents([content], metadatas=[metadata]))
            elif filename.endswith(".xlsx"):
                try:
                    df = pd.read_excel(file_path, usecols=[0, 1], dtype=str)
                    df.columns = ['Código NCM', 'Descrição NCM']
                    df['Código NCM'] = df['Código NCM'].astype(str).str.replace('.', '', regex=False)
                    for index, row in df.iterrows():
                        content = f"Código NCM: {row['Código NCM']} - Descrição: {row['Descrição NCM']}"
                        metadata = {"source": filename, "ncm_code": row['Código NCM']}
                        all_docs.append(Document(page_content=content, metadata=metadata))
                except Exception as e:
                    print(f"Error loading Excel file {filename}: {e}")

        print(f"Loaded and chunked {len(all_docs)} documents from the referencias directory.")
        return all_docs

    def initialize_vectorstore(self):
        """Initializes the Qdrant vector store with all knowledge base data."""
        all_chunks = self._load_and_chunk_referencias()

        if not all_chunks:
            print("No chunks to add to vectorstore. RAG system will not be effective.")
            return
        
        print(f"Creating Qdrant vector store with {len(all_chunks)} Document objects...")
        try:
            # Delete collection if it already exists for a fresh start
            self.qdrant_client.delete_collection(collection_name=self.collection_name)
        except Exception as e:
            print(f"Warning: Could not delete Qdrant collection (might not exist): {e}")

        try:
            self.vectorstore = Qdrant.from_documents(
                all_chunks,
                self.embeddings,
                url="http://localhost:6333",
                collection_name=self.collection_name,
            )
            print("Qdrant vector store initialized successfully.")
        except Exception as e:
            print(f"Error initializing Qdrant vector store: {e}")
            self.vectorstore = None

    def get_retriever(self):
        """Returns a LangChain retriever object."""
        if self.vectorstore:
            return self.vectorstore.as_retriever()
        else:
            print("Vector store not initialized. Cannot return retriever.")
            return None

    def retrieve_context(self, query: str, k: int = 5) -> List[str]:
        """Retrieves relevant context based on a query."""
        if self.vectorstore:
            print(f"DEBUG: retrieve_context called with query: {query[:100]}...")
            print(f"DEBUG: self.vectorstore is not None: {self.vectorstore is not None}")
            try:
                docs = self.vectorstore.similarity_search(query, k=k)
                return [doc.page_content for doc in docs]
            except Exception as e:
                print(f"Error during FAISS similarity search: {e}")
                raise # Re-raise the exception to get a full traceback
        else:
            print("Vector store not initialized. Skipping context retrieval.")
            return []

# Example Usage (for testing within rag_system.py)
if __name__ == "__main__":
    # Ensure GOOGLE_API_KEY is set in environment for utils.carregar_base_ncm to run if it uses it directly.
    # For HuggingFaceEmbeddings, you often don't need a specific API key unless using a private model.

    rag_sys = RAGSystem()
    rag_sys.initialize_vectorstore()

    if rag_sys.vectorstore:
        query = "Qual é a alíquota de ICMS para operações interestaduais envolvendo o NCM 84713012, e quais são as regras de substituição tributária aplicáveis?"
        context = rag_sys.retrieve_context(query)
        print(f"\nRetrieved context for query '{query}':")
        for i, c in enumerate(context):
            print(f"--- Chunk {i+1} ---")
            print(c)
