import json

import openai
from http_utils import post
from prompts import GET_NOTE_HEADLINE, SUMMARIZE_NOTE_PROMPT
from openai import OpenAI

api_key = "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"
client = OpenAI(api_key=api_key)

def summarize_note(note):
    try:
        tool_call_mappings = dict({"create_calendar_event": lambda inp: 0})
        # Call the OpenAI Chat Completion API
        completion = client.chat.completions.create(
            model="gpt-4-0613",  # Ensure you're using a model that supports function calling
            messages=[
                {"role": "system", "content": SUMMARIZE_NOTE_PROMPT},
                {"role": "user", "content": note}
            ],
            functions=[
                {
                    "name": "create_calendar_event",
                    "description": "Create a Google Calendar event when an event with a start date is mentioned.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "The title of the calendar event."
                            },
                            "description": {
                                "type": "string",
                                "description": "A description of the calendar event."
                            },
                            "start_date": {
                                "type": "string",
                                "description": "The start date and time of the event in ISO 8601 format."
                            },
                            "end_date": {
                                "type": "string",
                                "description": "The end date and time of the event in ISO 8601 format."
                            },
                            "location": {
                                "type": "string",
                                "description": "The location where the event will take place."
                            }
                        },
                        "required": ["summary", "description", "start_date", "end_date", "location"],
                        "additionalProperties": False
                    }
                }
            ],
            function_call="auto"  # Let the model decide if it should call the function
        )

        response_message = completion.choices[0].message

        # Check if a function call was triggered
        tool_calls = response_message.tool_calls
        summary = response_message.content
        if tool_calls:
            for i in range(len(tool_calls)):
                function_name = tool_calls[i].function.name
                arguments = json.loads(tool_calls[i].function.arguments)
                tool_function = tool_call_mappings[function_name]
                tool_call_response = tool_function(json.loads(tool_calls[i].function.arguments))
                return {"summary": None, "function_call": {"name": function_name, "arguments": arguments}}
        else:
            # Return the summary content
            summary = response_message.get("content", "No summary created.")
            return {"summary": summary, "function_call": None}
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


    

