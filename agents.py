from datetime import datetime
from typing import List, Dict, Tuple
from openai import OpenAI
import pandas as pd
import os
import rag

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
                model="gpt-4o",
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

            response = rag.get_response(input,self.character,retriever)

            self.add_to_history("assistant", response)
            return response
        except Exception as e:
            error_msg = f"Error getting response: {str(e)}"
            self.log_message(error_msg)
            print(error_msg)
            return ""    

def create_agents(client: OpenAI, log_dir: str) -> Tuple[TeachingAgent, TeachingAgent]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tutor_log = os.path.join(log_dir, f"tutor_{timestamp}.txt")
    quiz_log = os.path.join(log_dir, f"quiz_{timestamp}.txt")

    tutor_character = """You are now acting as a Tutor in a learning platform called CNavigator. I want you to explain a concept in C programming to a student in a friendly and engaging manner. Your goal is to ensure the student fully understands the topic, provide examples, and interact with them to confirm their understanding."""

    tutor = TeachingAgent(
        name="Professor Smith",
        role="tutor",
        character=tutor_character,
        client=client,
        log_file=tutor_log
    )

    quiz_character = """You are now acting as a QuizMaster in a learning platform called CNavigator. I want you to ask a series of quiz questions to help a student review their understanding of C programming based on the lecture content. Your tone should be friendly, encouraging, and interactive, guiding the student if they make mistakes."""

    quiz = TeachingAgent(
        name="Quiz Master",
        role="quiz",
        character=quiz_character,
        client=client,
        log_file=quiz_log
    )

    return tutor, quiz

def create_chapter_agents(client: OpenAI, log_dir: str) -> Tuple[TeachingAgent, TeachingAgent]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    host_log = os.path.join(log_dir, f"host_{timestamp}.txt")
    chapter_quiz_log = os.path.join(log_dir, f"chapter_quiz_{timestamp}.txt")

    host_character = """You are the Host in a C programming course. Your role is to introduce the course, motivate students by explaining the benefits of learning C at the first. When students give you a positive response, you should ask them whether they have C programming experience before. If they answer yes, you can ask whether they want to finish a question list in order to determine which level the student is. After each chapter, recognize their progress and encourage them to continue. Keep a friendly and supportive tone."""

    host = TeachingAgent(
        name="Course Host",
        role="host",
        character=host_character,
        client=client,
        log_file=host_log
    )

    chapter_quiz_character = """You're now acting as a Term Test Quiz Creator. I want you to quiz a student on their overall understanding of C programming at the end of chapter. Your style should be positive, reinforcing the key concepts they've learned. If they need help, you can offer one hint per question, but encourage them to try first."""

    chapter_quiz = TeachingAgent(
        name="Chapter Quiz Master",
        role="chapter_quiz",
        character=chapter_quiz_character,
        client=client,
        log_file=chapter_quiz_log
    )

    return host, chapter_quiz

def teaching_cycle(knowledge_point: str, knowledge_point_prompt: str, tutor: TeachingAgent, quiz: TeachingAgent, client: OpenAI, log_dir: str, retriever):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cycle_log = os.path.join(log_dir, f"teaching_cycle_{timestamp}_{knowledge_point.replace(' ', '_')}.txt")

    with open(cycle_log, 'w', encoding='utf-8') as f:
        f.write(f"Teaching Cycle for: {knowledge_point}\n")
        f.write("=" * 50 + "\n")

    lecture = tutor.get_response_on_rag(f"Now, please explain this programming concept: {knowledge_point_prompt}", retriever)
    print(lecture)

    while True:
        user_input = input("any question?  ")
        with open(cycle_log, 'a', encoding='utf-8') as f:
            f.write(f"\nLECTURE:\n{lecture}\n")
        if user_input.lower() == "cccc":
            print("OK! Let's do a tiny quiz!")
            break
        else:
            addition = tutor.get_response(f"{user_input}")
            print(addition)

    quiz_content = quiz.get_response(f"Now, based on the {lecture}, generate a quiz")
    print(quiz_content)

    while True:
        student_answer = input("enter: ")
        with open(cycle_log, 'a', encoding='utf-8') as f:
            f.write(f"\nQUIZ:\n{quiz_content}\n")
        if student_answer.lower() == "cccc":
            print("Loading next lesson......")
            break
        else:
            addition2 = quiz.get_response(f"{student_answer}")
            print(addition2)

def InLecture_block(chapter_df: pd.DataFrame, client: OpenAI, log_dir: str, main_log: str, retriever):
    tutor, quiz = create_agents(client, log_dir)
    for _, row in chapter_df.iterrows():
        knowledge_point = row['Knowledge Point']
        basic_content = row['Basic Content']
        advanced_content = row['Advanced Content']

        knowledge_point_prompt = f"""Knowledge Point: {knowledge_point}
        Basic Content: {basic_content}
        Advanced Content: {advanced_content}"""

        log_message = f"\n=== Starting lesson for: {knowledge_point} ==="
        print(log_message)
        with open(main_log, 'a', encoding='utf-8') as f:
            f.write(f"{log_message}\n")

        teaching_cycle(knowledge_point, knowledge_point_prompt, tutor, quiz, client, log_dir, retriever)
        time.sleep(5)