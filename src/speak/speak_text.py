#version 1 : a very ugly voice
# import pyttsx3
# import re
# def preprocess_text(text):
  
#     text = re.sub(r'[^\w\s.,!?\'"-]', '', text)
#     text = re.sub(r'`.*?`', '', text)
#     return text

# def speak_text(file_path):
#     try:
#         with open(file_path, 'r', encoding='utf-8') as file:
#             content = file.read()

#         content = preprocess_text(content)
#         engine = pyttsx3.init()
#         # engine.setProperty('rate', 150)  
#         # engine.setProperty('volume', 0.9)  
#         engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0')

        
        
#         engine.say(content)
#         engine.runAndWait()

#     except FileNotFoundError:
#         print(f"file not found：{file_path}")
#     except Exception as e:
#         print(f"errors：{e}")


# file_path = "src/speak/example.txt"
# # import os
# # print(os.path.abspath(file_path))
# speak_text(file_path)

# version 2: kind of ugly voice
import re
from gtts import gTTS
import os
def preprocess_text(text):
  
    text = re.sub(r'[^\w\s.,!?\'"-]', '', text)
    text = re.sub(r'`.*?`', '', text)
    return text

def speak_text(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        content = preprocess_text(content)
        tts = gTTS(content, lang='en', slow=False)
        
        #need to change the output file name here:
        tts.save("output.mp3")  
        os.system("start output.mp3")  

    except FileNotFoundError:
        print(f"file not found：{file_path}")
    except Exception as e:
        print(f"errors:{e}")


file_path = "src/speak/example.txt"
# import os
# print(os.path.abspath(file_path))
speak_text(file_path)



