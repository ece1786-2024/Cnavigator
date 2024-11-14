from openai import OpenAI
import pandas as pd
import time
from typing import List, Dict, Tuple
import json
from datetime import datetime
import os
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS

os.environ["OPENAI_API_KEY"] = "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"

llm = ChatOpenAI(model="gpt-4o-mini")

# 保持原有的 TeachingAgent 类和辅助函数不变
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
            
            #client:OpenAI
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
        
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self.character),
                    ("human", "{input}"),
                ]
            )
            question_answer_chain = create_stuff_documents_chain(ChatOpenAI(model="gpt-4o-mini"), prompt)
            rag_chain = create_retrieval_chain(retriever, question_answer_chain)
            response = rag_chain.invoke({"input": input})['answer']
            # print(response['answer'])

            
            self.add_to_history("assistant", response)
            return response
            
        except Exception as e:
            error_msg = f"Error getting response: {str(e)}"
            self.log_message(error_msg)
            print(error_msg)
            return ""    

def create_log_directory():
    log_dir = "conversation_logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

# 保持原有的 create_agents 函数不变
#def create_agents(client: OpenAI, log_dir: str) -> Tuple[TeachingAgent, TeachingAgent, TeachingAgent]:
def create_agents(client: OpenAI, log_dir: str) -> Tuple[TeachingAgent, TeachingAgent]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tutor_log = os.path.join(log_dir, f"tutor_{timestamp}.txt")
    quiz_log = os.path.join(log_dir, f"quiz_{timestamp}.txt")
    #ta_log = os.path.join(log_dir, f"ta_{timestamp}.txt")
    
    tutor_character =  """You are now acting as a Tutor in a learning platform called CNavigator. I want you to explain a concept in C programming to a student in a friendly and engaging manner. Your goal is to ensure the student fully understands the topic, provide examples, and interact with them to confirm their understanding.

For the following concept in C programming, create an interactive tutoring session:

Requirement:
1. Start with a friendly greeting and introduce the concept.
2. Provide a clear explanation of the concept, using simple language.
3. Include a code example to illustrate the concept.
4. Explain the example thoroughly.
5. Encourage the student to ask questions or request more examples if needed.
6. If the student has fully understood, you finish this lecture (Student will be the user, you are only acting as a tutor).
7. Ask student input “try a quiz” once students fully understand the content.

Please generate a tutoring session for this context: {context}.
"""
    
    tutor = TeachingAgent(
        name="Professor Smith",
        role="tutor",
        character=tutor_character,
        client=client,
        log_file=tutor_log
    )
    
    quiz_character = """You are now acting as a QuizMaster in a learning platform called CNavigator. I want you to ask a series of quiz questions to help a student review their understanding of C programming based on the lecture content. Your tone should be friendly, encouraging, and interactive, guiding the student if they make mistakes. You will appear to provide the quiz after each lecture. 

Based on the course content provided by Tutor, create a quiz question:

Requirement:
1. Include a friendly greeting and encourage the student.
2. Ask the question and provide 4 answer options, making it a multiple-choice question.
3. Offer to give a hint if the student is unsure.
4. Provide positive reinforcement if they get it correct, or an explanation if they answer incorrectly.
5. Do not show the answer before the student correctly answer it
6. After finishing the quiz, ask the student to input "CCCC".
"""
    
    quiz = TeachingAgent(
        name="Quiz Master",
        role="quiz",
        character=quiz_character,
        client=client,
        log_file=quiz_log
    )
    
    #ta_character = 
    """You are a teaching assistant responsible for grading.
    Review student answers and provide:
    1. Grade out of 10 (each multiple choice = 1 point, each coding = 3.5 points)
    2. If a student scores above 7, you will mark it as 'Pass.' 
    If the student scores below 7, you will mark it as 'Fail' and provide feedback on the knowledge areas where they made mistakes.
    Format your response should be like:
    "Result:Pass"
    or
    "Result: Fail
    Feedback: The student needs to improve in the following areas:
    - Understanding default types in C: Ensure familiarity with fundamental C data types, including the default integer type.
    - Integer division operations: Review integer operations to understand how division results are calculated and stored in integer variables."""
    
    #ta = TeachingAgent(name="TA Alex", role="ta", character=ta_character, client=client, log_file=ta_log)
    
    return tutor, quiz
    #return tutor, quiz, ta

# 新增 create_chapter_agents 函数
#def create_chapter_agents(client: OpenAI, log_dir: str) -> Tuple[TeachingAgent, TeachingAgent, TeachingAgent]:
def create_chapter_agents(client: OpenAI, log_dir: str) -> Tuple[TeachingAgent, TeachingAgent]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    host_log = os.path.join(log_dir, f"host_{timestamp}.txt")
    chapter_quiz_log = os.path.join(log_dir, f"chapter_quiz_{timestamp}.txt")
    #chapter_ta_log = os.path.join(log_dir, f"chapter_ta_{timestamp}.txt")
    
    # Host Agent
    host_character = """You are the Host in a C programming course. Your role is to introduce the course, motivate students by explaining the benefits of learning C at the first. When students give you a positive response, you should ask them whether they have C programming experience before. If they answer yes, you can ask whether they want to finish a question list in order to determine which level the student is. After each chapter, recognize their progress and encourage them to continue. Keep a friendly and supportive tone."""
    
    host = TeachingAgent(
        name="Course Host",
        role="host",
        character=host_character,
        client=client,
        log_file=host_log
    )
    
    # Chapter Quiz Agent
    chapter_quiz_character = """You're now acting as a Term Test Quiz Creator. I want you to quiz a student on their overall understanding of C programming at the end of chapter. Your style should be positive, reinforcing the key concepts they've learned. If they need help, you can offer one hint per question, but encourage them to try first.

Here's how you should interact:
1. Start with a friendly welcome and let them know this is a comprehensive test on the chapter.
2. Ask each question with four multiple-choice answers, but make it clear these questions cover various important topics from the chapter.
3. If they answer correctly, give positive feedback; if they're wrong, gently correct them with a brief explanation.
4. At the end, congratulate them on finishing the test and encourage them to review any areas they found challenging.

Let's start! Type "READY" to begin.
"""
    
    chapter_quiz = TeachingAgent(
        name="Chapter Quiz Master",
        role="chapter_quiz",
        character=chapter_quiz_character,
        client=client,
        log_file=chapter_quiz_log
    )
    
    # Chapter TA Agent
    #chapter_ta_character = 
    """You are a C programming chapter evaluator. Grade the comprehensive project and provide detailed feedback.
    Format your response in JSON:
    {
        "score": {
            "total": number,
            "functionality": number,
            "concept_usage": number,
            "code_quality": number
        },
        "feedback": {
            "strengths": ["string"],
            "areas_to_improve": ["string"]
        },
        "resources": {
            "documentation": [
                {"topic": "string", "url": "string"}
            ],
            "tutorials": [
                {"topic": "string", "url": "string"}
            ],
            "practice": [
                {"topic": "string", "url": "string"}
            ]
        },
        "encouragement": "string",
        "next_steps": ["string"]
    }"""
    
    #chapter_ta = TeachingAgent(name="Chapter TA", role="chapter_ta", character=chapter_ta_character, client=client, log_file=chapter_ta_log)
    
    #return host, chapter_quiz, chapter_ta
    return host, chapter_quiz

# 保持原有的 teaching_cycle 和 simulate_student_response 函数不变
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

#def teaching_cycle(knowledge_point: str, knowledge_point_prompt: str, tutor: TeachingAgent, 
#                  quiz: TeachingAgent, ta: TeachingAgent, client: OpenAI, log_dir: str,retriever=None) -> str:
def teaching_cycle(knowledge_point: str, knowledge_point_prompt: str, tutor: TeachingAgent, 
                  quiz: TeachingAgent, client: OpenAI, log_dir: str,retriever=None) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cycle_log = os.path.join(log_dir, f"teaching_cycle_{timestamp}_{knowledge_point.replace(' ', '_')}.txt")
    
    with open(cycle_log, 'w', encoding='utf-8') as f:
        f.write(f"Teaching Cycle for: {knowledge_point}\n")
        f.write("=" * 50 + "\n")
    
    print(f"\n🎓 Tutor explaining: {knowledge_point_prompt}")
    lecture = tutor.get_response_on_rag(f"Please explain this programming concept: {knowledge_point_prompt}",retriever)
    with open(cycle_log, 'a', encoding='utf-8') as f:
        f.write(f"\nLECTURE:\n{lecture}\n")
    print("Lecture completed.")
    
    print("\n📝 Generating quiz...")
    quiz_content = quiz.get_response(
        f"Based on this lecture about {knowledge_point_prompt}, generate a quiz:\n\n{lecture}"
    )
    with open(cycle_log, 'a', encoding='utf-8') as f:
        f.write(f"\nQUIZ:\n{quiz_content}\n")
    print("Quiz generated.")
    
    print("\n👨‍🎓 Student attempting quiz...")
    # student_answers = simulate_student_response(client, quiz_content, lecture, cycle_log)
    student_answers = get_student_input(quiz_content, lecture, cycle_log)
    print("Student submitted answers.")
    
    print("\n📊 TA grading...")
    grading_prompt = f"""
    Topic: {knowledge_point}
    Lecture: {lecture}
    Quiz: {quiz_content}
    Student Answers: {student_answers}
    
    Please grade the student's answers and provide feedback.
    """
    
    grading_result = quiz.get_response(grading_prompt)
    
    with open(cycle_log, 'a', encoding='utf-8') as f:
        f.write(f"\nGRADING RESULTS:{grading_result}\n")
    print(grading_result)
    return grading_result

# 新增 InLecture_block 函数
def InLecture_block(chapter_df: pd.DataFrame, client: OpenAI, log_dir: str, main_log: str,retriever=None) -> List[str]:
    """Execute the knowledge point learning cycle and return passed points"""
    passed_points = []
    #tutor, quiz, ta = create_agents(client, log_dir)
    tutor, quiz = create_agents(client, log_dir)
    for _, row in chapter_df.iterrows():
    
        knowledge_point = row['Knowledge Point']
        basic_content = row['Basic Content']
        advanced_content = row['Advanced Content']
        
        knowledge_point_prompt = f"""Knowledge Point: {knowledge_point}
        Basic Content: {basic_content}
        Advanced Content: {advanced_content}"""
        
        #FRONTEND log_message
        log_message = f"\n=== Starting lesson for: {knowledge_point} ==="
        print(log_message)
        
        with open(main_log, 'a', encoding='utf-8') as f:
            f.write(f"{log_message}\n")
        
        attempts = 0
        max_attempts = 3
        passed = False
        
        while not passed and attempts < max_attempts:
            attempts += 1
            log_message = f"\n📚 Attempt {attempts} of {max_attempts}"
            print(log_message)
            
            with open(main_log, 'a', encoding='utf-8') as f:
                f.write(f"{log_message}\n")
            
            #FRONTEND grading_result
            #grading_result = teaching_cycle(knowledge_point, knowledge_point_prompt, tutor, quiz, ta, client, log_dir,retriever)
            grading_result = teaching_cycle(knowledge_point, knowledge_point_prompt, tutor, quiz, client, log_dir,retriever)
            if 'pass' in grading_result.lower():
                passed = True
                passed_points.append(knowledge_point)
                log_message = f"\n✅ Passed! Moving to next topic."
                print(log_message)
                with open(main_log, 'a', encoding='utf-8') as f:
                    f.write(f"{log_message}\n")
            # elif attempts < max_attempts:
            #     #FRONTEND log_message
            #     log_message = f"\n⚠️ Grade below 7/10. Retrying..."
            #     print(log_message)
            #     with open(main_log, 'a', encoding='utf-8') as f:
            #         f.write(f"{log_message}\n")
            #     time.sleep(2)
            #     knowledge_point_prompt = grading_result.split('eedback')[-1]
            elif attempts < max_attempts:
                log_message = f"\n⚠️ Grade below 7/10. Would you like to try again? (yes/no)"
                print(log_message)
                retry = input().lower()
                if retry != 'yes':
                    break
                with open(main_log, 'a', encoding='utf-8') as f:
                    f.write(f"{log_message}\n")
                time.sleep(2)
                knowledge_point_prompt = grading_result.split('eedback')[-1]
            else:
                #FRONTEND log_message
                log_message = f"\n❌ Maximum attempts reached. Moving to next topic."
                print(log_message)
                with open(main_log, 'a', encoding='utf-8') as f:
                    f.write(f"{log_message}\n")
        
        time.sleep(5)
    
    return passed_points

def main():
    
    
    
    
    
    
    
    
    # Create log directory
    log_dir = create_log_directory()
    
    # Initialize OpenAI client
    client = OpenAI(api_key="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")
    
    # Create main log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    main_log = os.path.join(log_dir, f"main_log_{timestamp}.txt")
    
    
    
    
    
    
        
        
    
    
    try:

        
        # Read chapter structure from CSV
        file_path = 'C_Variables_Knowledge_Points.csv'
        df = pd.read_csv(file_path,encoding='utf-8-sig')
        loader = CSVLoader(file_path=file_path,encoding='utf-8-sig')
        data = loader.load()
        # print(df)


            
        # len(data[0].page_content)    
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=100, chunk_overlap=20, add_start_index=True
        )
        all_splits = text_splitter.split_documents(data)

        # print(len(all_splits))
        # print(all_splits)
       

        vectorstore = FAISS.from_documents(all_splits, OpenAIEmbeddings())
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})
        # print(retriever)
        # print(1)
        
        # Create chapter-level agents
        #host, chapter_quiz, chapter_ta = create_chapter_agents(client, log_dir)
        host, chapter_quiz = create_chapter_agents(client, log_dir)
        # print(1)
        
        with open(main_log, 'w', encoding='utf-8') as f:
            f.write("Teaching Session Started\n")
            f.write("=" * 50 + "\n")
        
        # Process each chapter
        for chapter_name, chapter_df in df.groupby('Chapter',sort=False):
            print(f"\n{'='*20} Chapter: {chapter_name} {'='*20}")
            
            # Step 1: Host introduces chapter
            chapter_info = {
                'name': chapter_name,
                'basic_content': chapter_df['Basic Content'].tolist(),
                'advanced_content': chapter_df['Advanced Content'].tolist()
            }
            syllabus = host.get_response(f"Create a syllabus for chapter '{chapter_name}' with this content: {json.dumps(chapter_info)}, don't be too long")
            print("\n📚 Chapter Syllabus:")
            print(syllabus)
            
            # Step 2: Run through all knowledge points
            passed_points = InLecture_block(chapter_df, client, log_dir, main_log,retriever)
            
            if len(passed_points) > 0:
                # Step 3: Chapter Quiz
                print("\n📝 Generating Chapter Quiz...")
                chapter_content = {
                    'chapter': chapter_name,
                    'knowledge_points': passed_points,
                    'basic_content': chapter_df['Basic Content'].tolist(),
                    'advanced_content': chapter_df['Advanced Content'].tolist()
                }
                chapter_quiz_content = chapter_quiz.get_response(
                    f"Create a comprehensive chapter quiz based on: {json.dumps(chapter_content)}"
                )
                
                # Step 4: Student attempts chapter quiz
                print("\n👨‍🎓 Student attempting chapter quiz...")
                student_answers = simulate_student_response(client, chapter_quiz_content, syllabus, main_log)
                
                # Step 5: Chapter TA evaluation
                print("\n📊 Evaluating chapter mastery...")
                evaluation_prompt = {
                    'chapter': chapter_name,
                    'quiz': chapter_quiz_content,
                    'student_solution': student_answers,
                    'covered_concepts': passed_points
                }
                
                evaluation = chapter_quiz.get_response(
                    f"Evaluate this chapter quiz solution: {json.dumps(evaluation_prompt)}"
                )
                
                try:
                    eval_data = json.loads(evaluation)
                    print("\n=== Chapter Evaluation ===")
                    
                    if eval_data["score"]["total"] >= 70:
                        print("✅ Chapter Mastered!")
                        print(f"💪 {eval_data['encouragement']}")
                    else:
                        print("ℹ️ Additional Practice Recommended")
                        print("\nRecommended Resources:")
                        for doc in eval_data["resources"]["documentation"]:
                            print(f"📚 {doc['topic']}: {doc['url']}")
                        for tutorial in eval_data["resources"]["tutorials"]:
                            print(f"📝 {tutorial['topic']}: {tutorial['url']}")
                        for practice in eval_data["resources"]["practice"]:
                            print(f"✍️ {practice['topic']}: {practice['url']}")
                        print(f"\n💪 {eval_data['encouragement']}")
                    
                    print("\nNext Steps:")
                    for step in eval_data["next_steps"]:
                        print(f"➡️ {step}")
                    
                    with open(main_log, 'a', encoding='utf-8') as f:
                        f.write(f"\nChapter {chapter_name} Evaluation:\n")
                        f.write(json.dumps(eval_data, indent=2))
                    
                except json.JSONDecodeError:
                    print("Evaluation completed. See logs for details.")
            else:
                print(f"\n⚠️ No topics were successfully completed in chapter {chapter_name}")
            
            print(f"\nCompleted Chapter: {chapter_name}\n")
            time.sleep(5)
            
    except Exception as e:
        error_msg = f"Error in teaching session: {str(e)}"
        print(error_msg)
        with open(main_log, 'a', encoding='utf-8') as f:
            f.write(f"\nERROR: {error_msg}\n")

if __name__ == "__main__":
    main()