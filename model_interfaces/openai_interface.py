import json

from openai import OpenAI
from typing import List
from http_utils import post
from prompts import GET_NOTE_HEADLINE, SUMMARIZE_NOTE_PROMPT
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionMessage

api_key = "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"
client = OpenAI(api_key=api_key)

def summarize(notes: List[str]) -> str:
    print("OpenAI predicting...")
    try:
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": SUMMARIZE_NOTE_PROMPT}
        ]
        for note in notes:
            messages.append({"role": "user", "content": note})
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        response_message: ChatCompletionMessage = completion.choices[0].message
        print("OpenAI response successful!")
        return response_message.content if hasattr(response_message, 'content') and response_message.content else "No summary created."
    except Exception as e:
        print("OpenAI Error.")
        print(e)
        raise Exception("OpenAI Rate Limit Hit.")


def generate_note_headline(note) -> str:
    print("OpenAI predicting...")
    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": GET_NOTE_HEADLINE},
        {
            "role": "user",
            "content": note
        }])
    try:
        print("OpenAI response successful!")
        note_headline = completion.choices[0].message.content
        return note_headline if note_headline else "No headline available"
    except Exception as e:
        print("OpenAI Error.")
        print(e)
        raise Exception("OpenAI Rate Limit Hit.")


    

