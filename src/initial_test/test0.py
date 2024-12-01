import pandas as pd
def init_test(file_path = "ini_test.csv"):
    

    # print(file_path)
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    # print(df)

    #test if students have know something about C, if not, skip all following questions
    print("\nQuiz Content:")
    print("Chapter:", df.iloc[0]['Chapter'])
    print("Question:", df.iloc[0]['Question'])
    print("Option A:", df.iloc[0]['Option A'])
    print("Option B:", df.iloc[0]['Option B'])
    print("Option C:", df.iloc[0]['Option C'])
    print("Option D:", df.iloc[0]['Option D'])
    print("\nPlease enter your answer:")
    student_response = input()

    df=df.iloc[1:]    
    if student_response.upper()=='A':
        return df['Chapter'].tolist()[1:]
    
    unfamiliar_list=[]
    
    for index, row in df.iterrows():
        print("\nQuiz Content:")
        print("Chapter:", row['Chapter'])
        print("Question:", row['Question'])
        print("Option A:", row['Option A'])
        print("Option B:", row['Option B'])
        print("Option C:", row['Option C'])
        print("Option D:", row['Option D'])
        print("\nPlease enter your answer:")
        student_response = input()
        
        if student_response.upper() != row['Answer']:
            unfamiliar_list.append(row['Chapter'])


    # print(unfamilar_list)
    return unfamiliar_list

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
