from typing import Tuple
import os
from datetime import datetime
from openai import OpenAI
from src.agents.base import TeachingAgent
from src.agents.characters import (
    TUTOR_CHARACTER, 
    QUIZ_CHARACTER, 
    HOST_CHARACTER, 
    CHAPTER_QUIZ_CHARACTER
)

def create_agents(client: OpenAI, log_dir: str) -> Tuple[TeachingAgent, TeachingAgent]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tutor_log = os.path.join(log_dir, f"tutor_{timestamp}.txt")
    quiz_log = os.path.join(log_dir, f"quiz_{timestamp}.txt")
    
    tutor = TeachingAgent(
        name="Professor Smith",
        role="tutor",
        character=TUTOR_CHARACTER,
        client=client,
        log_file=tutor_log
    )
    
    quiz = TeachingAgent(
        name="Quiz Master",
        role="quiz",
        character=QUIZ_CHARACTER,
        client=client,
        log_file=quiz_log
    )
    
    return tutor, quiz

def create_chapter_agents(client: OpenAI, log_dir: str) -> Tuple[TeachingAgent, TeachingAgent]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    host_log = os.path.join(log_dir, f"host_{timestamp}.txt")
    chapter_quiz_log = os.path.join(log_dir, f"chapter_quiz_{timestamp}.txt")
    
    host = TeachingAgent(
        name="Course Host",
        role="host",
        character=HOST_CHARACTER,
        client=client,
        log_file=host_log
    )
    
    chapter_quiz = TeachingAgent(
        name="Chapter Quiz Master",
        role="chapter_quiz",
        character=CHAPTER_QUIZ_CHARACTER,
        client=client,
        log_file=chapter_quiz_log
    )
    
    return host, chapter_quiz

def simulate_student_response(client: OpenAI, quiz_content: str, lecture_content: str, log_file: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    student_prompt = f"""You are a smart student but have no experience on C. 
    Please answer this quiz based on your assigned role: {quiz_content}
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": student_prompt}
            ],
            max_tokens=1000
        )
        response = completion.choices[0].message.content
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n[{timestamp}] Student Response:\n{response}\n")
        
        return response
    except Exception as e:
        error_msg = f"Error simulating student response: {str(e)}"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n[{timestamp}] Error: {error_msg}\n")
        print(error_msg)
        return ""

def get_student_input(quiz_content: str, lecture_content: str, log_file: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("\nQuiz Content:")
    print(quiz_content)
    print("\nPlease enter your answer:")
    student_response = input()
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n[{timestamp}] Student Response:\n{student_response}\n")
    
    return student_response