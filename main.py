import os
import time
from datetime import datetime
import json
import pandas as pd
from langchain_openai import ChatOpenAI
from agents import  create_chapter_agents,  InLecture_block
from rag import create_rag_retriever
from utils import create_log_directory

def main():
    log_dir = create_log_directory()
    client = ChatOpenAI(api_key="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")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    main_log = os.path.join(log_dir, f"main_log_{timestamp}.txt")

    file_path = 'C_Variables_Knowledge_Points.csv'
    retriever = create_rag_retriever(file_path)

    host, chapter_quiz = create_chapter_agents(client, log_dir)

    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')

        with open(main_log, 'w', encoding='utf-8') as f:
            f.write("Teaching Session Started\n")
            f.write("=" * 50 + "\n")

        for chapter_name, chapter_df in df.groupby('Chapter', sort=False):
            print(f"\n{'='*20} Chapter: {chapter_name} {'='*20}")

            chapter_info = {
                'name': chapter_name,
                'basic_content': chapter_df['Basic Content'].tolist(),
                'advanced_content': chapter_df['Advanced Content'].tolist()
            }
            syllabus = host.get_response(f"Create a syllabus for chapter '{chapter_name}' with this content: {json.dumps(chapter_info)}, don't be too long")
            print("\n📚 Chapter Syllabus:")
            print(syllabus)

            InLecture_block(chapter_df, client, log_dir, main_log, retriever)

            chapter_content = {
                'chapter': chapter_name,
                'basic_content': chapter_df['Basic Content'].tolist(),
                'advanced_content': chapter_df['Advanced Content'].tolist()
            }
            chapter_quiz_content = chapter_quiz.get_response(f"Create a comprehensive chapter test based on: {json.dumps(chapter_content)}")
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

            print(f"\nCompleted Chapter: {chapter_name}\n")

            summary = host.get_response("Please summarize our discussion so far.")
            host.clear_history()
            host.add_to_history("system", host.character)
            host.add_to_history("system", f"Summary: {summary}")

            time.sleep(5)

    except Exception as e:
        error_msg = f"Error in teaching session: {str(e)}"
        print(error_msg)
        with open(main_log, 'a', encoding='utf-8') as f:
            f.write(f"\nERROR: {error_msg}\n")

if __name__ == "__main__":
    main()