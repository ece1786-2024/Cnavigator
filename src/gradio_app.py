import gradio as gr
from initial_test.test0 import Tests

def create_quiz_interface(tests):
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
        
    return app

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