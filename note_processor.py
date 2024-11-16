import json
from typing import List

import openai
from http_utils import post
from prompts import GET_NOTE_HEADLINE, SUMMARIZE_NOTE_PROMPT
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionMessage

api_key = "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"
client = OpenAI(api_key=api_key)

def summarize(notes: List[str]):
    try:
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": SUMMARIZE_NOTE_PROMPT}
        ]
        for note in notes:
            messages.append({"role": "user", "content": note})
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        response_message: ChatCompletionMessage = completion.choices[0].message
        return response_message.content if hasattr(response_message, 'content') else "No summary created."
    except Exception as e:
        print(e)
        return str(e)


def generate_note_headline(note):
    completion = client.chat.completions.create(
    model="gpt-4o-mini",
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


    

