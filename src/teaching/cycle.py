# src/teaching/cycle.py

import time
import json
from typing import List
import pandas as pd
from openai import OpenAI
from src.agents.base import TeachingAgent
from src.utils.helpers import create_agents
from src.config import WAIT_TIME

def teaching_cycle(
    knowledge_point: str,
    knowledge_point_prompt: str,
    tutor: TeachingAgent,
    quiz: TeachingAgent,
    client: OpenAI,
    log_dir: str,
    retriever=None
):
    """Interactive teaching cycle for a single knowledge point"""
    cycle_log = f"{log_dir}/teaching_cycle_{time.strftime('%Y%m%d_%H%M%S')}_{knowledge_point.replace(' ', '_')}.txt"
    
    with open(cycle_log, 'w', encoding='utf-8') as f:
        f.write(f"Teaching Cycle for: {knowledge_point}\n{'=' * 50}\n")
    
    print(f"\n🎓 Tutor explaining: {knowledge_point_prompt}")
    lecture = tutor.get_response_on_rag(
        f"Now, please explain this programming concept: {knowledge_point_prompt}",
        retriever
    )
    print(lecture)
    
    # Interactive discussion with tutor
    while True:
        user_input = input("any question? ")
        with open(cycle_log, 'a', encoding='utf-8') as f:
            f.write(f"\nLECTURE:\n{lecture}\n")
        if user_input.lower() == "cccc":
            print("OK! Let's do a tiny quiz!")
            break
        else:
            addition = tutor.get_response(f"{user_input}")
            print(addition)
    
    # Quiz section
    print("\n📝 Generating quiz...")
    quiz_content = quiz.get_response(f"Now, based on the {lecture}, generate a quiz")
    print(quiz_content)
    
    # Interactive quiz attempts
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

def InLecture_block(
    chapter_df: pd.DataFrame,
    client: OpenAI,
    log_dir: str,
    main_log: str,
    retriever=None,
    unfamilar_list=[]
) -> List[str]:
    """Execute the lecture block for all knowledge points in a chapter"""
    tutor, quiz = create_agents(client, log_dir)
    
    for _, row in chapter_df.iterrows():
        knowledge_point = row['Knowledge Point']
        
        if knowledge_point not in unfamilar_list:
            continue
        
        
        basic_content = row['Basic Content']
        advanced_content = row['Advanced Content']
        
        knowledge_point_prompt = f"""Knowledge Point: {knowledge_point}
        Basic Content: {basic_content}
        Advanced Content: {advanced_content}"""
        
        log_message = f"\n=== Starting lesson for: {knowledge_point} ==="
        print(log_message)
        with open(main_log, 'a', encoding='utf-8') as f:
            f.write(f"{log_message}\n")
        
        teaching_cycle(
            knowledge_point, 
            knowledge_point_prompt, 
            tutor, 
            quiz, 
            client, 
            log_dir,
            retriever
        )
        time.sleep(WAIT_TIME)