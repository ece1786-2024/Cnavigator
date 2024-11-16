# src/utils/langchain_setup.py

from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_openai import ChatOpenAI

class LangChainService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=100,
            chunk_overlap=20,
            add_start_index=True
        )
    
    def load_csv_data(self, file_path: str):
        """Load data from CSV file"""
        loader = CSVLoader(file_path=file_path, encoding='utf-8-sig')
        return loader.load()
    
    def create_retriever(self, data):
        """Create FAISS retriever from documents"""
        all_splits = self.text_splitter.split_documents(data)
        vectorstore = FAISS.from_documents(all_splits, self.embeddings)
        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 6}
        )