# src/main.py
import os 
import json
import time
import pandas as pd
from openai import OpenAI

from src.config import OPENAI_API_KEY, CSV_FILE_PATH, LOG_DIR, WAIT_TIME
from src.utils.logger import create_log_directory, create_log_file, log_message
from src.utils.helpers import create_chapter_agents, create_agents
from src.initial_test.test0 import init_test, init_chapter_test
from src.utils.langchain_setup import LangChainService
from src.teaching.cycle import Chapter_block

# 到39行和之前一样
def main():
    # Create log directory
    log_dir = create_log_directory()
    
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    
    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Create main log file
    main_log = create_log_file(log_dir, "main_log")
    
    try:
        # ask students preference for teaching style:
        print("Welcome to the CNavigator learning platform! We're here to help you master C programming, from basics to advanced levels. Let's begin this exciting journey together!")
        print("\nWhat teaching style do you prefer? Please enter an adjective, such as 'humorous':")
        teaching_style = "You should be "+input().lower()+" when you are teaching with the students."

        # Create chapter-level agents and provide the introduction to users
        host, chapter_quiz = create_chapter_agents(client, log_dir, teaching_style)
        formal_intro = host.get_response("Now a student just gets in the C programing course, please tell him how powerful C is, and why learning C is a good start.")
        print(formal_intro)
        
        # Initial test 存入不熟悉（答错）的章节名称
        basic_unfamiliar_list = init_test(file_path="ini_test.csv")
        
        # Initialize LangChain service
        langchain_service = LangChainService()

        # Load and prepare data
        data = langchain_service.load_csv_data(CSV_FILE_PATH)
        df = pd.read_csv(CSV_FILE_PATH, encoding='utf-8-sig')
        retriever = langchain_service.create_retriever(data)
        
        # Create teaching agents 在外面创建agents，这样就能有所有的教学进度了
        tutor, quiz = create_agents(client, log_dir, teaching_style)
        # Process each chapter
        for chapter_name, chapter_df in df.groupby('Chapter', sort=False):
            print(f"\n{'='*20} Chapter: {chapter_name} {'='*20}")
            chapter_content = []
            
            # Start creating the lecture 从这开始全变了， 第一个if如果章节名称在不熟悉的list里，就给他生成basic 的知识点
            if chapter_name in basic_unfamiliar_list: # Deliver basic course based on the inital test results
                knowledge_points = chapter_df['Knowledge Point'].tolist()
                chapter_info = {'Knowledge point': knowledge_points, 'basic_content': chapter_df['Basic Content'].tolist()}
                chapter_content.append(chapter_info)
                syllabus = host.get_response(f"Create a syllabus for chapter '{chapter_name}' with this content: {json.dumps(chapter_info)}, don't be too long")
                print("\n📚 Chapter Syllabus:")
                print(syllabus)
                
                # Start the basic level lecture 加了变量，输出格式没变，但现在会根据level生成课程了，这里是根据basic_unfamiliar_list生成课程
                Chapter_block(chapter_df, level = 'basic', tutor, quiz, log_dir, main_log, retriever, knowledge_points) 
                
            
            else: # Deliver advanced course 如果知识点不在basic_unfamiliar_list，就做chapter test
                advanced_need_list = init_chapter_test(chapter_name) # these knowledge points are going to be taught. 然后根据chapter test，把章节内需要讲解的知识点存到了advanced_need_list
                if advanced_need_df != []:# 如果没有需要讲解的直接跳过，去做chapter quiz
                    advanced_need_df = chapter_df[chapter_df['Knowledge Point'].isin(advanced_need_list)] # convert chapter_df to only include the knowledge points we want.
                    
                    chapter_info = {'Knowledge point': advanced_need_list, 'advanced_content': advanced_need_df['Advanced Content'].tolist()}
                    chapter_content.append(chapter_info)
                    syllabus = host.get_response(f"Create a syllabus for chapter '{chapter_name}' with this content: {json.dumps(chapter_info)}, don't be too long")
                    print("\n📚 Chapter Syllabus:")
                    print(syllabus)
                    
                    # Start the lecture 同理，根据advanced_need_list的knowledge point生成课程内容
                    Chapter_block(chapter_df, level = 'advanced', tutor, quiz, log_dir, main_log, retriever, advanced_need_list)
                    
            
            # Chapter coding quiz 和之前一样的chapter quiz流程
            df = pd.read_csv('coding_standard.csv')
            coding_habit = df.to_string(index=False) # For coding standard
            
            chapter_quiz_content = chapter_quiz.get_response(
                f"Create a comprehensive chapter test based on: {json.dumps(chapter_content, indent=2)}, and help the student follow these coding standards:{coding_habit} while they write their code.")

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
            
            time.sleep(WAIT_TIME)
       #总结部分     
# 这里开始又有变化， 总结历史记录，分别是课程内容，课程互动，quiz互动，然后全部传给host让他来做总结并推荐下一步学习
        course_summary = tutor.get_response("Summarize the course content covered so far, including chapters and knowledge points.")
        
        student_lecture_summary = tutor.get_response("Analyze the student's performance so far. Focus on their strengths, weaknesses, and overall progress.")
        
        student_quiz_summary = quiz.get_response("Analyze the student's performance so far. Focus on their strengths, weaknesses, and overall progress.")
            
        # Ending
        conclusion = host.get_response(f"Now that we have reached the end of this course, please provide a summary of the student's performance based on Course Summary: {course_summary}, Student Lecture Performance Summary: {student_lecture_summary}, and Student Quiz Performance Summary: {student_quiz_summary}. Additionally, suggest what they can do next to continue improving their skills in C programming.")
        print(conclusion) 
        
    except Exception as e:
        error_msg = f"Error in teaching session: {str(e)}"
        print(error_msg)
        log_message(main_log, f"ERROR: {error_msg}")

if __name__ == "__main__":
    main()

                    
                    
                
                
                
                
                
                
                
