import json
import os

import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


def load_json_schema(file_path: str) -> (bool, dict[str, any] | None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Schema file not found: {file_path}")

    try:
        with open(file_path, 'r') as file:
            schema = json.load(file)
        return True, schema
    except json.JSONDecodeError as e:
        return False, None


def get_function_schema(name, description, json_schema) -> dict[str, dict[str, any] | str]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": json_schema,
        }
    }


def call_openai_function(content: any, function_definition: dict[str, any]):
    """
    Call the OpenAI API to fill in the planet schema based on the provided text
    """
    response = openai.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """
                    You are an assistant helping a user fill in the schema based on the provided text.
                """
            },
            {
                "role": "user",
                "content": json.dumps(obj=content, indent=None)
            }
        ],
        model="gpt-4o",
        tools=[function_definition],
        tool_choice="auto"
    )
    arguments = response.choices[0].message.tool_calls[0].function.arguments
    return json.loads(arguments)
