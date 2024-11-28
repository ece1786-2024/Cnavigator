import os
import pandas as pd
from openai import OpenAI

from .config import OPENAI_API_KEY, CSV_FILE_PATH, LOG_DIR, WAIT_TIME
from .utils.logger import create_log_directory, create_log_file, log_message
from .utils.langchain_setup import LangChainService
from .utils.helpers import create_chapter_agents
from .initial_test.test0 import Tests
from .gradio_app import create_quiz_interface

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

def main():
    try:
        # Initialize environment and services
        log_dir, client, main_log, df, retriever = setup_environment()
        
        # Run initial test and get results
        familiar_list, teaching_style = init_test(file_path="ini_test.csv")

        # Create chapter-level agents
        host, chapter_quiz = create_chapter_agents(client, log_dir,teaching_style)
        
                
    except Exception as e:
        error_msg = f"Error in teaching session: {str(e)}"
        print(error_msg)
        log_message(main_log, f"ERROR: {error_msg}")

if __name__ == "__main__":
    main()    