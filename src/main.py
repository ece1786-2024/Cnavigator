import os
import json
import time
import pandas as pd
from openai import OpenAI
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from src.config import OPENAI_API_KEY, CSV_FILE_PATH, LOG_DIR, WAIT_TIME
from src.utils.logger import create_log_directory, create_log_file, log_message
from src.utils.helpers import create_chapter_agents, simulate_student_response
from src.teaching.cycle import InLecture_block
from src.initial_test.test0 import init_test,init_chapter_test

from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

def main():
    # Create log directory
    log_dir = create_log_directory()
    
    os.environ["OPENAI_API_KEY"] = "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"
    
    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Create main log file
    main_log = create_log_file(log_dir, "main_log")
    
    try:
        #initial test:
        
        #familar_list: means students may know something, 
        # so there will be a following test for the specific concept
        #if concept not in this list
        # means students no know nothing
        familar_list=init_test(file_path = "ini_test.csv")
        # print('familar_list: ',familar_list)
        
        # Read chapter structure and prepare RAG
        loader = CSVLoader(file_path=CSV_FILE_PATH, encoding='utf-8-sig')
        data = loader.load()
        df = pd.read_csv(CSV_FILE_PATH, encoding='utf-8-sig')

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=100,
            chunk_overlap=20,
            add_start_index=True
        )
        all_splits = text_splitter.split_documents(data)
        
        vectorstore = FAISS.from_documents(all_splits, OpenAIEmbeddings())
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 6}
        )
        
        # Create chapter-level agents
        host, chapter_quiz = create_chapter_agents(client, log_dir)
        
        with open(main_log, 'w', encoding='utf-8') as f:
            f.write("Teaching Session Started\n" + "=" * 50 + "\n")
        
        # Process each chapter
        for chapter_name, chapter_df in df.groupby('Chapter', sort=False):
            print(f"\n{'='*20} Chapter: {chapter_name} {'='*20}")
            
            #chapter init test:
            unfamilar_list=[]
            if chapter_name in familar_list:
                unfamilar_list=init_chapter_test(chapter_name)
            else:
                df_test=pd.read_csv("chapter_test.csv", encoding='utf-8-sig')
                unfamilar_list=df_test[df_test['Chapter'] == chapter_name]['Knowledge Point'].tolist()
            #students know everything for this chapter, go to the chapter test directly
            if unfamilar_list==[]:
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
                # Step 1: Host introduces chapter
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
                
                # Step 2: Run through all knowledge points
                InLecture_block(chapter_df, client, log_dir, main_log, retriever,unfamilar_list)
                
                # Step 3: Chapter Quiz
                chapter_content = {
                    'chapter': chapter_name,
                    'basic_content': chapter_df['Basic Content'].tolist(),
                    'advanced_content': chapter_df['Advanced Content'].tolist()
                }
                chapter_quiz_content = chapter_quiz.get_response(
                    f"Create a comprehensive chapter test based on: {json.dumps(chapter_content)}"
                )
                print(chapter_quiz_content)

                # Step 4: Interactive quiz loop
                while True:
                    coding_answer = input("type your answer: ")
                    with open(main_log, 'a', encoding='utf-8') as f:
                        f.write(f"\nLECTURE:\n{chapter_quiz_content}\n")
                    
                    if coding_answer.lower() == "cccc":
                        print("Loading next chapter......")
                        break
                    else:
                        # Step 5: Chapter QuizMaster evaluation
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