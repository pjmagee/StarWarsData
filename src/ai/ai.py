import json
import os
from typing import NewType

import openai
from openai import OpenAI
from openai.types.chat.completion_create_params import ResponseFormat

# openai.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

JsonSchema = NewType("JsonSchema", dict[str, any])


def load_json_schema(schema_name: str) -> JsonSchema | None:
    schema_file = os.path.join(os.path.dirname(__file__), "json_schemas", f"{schema_name}.json")

    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    try:
        with open(schema_file, 'r') as file:
            schema = json.load(file)
        return schema
    except json.JSONDecodeError as e:
        return None


def get_function_definition(
        name: str,
        description: str,
        json_schema: JsonSchema) -> dict[str, dict[str, any] | str]:
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
    Call the OpenAI API to fill in the schema based on the provided text
    """
    format = ResponseFormat(type="json_schema")
    format["json_schema"] = {
        "name": function_definition["function"]["name"],
        "strict": "true",
        "schema": function_definition["function"]["parameters"]
    }

    response = client.chat.completions.create(
        model="LM-Studio",
        messages=[
            {
                "role": "system",
                "content": """
                    You are a helpful Star Wars Wikipedia who is filling in the schema based on the provided user content.
                """
            },
            {
                "role": "user",
                "content": json.dumps(obj=content, indent=None)
            }
        ],
        response_format=format,
    )

    # response = response.choices[0].message.tool_calls[0].function.arguments
    response = response.choices[0].message.content
    return json.loads(response)
