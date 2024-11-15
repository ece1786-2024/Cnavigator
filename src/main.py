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

def main():
    # Create log directory
    log_dir = create_log_directory()
    
    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Create main log file
    main_log = create_log_file(log_dir, "main_log")
    
    try:
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
            passed_points = InLecture_block(chapter_df, client, log_dir, main_log, retriever)
            
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
                student_answers = simulate_student_response(
                    client,
                    chapter_quiz_content,
                    syllabus,
                    main_log
                )
                
                # Step 5: Chapter Quiz evaluation
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
            time.sleep(WAIT_TIME)
            
    except Exception as e:
        error_msg = f"Error in teaching session: {str(e)}"
        print(error_msg)
        log_message(main_log, f"ERROR: {error_msg}")

if __name__ == "__main__":
    main()