# rag.py
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_openai import ChatOpenAI
from langchain.schema import BaseRetriever

def get_rag_response(
    query: str,
    retriever: BaseRetriever,
    system_prompt: str,
    model_name: str = "gpt-4o-mini"
) -> Optional[str]:
    """
    Get response using RAG (Retrieval Augmented Generation)
    
    Args:
        query: User input query
        retriever: Document retriever instance
        system_prompt: System prompt/character setting
        model_name: Name of the OpenAI model to use
        
    Returns:
        Generated response string or None if error occurs
    """
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(
            ChatOpenAI(model=model_name),
            prompt
        )
        
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)
        response = rag_chain.invoke({"input": query})['answer']
        
        return response
        
    except Exception as e:
        print(f"Error in RAG response generation: {str(e)}")
        return None