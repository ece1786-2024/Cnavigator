from .gradio_app import create_quiz_interface

import os
import json
import time
import pandas as pd
import gradio as gr
from openai import OpenAI
from threading import Event

from src.config import OPENAI_API_KEY, CSV_FILE_PATH, LOG_DIR, WAIT_TIME
from src.utils.logger import create_log_directory, create_log_file, log_message
from src.utils.helpers import create_chapter_agents
from src.initial_test.test0 import Tests
from src.utils.langchain_setup import LangChainService
from src.teaching.cycle import InLecture_block

def setup_environment():
    log_dir = create_log_directory()
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    client = OpenAI(api_key=OPENAI_API_KEY)
    main_log = create_log_file(log_dir, "main_log")
    
    langchain_service = LangChainService()
    data = langchain_service.load_csv_data(CSV_FILE_PATH)
    df = pd.read_csv(CSV_FILE_PATH, encoding='utf-8-sig')
    retriever = langchain_service.create_retriever(data)
    
    return log_dir, client, main_log, df, retriever

def init_test(file_path="ini_test.csv"):
    tests = Tests(file_path)
    app = create_quiz_interface(tests)
    app.launch()
    return tests.get_results()

# Global variables
teaching_style_event = Event()
teaching_style_value = None
initial_test_event = Event()
initial_test_value = None
chapter_test_event = Event()
chapter_test_value = None

def submit_teaching_style(style):
    global teaching_style_value
    teaching_style_value = "You should be " + style.lower() + " when you are teaching with the students."
    teaching_style_event.set()
    return "Thank you! Your preference has been recorded."

def submit_initial_test_response(response):
    global initial_test_value
    initial_test_value = response
    initial_test_event.set()
    return "Your answer has been recorded."

def submit_chapter_test_response(response):
    global chapter_test_value
    chapter_test_value = response
    chapter_test_event.set()
    return "Your answer has been recorded."

def create_gradio_interface():
    with gr.Blocks() as interface:
        gr.Markdown("# Welcome to CNavigator Learning Platform")
        gr.Markdown("Please enter your preferred teaching style (e.g., 'humorous', 'serious', 'patient')")
        
        style_input = gr.Textbox(
            label="Teaching Style",
            placeholder="Enter an adjective (e.g., humorous)"
        )
        submit_btn = gr.Button("Submit")
        output = gr.Textbox(label="Status", visible=False)
        
        submit_btn.click(
            fn=submit_teaching_style,
            inputs=style_input,
            outputs=output,
            show_progress=False
        )
    
    return interface

def create_initial_test_interface(quiz_content):
    with gr.Blocks() as interface:
        gr.Markdown("# Initial Quiz")
        gr.Markdown(quiz_content)
        response_input = gr.Textbox(
            label="Your Answer",
            placeholder="Enter your answer (A, B, C, or D)"
        )
        submit_btn = gr.Button("Submit")
        output = gr.Textbox(label="Status", visible=False)
        
        submit_btn.click(
            fn=submit_initial_test_response,
            inputs=response_input,
            outputs=output,
            show_progress=False
        )
    
    return interface

def create_chapter_test_interface(quiz_content):
    with gr.Blocks() as interface:
        gr.Markdown("# Chapter Test")
        gr.Markdown(quiz_content)
        response_input = gr.Textbox(
            label="Your Answer",
            placeholder="Enter your answer (A, B, C, or D)"
        )
        submit_btn = gr.Button("Submit")
        output = gr.Textbox(label="Status", visible=False)
        
        submit_btn.click(
            fn=submit_chapter_test_response,
            inputs=response_input,
            outputs=output,
            show_progress=False
        )
    
    return interface

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    try:
        # Initialize environment and services
        log_dir, client, main_log, df, retriever = setup_environment()
        
        # Run initial test and get results
        familiar_list, teaching_style = init_test(file_path="ini_test.csv")

        # Create chapter-level agents
        host, chapter_quiz = create_chapter_agents(client, log_dir,teaching_style)
        
        # Process each chapter
        for chapter_name, chapter_df in df.groupby('Chapter', sort=False):
            print(f"\n{'='*20} Chapter: {chapter_name} {'='*20}")
            
            # Chapter init test
            unfamiliar_list = []
            if chapter_name in familiar_list:
                chapter_test_path = os.path.join(project_root, '..', 'chapter_test.csv')
                df_test = pd.read_csv(chapter_test_path, encoding='utf-8-sig')
                for index, row in df_test.iterrows():
                    if chapter_name != row['Chapter']:
                        continue
                    quiz_content = f"\nQuiz Content:\nChapter: {row['Chapter']}\nQuestion: {row['Question']}\nOption A: {row['Option A']}\nOption B: {row['Option B']}\nOption C: {row['Option C']}\nOption D: {row['Option D']}\n"
                    chapter_test_interface = create_chapter_test_interface(quiz_content)
                    chapter_test_interface.launch(share=False, prevent_thread_lock=True)
                    
                    # Wait for response
                    chapter_test_event.wait()
                    student_response = chapter_test_value
                    
                    if student_response.upper() != row['Answer']:
                        unfamiliar_list.append(row['Knowledge Point'])
            else:
                chapter_test_path = os.path.join(project_root, '..', 'chapter_test.csv')
                df_test = pd.read_csv(chapter_test_path, encoding='utf-8-sig')
                unfamiliar_list = df_test[df_test['Chapter'] == chapter_name]['Knowledge Point'].tolist()
                
            # Process chapter based on familiarity
            if unfamiliar_list == []:
                # Direct chapter test for familiar content
                chapter_content = {
                    'chapter': chapter_name,
                    'advanced_content': chapter_df['Advanced Content'].tolist()
                }
                
                coding_standard_path = os.path.join(project_root, '..', 'coding_standard.csv')
                df = pd.read_csv(coding_standard_path)
                coding_habit = df.to_string(index=False)
                
                chapter_quiz_content = chapter_quiz.get_response(
                    f"Create a comprehensive chapter test based on: {json.dumps(chapter_content)}, and help the student follow these coding standards:{coding_habit} while they write their code.")
 
                print(chapter_quiz_content)
                
                while True:
                    coding_answer = input("type your answer: ")
                    with open(main_log, 'a', encoding='utf-8') as f:
                        f.write(f"\nLECTURE:\n{chapter_quiz_content}\n")
                    
                    if coding_answer.lower() == "cccc":
                        print("Loading next chapter......")
                        break
                    else:
                        answer = chapter_quiz.get_response(f"{coding_answer}")
                        print(answer)
            else:
                # Full chapter process for unfamiliar content
                chapter_info = {
                    'name': chapter_name,
                    'basic_content': chapter_df['Basic Content'].tolist(),
                    'advanced_content': chapter_df['Advanced Content'].tolist()
                }
                syllabus = host.get_response(
                    f"Create a syllabus for chapter '{chapter_name}' with this content: {json.dumps(chapter_info)}, don't be too long"
                )
                print("\n📚 Chapter Syllabus:")
                print(syllabus)
                
                InLecture_block(chapter_df, client, log_dir, main_log, teaching_style, retriever, unfamiliar_list)
                
                # Chapter Quiz
                chapter_content = {
                    'chapter': chapter_name,
                    'basic_content': chapter_df['Basic Content'].tolist(),
                    'advanced_content': chapter_df['Advanced Content'].tolist()
                }
                
                coding_standard_path = os.path.join(project_root, '..', 'coding_standard.csv')
                standard = pd.read_csv(coding_standard_path)
                coding_habit = standard.to_string(index=False)
                
                chapter_quiz_content = chapter_quiz.get_response(
                    f"Create a comprehensive chapter test based on: {json.dumps(chapter_content)}, and help the student follow these coding standards:{coding_habit} while they write their code."
                )
                print(chapter_quiz_content)

                # Interactive quiz loop
                while True:
                    coding_answer = input("type your answer: ")
                    with open(main_log, 'a', encoding='utf-8') as f:
                        f.write(f"\nLECTURE:\n{chapter_quiz_content}\n")
                    
                    if coding_answer.lower() == "cccc":
                        print("Loading next chapter......")
                        break
                    else:
                        answer = chapter_quiz.get_response(f"{coding_answer}")
                        print(answer)
            
            print(f"\nCompleted Chapter: {chapter_name}\n")
            
            # Periodic summary and reset
            summary = host.get_response("Please summarize our discussion so far.")
            initial_host_character = """You are the Host in a C programming course. Your role is to introduce the course, motivate students by explaining the benefits of learning C at the first. When students give you a positive response, you should ask them whether they have C programming experience before. If they answer yes, you can ask whether they want to finish a question list in order to determine which level the student is. After each chapter, recognize their progress and encourage them to continue. Keep a friendly and supportive tone."""
            host.clear_history()
            host.add_to_history("system", initial_host_character)
            host.add_to_history("system", f"Summary: {summary}")
            
            time.sleep(WAIT_TIME)
            
        # Ending
        conclusion = host.get_response("Now that we have reached the end of this course, could you please provide a summary of the student's performance based on the conversation history? Additionally, suggest what they can do next to continue improving their skills in C programming.")
        print(conclusion)
                        
    except Exception as e:
        error_msg = f"Error in teaching session: {str(e)}"
        print(error_msg)
        log_message(main_log, f"ERROR: {error_msg}")

if __name__ == "__main__":
    main()    