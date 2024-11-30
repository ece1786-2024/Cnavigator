import pandas as pd
import gradio as gr

import pandas as pd

class Tests:
    def __init__(self, file_path="ini_test.csv"):
        self.df = pd.read_csv(file_path, encoding='utf-8-sig')
        self.familiar_chapters = []
        self.selected_style = None
        
    def get_initial_question(self):
        return {
            'chapter': self.df.iloc[0]['Chapter'],
            'question': self.df.iloc[0]['Question'],
            'options': [
                self.df.iloc[0]['Option A'],
                self.df.iloc[0]['Option B'],
                self.df.iloc[0]['Option C'],
                self.df.iloc[0]['Option D']
            ]
        }
    
    def get_remaining_questions(self):
        questions = []
        for _, row in self.df.iloc[1:].iterrows():
            questions.append({
                'chapter': row['Chapter'],
                'question': row['Question'],
                'options': [
                    row['Option A'],
                    row['Option B'],
                    row['Option C'],
                    row['Option D']
                ],
                'answer': row['Answer']
            })
        return questions
    
    def check_initial_answer(self, choice):
        if not choice:
            return False, None
            
        if choice == self.df.iloc[0]['Option A']:
            chapters = self.df['Chapter'].tolist()[1:]
            return True, chapters
        return False, None
        
    def check_answer(self, choice, question_idx):
        if not choice:
            return False
            
        row = self.df.iloc[question_idx + 1]
        correct = choice == row[f'Option {row["Answer"]}']
        if correct:
            self.familiar_chapters.append(row['Chapter'])
        return correct
        
    def set_teaching_style(self, style):
        self.selected_style = f"Your speaking style is {style.lower()}."
        return self.selected_style
        
    def get_results(self):
        return self.familiar_chapters, self.selected_style or "No style selected"
    
def init_chapter_test(chapter_name,file_path = "chapter_test.csv"):
    

    # print(file_path)
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    
    
    unfamilar_list=[]
    
    for index, row in df.iterrows():
        if chapter_name!=row['Chapter']:
            continue
        print("\nQuiz Content:")
        print("Chapter:", row['Chapter'])
        print("Question:", row['Question'])
        print("Option A:", row['Option A'])
        print("Option B:", row['Option B'])
        print("Option C:", row['Option C'])
        print("Option D:", row['Option D'])
        print("\nPlease enter your answer:")
        student_response = input()
        
        if student_response.upper()!=row['Answer']:
            unfamilar_list.append(row['Knowledge Point'])

    # print(unfamilar_list)
    return unfamilar_list
