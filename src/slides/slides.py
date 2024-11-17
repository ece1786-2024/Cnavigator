from openai import OpenAI
import matplotlib.pyplot as plt
import re
client = OpenAI(api_key="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")


def generate_ppt_content(lecture_script):
    prompt = f"""
    Based on the following lecture script, generate a concise PowerPoint slide. 
    The output should be in plain text, without using LaTeX format
    The output should only contain the following:
    1.title: A main heading for the topic.
    2.subtitle: Multiple subheadings with corresponding context (body text). Each subtitle should be followed by a description or explanation. 
    Make sure the content is clear, and the subheadings and body text are brief and informative. Use the following format:

    title: [Main heading of the presentation]
    subtitle: [First subheading]
    context: [Explanation or details related to the first subheading]

    subtitle: [Second subheading]
    context: [Explanation or details related to the second subheading]
    ...
    
    The content should be summarized and refined to fit within a single slide."
    \n\n{lecture_script}
    """
    
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Use the GPT-3.5 model or the latest model
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=200,
        temperature=0.5
    ).choices[0].message.content
    
    return response

def clean_text(text):
    
    #comment here is chinese, because i don't know the english version
    text = re.sub(r'\\[a-zA-Z]*\{.*?\}', '', text)  # 去掉 LaTeX 命令，如 \textbf{}
    text = re.sub(r'\*\*|\*', '', text)  # 去掉 Markdown 样式的加粗 (**) 或斜体 (*) 符号
    text = re.sub(r'\$.*?\$', '', text)  # 去掉美元符号包围的数学公式 ($...$)
    text = re.sub(r'\\[a-zA-Z]+', '', text)  # 去掉 LaTeX 命令（例如 \section, \subsection）
    text = text.replace('\n', ' ').strip()  # 去掉不必要的换行符和多余的空格
    text = re.sub(r'`(.*?)`', r'\1', text)  # 保留反引号包围的内容但去掉反引号，如`char`
    
    return text

def render_text_to_image(text_content, output_path="text_image.png"):
    
    main_title = None
    subtitles = []  
    contexts = []   

    
    title_match = re.search(r'title:\s*(.*?)\n', text_content)
    if title_match:
        main_title = clean_text(title_match.group(1))  

    
    subtitle_matches = re.findall(r'subtitle:\s*(.*?)\ncontext:\s*(.*?)\n', text_content, re.DOTALL)
    for match in subtitle_matches:
        subtitles.append(clean_text(match[0])) 
        contexts.append(clean_text(match[1]))   

    # PPT size (13.33 x 7.5 英寸)
    fig, ax = plt.subplots(figsize=(13.33, 7.5))
    fig.patch.set_facecolor('white')  
    
    
    # if u think it ugly, you can change it carefully
    if main_title:
        ax.text(0.05, 0.95, main_title, fontsize=34, fontweight='bold', ha='left', va='top', color='black')  

   
    y_position = 0.80  
    for subtitle, context in zip(subtitles, contexts):
        # subtitle: dark dark gray
        ax.text(0.05, y_position, f"{subtitle}:", fontsize=22, fontweight='bold', ha='left', va='top', color='#4B4B4B')  
        y_position -= 0.07  

        # sub content: dark gray
        ax.text(0.05, y_position, context, fontsize=18, ha='left', va='top', wrap=True, color='#6F6F6F')  
        y_position -= 0.15  
    
    ax.axis('off')  
    
    #remember to change the output_path in main function
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0.1, transparent=False)
    plt.close(fig)



# Example lecture script(i got it from one test)
lecture_script = """
Hey there, future C programming superstar! 🌟 Are you ready to dive into the world of characters? No, not the ones in your favorite TV show, but the ones that help us communicate with our computers! Today, we’re going to explore the `char` data type in C. 


So, what is a `char`, you ask? Well, it’s like the “one letter” superhero of the C programming language! It can store single characters, like 'a', 'B', or even 'Z'. But remember, characters are shy creatures, so they like to hang out in single quotes — like 'this'.

### Basic Content: What is `char`?

The `char` data type is used to store a single character. For example:
```c
char letter = 'A';
```
In this example, we’re declaring a variable named `letter`, and we’re assigning it the character 'A'. Easy-peasy, right?        

### Advanced Content: Character Arrays and Strings

But wait, there’s more! Just like how a superhero can have sidekicks, the `char` type can also be extended to character arrays and strings. When we want to store multiple characters together, we can do this:
```c
char name[] = "Alice";
```
Notice that we used double quotes here? That's because "Alice" is a string of characters! So, in C, strings are more like arrays of `char` types. Pretty neat, huh?

### Signed vs Unsigned `char`

Now, let’s get a little fancy and talk about signed and unsigned `char`.

- **Signed char**: This can hold values from -128 to 127. So if you think of it like a roller coaster, it can go down to negative heights!
- **Unsigned char**: This one is all positive, holding values from 0 to 255. So, no frowny faces allowed here.

The big difference is how they interpret the bits, which affects the range of characters they can represent. For example, if you use `signed char`, you can store some characters that are “negative” (like a bad review on a movie), while `unsigned char` focuses on all the happy, positive characters!

### ASCII and Unicode

And finally, we can’t forget about ASCII and Unicode. ASCII is like the original superhero team, which represents characters using numbers from 0 to 127. It’s perfect for English characters and some control characters. However, when you want to go global and represent characters from different languages, you need Unicode, which can cover a much wider range of characters. So, if you want to write a program that speaks multiple languages, Unicode has got your back!

### Example Recap

To wrap this up, here’s a quick example:
```c
#include <stdio.h>

int main() {
    char letter = 'A';
    char name[] = "Alice";
    signed char s_char = -5; // can store negative values
    unsigned char u_char = 250; // only positive values

    printf("Single character: %c\n", letter);
    printf("String: %s\n", name);
    printf("Signed char: %d\n", s_char);
    printf("Unsigned char: %u\n", u_char);

    return 0;
}
```

In this code, we’re showing off our `char` variable, a string, and both signed and unsigned characters. The `printf` function prints them out for us.

Now, do you have any questions about `char`, signed vs. unsigned, or ASCII and Unicode? Or maybe you want to see more examples? Let me know! 🦸‍♂️"""


ppt_content = generate_ppt_content(lecture_script)
# print(ppt_content)

render_text_to_image(ppt_content)
