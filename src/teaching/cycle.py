import time
from typing import List
import pandas as pd
import gradio as gr
from openai import OpenAI
from threading import Event
from src.agents.base import TeachingAgent
from src.utils.helpers import create_agents
from src.config import WAIT_TIME

# Global variable
lecture_event = Event()
lecture_input_value = None
quiz_event = Event()
quiz_input_value = None

def submit_lecture_response(response):
    global lecture_input_value
    lecture_input_value = response
    lecture_event.set()
    return "Your response has been recorded."

def submit_quiz_response(response):
    global quiz_input_value
    quiz_input_value = response
    quiz_event.set()
    return "Your answer has been recorded."

def create_lecture_interface(knowledge_point_prompt, lecture):
    with gr.Blocks() as interface:
        gr.Markdown(f"# Lecture on {knowledge_point_prompt}")
        gr.Markdown(lecture)
        response_input = gr.Textbox(
            label="Your Question",
            placeholder="Enter any questions you have (type 'cccc' to proceed to quiz)"
        )
        submit_btn = gr.Button("Submit")
        output = gr.Textbox(label="Status", visible=False)
        
        submit_btn.click(
            fn=submit_lecture_response,
            inputs=response_input,
            outputs=output,
            show_progress=False
        )
    return interface

def create_quiz_interface(quiz_content):
    with gr.Blocks() as interface:
        gr.Markdown("# Quiz Time!")
        gr.Markdown(quiz_content)
        response_input = gr.Textbox(
            label="Your Answer",
            placeholder="Enter your answer (type 'cccc' to proceed to the next lesson)"
        )
        submit_btn = gr.Button("Submit")
        output = gr.Textbox(label="Status", visible=False)
        
        submit_btn.click(
            fn=submit_quiz_response,
            inputs=response_input,
            outputs=output,
            show_progress=False
        )
    return interface

def teaching_cycle(
    knowledge_point: str,
    knowledge_point_prompt: str,
    tutor: TeachingAgent,
    quiz: TeachingAgent,
    log_dir: str,
    retriever=None
):
    """Interactive teaching cycle for a single knowledge point"""
    cycle_log = f"{log_dir}/teaching_cycle_{time.strftime('%Y%m%d_%H%M%S')}_{knowledge_point.replace(' ', '_')}.txt"
    
    with open(cycle_log, 'w', encoding='utf-8') as f:
        f.write(f"Teaching Cycle for: {knowledge_point}\n{'=' * 50}\n")
    
    # Tutor explaining the knowledge point
    lecture = tutor.get_response_on_rag(
        f"Now, please explain this programming concept: {knowledge_point_prompt}",
        retriever
    )
    
    # Launch lecture interface
    lecture_interface = create_lecture_interface(knowledge_point_prompt, lecture)
    lecture_interface.launch(share=False, prevent_thread_lock=True)
    
    # Interactive discussion with tutor
    while True:
        lecture_event.wait()
        user_input = lecture_input_value
        lecture_event.clear()
        
        with open(cycle_log, 'a', encoding='utf-8') as f:
            f.write(f"\nLECTURE:\n{lecture}\n")
        
        if user_input.lower() == "cccc":
            print("OK! Let's do a tiny quiz!")
            break
        else:
            addition = tutor.get_response(f"{user_input}")
            print(addition)
            # Update lecture interface with the additional response
            lecture_interface = create_lecture_interface(knowledge_point_prompt, addition)
            lecture_interface.launch(share=False, prevent_thread_lock=True)
    
    # Quiz section
    print("\n📝 Generating quiz...")
    quiz_content = quiz.get_response(f"Now, based on the {lecture}, generate a quiz")
    
    # Launch quiz interface
    quiz_interface = create_quiz_interface(quiz_content)
    quiz_interface.launch(share=False, prevent_thread_lock=True)
    
    # Interactive quiz attempts
    while True:
        quiz_event.wait()
        student_answer = quiz_input_value
        quiz_event.clear()
        
        with open(cycle_log, 'a', encoding='utf-8') as f:
            f.write(f"\nQUIZ:\n{quiz_content}\n")
        
        if student_answer.lower() == "cccc":
            print("Loading next lesson......")
            break
        else:
            addition2 = quiz.get_response(f"{student_answer}")
            print(addition2)
            # Update quiz interface with additional feedback
            quiz_interface = create_quiz_interface(addition2)
            quiz_interface.launch(share=False, prevent_thread_lock=True)

def InLecture_block(
    chapter_df: pd.DataFrame,
    client: OpenAI,
    log_dir: str,
    main_log: str,
    teaching_style: str,
    retriever=None,
    unfamilar_list=[]
) -> List[str]:
    """Execute the lecture block for all knowledge points in a chapter"""
    tutor, quiz = create_agents(client, log_dir, teaching_style)
    
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
            log_dir,
            retriever
        )
        time.sleep(WAIT_TIME)
