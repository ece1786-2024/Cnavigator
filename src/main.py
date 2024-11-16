# src/main.py
import os
import json
import time
import pandas as pd
from openai import OpenAI

from src.config import OPENAI_API_KEY, CSV_FILE_PATH, LOG_DIR, WAIT_TIME
from src.utils.logger import create_log_directory, create_log_file, log_message
from src.utils.helpers import create_chapter_agents
from src.initial_test.test0 import init_test, init_chapter_test
from src.utils.langchain_setup import LangChainService
from src.teaching.cycle import InLecture_block

def main():
    # Create log directory
    log_dir = create_log_directory()
    
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    
    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Create main log file
    main_log = create_log_file(log_dir, "main_log")
    
    try:
        # Initial test
        familar_list = init_test(file_path="ini_test.csv")
        
        # Initialize LangChain service
        langchain_service = LangChainService()
        
        # Load and prepare data
        data = langchain_service.load_csv_data(CSV_FILE_PATH)
        df = pd.read_csv(CSV_FILE_PATH, encoding='utf-8-sig')
        retriever = langchain_service.create_retriever(data)
        
        # ask students preference for teaching style:
        print("\nWhat teaching style do you prefer? Please enter an adjective, such as 'humorous':")
        teaching_style = "Your speaking style is "+input().lower()+". "
        
        
        # Create chapter-level agents
        host, chapter_quiz = create_chapter_agents(client, log_dir,teaching_style)
        
        with open(main_log, 'w', encoding='utf-8') as f:
            f.write("Teaching Session Started\n" + "=" * 50 + "\n")
        
        # Process each chapter
        for chapter_name, chapter_df in df.groupby('Chapter', sort=False):
            print(f"\n{'='*20} Chapter: {chapter_name} {'='*20}")
            
            # Chapter init test
            unfamilar_list = []
            if chapter_name in familar_list:
                unfamilar_list = init_chapter_test(chapter_name)
            else:
                df_test = pd.read_csv("chapter_test.csv", encoding='utf-8-sig')
                unfamilar_list = df_test[df_test['Chapter'] == chapter_name]['Knowledge Point'].tolist()
                
            # Process chapter based on familiarity
            if unfamilar_list == []:
                # Direct chapter test for familiar content
                chapter_content = {
                    'chapter': chapter_name,
                    'basic_content': chapter_df['Basic Content'].tolist(),
                    'advanced_content': chapter_df['Advanced Content'].tolist()
                }
                chapter_quiz_content = chapter_quiz.get_response(
                    f"Create a comprehensive chapter test based on: {json.dumps(chapter_content)}"
                )
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
                
                InLecture_block(chapter_df, client, log_dir, main_log, teaching_style, retriever, unfamilar_list)
                
                # Chapter Quiz
                chapter_content = {
                    'chapter': chapter_name,
                    'basic_content': chapter_df['Basic Content'].tolist(),
                    'advanced_content': chapter_df['Advanced Content'].tolist()
                }
                chapter_quiz_content = chapter_quiz.get_response(
                    f"Create a comprehensive chapter test based on: {json.dumps(chapter_content)}"
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
            
    except Exception as e:
        error_msg = f"Error in teaching session: {str(e)}"
        print(error_msg)
        log_message(main_log, f"ERROR: {error_msg}")

if __name__ == "__main__":
    main()