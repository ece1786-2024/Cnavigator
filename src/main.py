import os
import pandas as pd
from openai import OpenAI
import json

from config import OPENAI_API_KEY, CSV_FILE_PATH, LOG_DIR, WAIT_TIME
from utils.logger import create_log_directory, create_log_file, log_message
from utils.langchain_setup import LangChainService
from utils.helpers import create_chapter_agents
from initial_test.test0 import  Tests,ChapterTest
import gradio as gr

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

def create_style_section():
    with gr.Column(visible=False) as style_section:
        gr.Markdown("## Select Your Preferred Teaching Style")
        style_dropdown = gr.Dropdown(
            choices=["Humorous", "Serious", "Interactive", 
                    "Calm", "Engaging", "Inspiring"],
            label="Choose a teaching style:",
            interactive=True
        )
        submit_button = gr.Button("Submit")
        style_result = gr.Markdown()
        start_button = gr.Button("Start Learning")
        
        return style_section
def create_chapter_quiz_section(tests):
    with gr.Column(visible=True) as chapter_quiz_section:
        # # question UI
        # q = tests.get_questions_for_chapter()
        # gr.Markdown(f"**Chapter:** {q['chapter']}")
        # gr.Markdown(f"**Question:** {q['question']}")
        
        # exp_choice = gr.Radio(
        #     choices=q['options'],
        #     label="Please select your answer:",
        #     interactive=True
        # )
        # exp_submit = gr.Button("Submit Answer")
        # first_result = gr.Markdown(visible=True)
        
        # questions UI
        with gr.Column(visible=False) as basic_questions:
            choices, submits, results = [], [], []
            for question in tests.get_questions_for_chapter():
                gr.Markdown("---")
                gr.Markdown(f"**Chapter:** {question['chapter']}")
                gr.Markdown(f"**Question:** {question['question']}")
                
                choice = gr.Radio(
                    choices=question['options'],
                    label="Please select your answer:",
                    interactive=True
                )
                submit = gr.Button("Submit Answer")
                result = gr.Markdown(visible=True)
                
                choices.append(choice)
                submits.append(submit)
                results.append(result)
        
        final_result = gr.Markdown(visible=True)
        finish_button = gr.Button("Finish Quiz", visible=True)

def base_ui_updates(interactive, visible, message):
    return [
        gr.update(interactive=interactive),
        gr.update(visible=visible),
        gr.update(value=message)
    ]

def switch_to_style_section(quiz_section, style_section, finish_button, final_result):
    return [
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(value="Please select your preferred teaching style")
    ]

def main():
    try:
        # Initialize environment and services
        log_dir, client, main_log, df, retriever = setup_environment()
        
        # Run initial test and get results
        tests = Tests("ini_test.csv")
        familar_list, teaching_style = tests.get_results()
        
        with gr.Blocks() as app:
            with gr.Column(visible=True) as quiz_section:
                # Initial question UI
                initial_q = tests.get_initial_question()
                gr.Markdown(f"**Chapter:** {initial_q['chapter']}")
                gr.Markdown(f"**Question:** {initial_q['question']}")
                
                exp_choice = gr.Radio(
                    choices=initial_q['options'],
                    label="Please select your answer:",
                    interactive=True
                )
                exp_submit = gr.Button("Submit Answer")
                first_result = gr.Markdown(visible=True)
                
                # Detailed questions UI
                with gr.Column(visible=False) as basic_questions:
                    choices, submits, results = [], [], []
                    for question in tests.get_remaining_questions():
                        gr.Markdown("---")
                        gr.Markdown(f"**Chapter:** {question['chapter']}")
                        gr.Markdown(f"**Question:** {question['question']}")
                        
                        choice = gr.Radio(
                            choices=question['options'],
                            label="Please select your answer:",
                            interactive=True
                        )
                        submit = gr.Button("Submit Answer")
                        result = gr.Markdown(visible=True)
                        
                        choices.append(choice)
                        submits.append(submit)
                        results.append(result)
                
                final_result = gr.Markdown(visible=True)
                finish_button = gr.Button("Finish Quiz", visible=True)
                
            # Style selection UI
            style_section = create_style_section()
            
            # Event handlers
            def on_first_submit(choice):
                is_basic, chapters = tests.check_initial_answer(choice)
                if not choice:
                    return base_ui_updates(True, False, "Please select an answer")
                if is_basic:
                    return base_ui_updates(False, False, 
                        f"Test completed. These chapters will be covered in detail: {', '.join(chapters)}")
                return base_ui_updates(False, True, "Proceeding with detailed assessment...")
            
            exp_submit.click(
                fn=on_first_submit,
                inputs=[exp_choice],
                outputs=[exp_choice, basic_questions, first_result]
            )
            
            def on_answer_submit(choice, row_idx):
                if not choice:
                    return [gr.update(interactive=True), gr.update(value="Please select an answer")]
                
                is_correct = tests.check_answer(choice, row_idx)
                return [
                    gr.update(interactive=False),
                    gr.update(value="Correct!" if is_correct else "Incorrect.")
                ]
            
            for idx, (choice, submit, result) in enumerate(zip(choices, submits, results)):
                submit.click(
                    fn=lambda c, i=idx: on_answer_submit(c, i),
                    inputs=[choice],
                    outputs=[choice, result]
                )
                
            finish_button.click(
                fn=lambda: switch_to_style_section(quiz_section, style_section, 
                                                finish_button, final_result),
                outputs=[quiz_section, style_section, finish_button, final_result]
            )
            

        
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
                    # unfamilar_list = init_chapter_test(chapter_name)
                    chaptertests = ChapterTest("chapter_test.csv")
                    unfamilar_list = chaptertests.get_results()
                    
                    with gr.Column(visible=True) as chapter_quiz_section:       
                        # questions UI
                        with gr.Column(visible=False) as chapter_basic_questions:
                            choices, submits, results = [], [], []
                            for question in chaptertests.get_questions_for_chapter():
                                gr.Markdown("---")
                                gr.Markdown(f"**Chapter:** {question['chapter']}")
                                gr.Markdown(f"**Question:** {question['question']}")
                                
                                choice = gr.Radio(
                                    choices=question['options'],
                                    label="Please select your answer:",
                                    interactive=True
                                )
                                submit = gr.Button("Submit Answer")
                                result = gr.Markdown(visible=True)
                                
                                choices.append(choice)
                                submits.append(submit)
                                results.append(result)
                        
                        final_result = gr.Markdown(visible=True)
                        finish_button = gr.Button("Finish Quiz", visible=True)
                    
                    # Event handlers    
                    def on_answer_submit_chapter(choice, row_idx):
                        if not choice:
                            return [gr.update(interactive=True), gr.update(value="Please select an answer")]
                        
                        is_correct = chaptertests.check_answer(choice, row_idx)
                        return [
                            gr.update(interactive=False),
                            gr.update(value="Correct!" if is_correct else "Incorrect.")
                        ]
                    
                    for idx, (choice, submit, result) in enumerate(zip(choices, submits, results)):
                        submit.click(
                            fn=lambda c, i=idx: on_answer_submit_chapter(c, i),
                            inputs=[choice],
                            outputs=[choice, result]
                        )
                        
                    #！这里暂时不会改
                    # finish_button.click(
                    #     fn=lambda: switch_to_style_section(quiz_section, style_section, 
                    #                                     finish_button, final_result),
                    #     outputs=[quiz_section, style_section, finish_button, final_result]
                    # )
                    
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
                    # print(chapter_quiz_content)
                    with gr.Column() as chapter_quiz_content:
                        gr.Markdown("---")
                        gr.Markdown(f"chapter_quiz_content")
                        gr.Markdown(chapter_quiz_content)
                    
                    
                    
                    
                    
                    def chapter_quiz_response(answer):
                        if answer.lower() == "cccc":
                            return "Loading next chapter......", True  # 第二个值用于指示是否进入下一章
                        else:
                            answer = chapter_quiz.get_response(f"{coding_answer}")
                            return answer, False

                    def handle_answer(answer, log):
                        with open("main_log.txt", 'a', encoding='utf-8') as f:
                            f.write(f"\nLECTURE:\n{chapter_quiz_content}\nANSWER: {answer}\n")
                        response, next_chapter = chapter_quiz_response(answer)
                        if next_chapter:
                            return response, gr.update(visible=False), gr.update(value=""), gr.update(value="")
                        else:
                            return response, gr.update(visible=True), gr.update(value=""), gr.update(value="")

               
                    with gr.Blocks() as coding_answer:
                        with gr.Column():
                
                            answer_box = gr.Textbox(label="Type your answer:")
                            submit_button = gr.Button("Submit Answer")
                            result = gr.Markdown("")
                            reset_button = gr.Button("Reset Chapter", visible=False)
                            
                            
                            submit_button.click(
                                fn=handle_answer,
                                inputs=[answer_box, "main_log.txt"],
                                outputs=[result, reset_button, answer_box, result]
                            )
                            
                
                
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
                    # print("\n📚 Chapter Syllabus:")
                    # print(syllabus)
                    with gr.Column() as chapter_syllabus:
                        gr.Markdown("---")
                        gr.Markdown(f"Chapter Syllabus:")
                        gr.Markdown(syllabus)
                    
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
                    with gr.Column() as chapter_quiz_content:
                        gr.Markdown("---")
                        gr.Markdown(f"chapter_quiz_content")
                        gr.Markdown(chapter_quiz_content)
                          
                    
                    def chapter_quiz_response(answer):
                        if answer.lower() == "cccc":
                            return "Loading next chapter......", True  # 第二个值用于指示是否进入下一章
                        else:
                            answer = chapter_quiz.get_response(f"{coding_answer}")
                            return answer, False

                    def handle_answer(answer, log):
                        with open("main_log.txt", 'a', encoding='utf-8') as f:
                            f.write(f"\nLECTURE:\n{chapter_quiz_content}\nANSWER: {answer}\n")
                        response, next_chapter = chapter_quiz_response(answer)
                        if next_chapter:
                            return response, gr.update(visible=False), gr.update(value=""), gr.update(value="")
                        else:
                            return response, gr.update(visible=True), gr.update(value=""), gr.update(value="")

                    with gr.Blocks() as coding_answer:
                        with gr.Column():
                
                            answer_box = gr.Textbox(label="Type your answer:")
                            submit_button = gr.Button("Submit Answer")
                            result = gr.Markdown("")
                            reset_button = gr.Button("Reset Chapter", visible=False)
                            
                            
                            submit_button.click(
                                fn=handle_answer,
                                inputs=[answer_box, "main_log.txt"],
                                outputs=[result, reset_button, answer_box, result]
                            )
                            
                
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
