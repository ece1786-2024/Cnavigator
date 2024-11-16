import time
import json
from typing import List
import pandas as pd
from openai import OpenAI
from src.agents.base import TeachingAgent
from src.utils.helpers import get_student_input, create_agents
from src.config import MAX_ATTEMPTS, WAIT_TIME

def teaching_cycle(
    knowledge_point: str,
    knowledge_point_prompt: str,
    tutor: TeachingAgent,
    quiz: TeachingAgent,
    client: OpenAI,
    log_dir: str,
    retriever=None
) -> str:
    cycle_log = f"{log_dir}/teaching_cycle_{time.strftime('%Y%m%d_%H%M%S')}_{knowledge_point.replace(' ', '_')}.txt"
    
    with open(cycle_log, 'w', encoding='utf-8') as f:
        f.write(f"Teaching Cycle for: {knowledge_point}\n{'=' * 50}\n")
    
    print(f"\n🎓 Tutor explaining: {knowledge_point_prompt}")
    lecture = tutor.get_response_on_rag(
        f"Please explain this programming concept: {knowledge_point_prompt}",
        retriever
    )
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
    student_answers = get_student_input(quiz_content, lecture, cycle_log)
    print("Student submitted answers.")
    
    grading_prompt = f"""
    Topic: {knowledge_point}
    Lecture: {lecture}
    Quiz: {quiz_content}
    Student Answers: {student_answers}
    
    Please grade the student's answers and provide feedback.
    """
    
    grading_result = quiz.get_response(grading_prompt)
    
    with open(cycle_log, 'a', encoding='utf-8') as f:
        f.write(f"\nGRADING RESULTS:\n{grading_result}\n")
    print(grading_result)
    return grading_result

def InLecture_block(
    chapter_df: pd.DataFrame,
    client: OpenAI,
    log_dir: str,
    main_log: str,
    retriever=None
) -> List[str]:
    """Execute the knowledge point learning cycle and return passed points"""
    passed_points = []
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
        
        attempts = 0
        passed = False
        
        while not passed and attempts < MAX_ATTEMPTS:
            attempts += 1
            log_message = f"\n📚 Attempt {attempts} of {MAX_ATTEMPTS}"
            print(log_message)
            
            with open(main_log, 'a', encoding='utf-8') as f:
                f.write(f"{log_message}\n")
            
            grading_result = teaching_cycle(
                knowledge_point,
                knowledge_point_prompt,
                tutor,
                quiz,
                client,
                log_dir,
                retriever
            )
            
            if 'pass' in grading_result.lower():
                passed = True
                passed_points.append(knowledge_point)
                log_message = f"\n✅ Passed! Moving to next topic."
                print(log_message)
                with open(main_log, 'a', encoding='utf-8') as f:
                    f.write(f"{log_message}\n")
            elif attempts < MAX_ATTEMPTS:
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
                log_message = f"\n❌ Maximum attempts reached. Moving to next topic."
                print(log_message)
                with open(main_log, 'a', encoding='utf-8') as f:
                    f.write(f"{log_message}\n")
        
        time.sleep(WAIT_TIME)
    
    return passed_points