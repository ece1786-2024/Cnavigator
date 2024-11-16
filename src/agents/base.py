from typing import List, Dict
from datetime import datetime
from openai import OpenAI

class TeachingAgent:
    def __init__(self, name: str, role: str, character: str, client: OpenAI, log_file: str):
        self.name = name
        self.role = role
        self.character = character
        self.client = client
        self.conversation_history: List[Dict] = []
        self.log_file = log_file
    
    def log_message(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n[{timestamp}] {self.name}: {message}\n")
    
    def add_to_history(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        if role == "user":
            self.log_message(f"Received prompt: {content}")
        else:
            self.log_message(f"Response: {content}")
    
    def clear_history(self):
        self.conversation_history = []
        self.log_message("Conversation history cleared")
    
    def get_response(self, prompt: str) -> str:
        try:
            self.add_to_history("user", prompt)
            messages = [
                {"role": "system", "content": self.character},
                *self.conversation_history
            ]
            
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=2000
            )
            
            response = completion.choices[0].message.content
            self.add_to_history("assistant", response)
            return response
            
        except Exception as e:
            error_msg = f"Error getting response: {str(e)}"
            self.log_message(error_msg)
            print(error_msg)
            return ""

    def get_response_on_rag(self, input: str, retriever) -> str:
        try:
            self.add_to_history("user", input)
            
            from src.rag.rag import get_rag_response
            response = get_rag_response(
                query=input,
                retriever=retriever,
                system_prompt=self.character
            )
            
            if response:
                self.add_to_history("assistant", response)
                return response
            return ""
                
        except Exception as e:
            error_msg = f"Error getting response: {str(e)}"
            self.log_message(error_msg)
            print(error_msg)
            return ""