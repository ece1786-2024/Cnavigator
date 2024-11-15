import pandas as pd
file_path = 'C_Variables_Knowledge_Points.csv'
df = pd.read_csv(file_path,encoding='utf-8-sig')
       

for chapter_name, chapter_df in df.groupby('Chapter'):
    print(f"\n{'='*20} Chapter: {chapter_name} {'='*20}")