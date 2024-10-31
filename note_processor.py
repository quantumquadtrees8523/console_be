from prompts import GET_NOTE_HEADLINE, SUMMARIZE_NOTE_PROMPT
from openai import OpenAI

api_key = "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"
client = OpenAI(api_key=api_key)

def summarize_note(note):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SUMMARIZE_NOTE_PROMPT},
            {
                "role": "user",
                "content": note
            }
        ]
    )

    try:
        return completion.choices[0].message.content
    except Exception as e:
        print(e)
        return note
    
def generate_note_headline(note):
    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": GET_NOTE_HEADLINE},
        {
            "role": "user",
            "content": note
        }])
    try:
        return completion.choices[0].message.content
    except Exception as e:
        print(e)
        return str(e)
