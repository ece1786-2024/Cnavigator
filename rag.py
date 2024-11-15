from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
import os
os.environ["OPENAI_API_KEY"] = "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"

def create_rag_retriever(file_path: str):
    loader = CSVLoader(file_path=file_path, encoding='utf-8-sig')
    data = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100, chunk_overlap=20, add_start_index=True
    )
    all_splits = text_splitter.split_documents(data)

    vectorstore = FAISS.from_documents(all_splits, OpenAIEmbeddings())
    return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})

def get_response(input, character,retriever) -> str:
    
    prompt = ChatPromptTemplate.from_messages([
                ("system", character),
                ("human", input),
            ])
  
    question_answer_chain = create_stuff_documents_chain(ChatOpenAI(model="gpt-4o-mini"), prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    response = rag_chain.invoke({"input": input})['answer']

    return response
