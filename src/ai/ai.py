import json

import openai

openai.api_key = 'sk-proj-XuQ7eeJ9hu3kv8lcoph0T3BlbkFJmmTeDhvkvJX0tdR7N4wo'


def create_function_fill_planet_schema() -> dict[str, any]:
    return {
        "type": "function",
        "function": {
            "name": "fill_planet_schema",
            "description": "Fill in the planet schema based on the provided text from the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "region": {"type": "string"},
                    "sector": {"type": "string"},
                    "system": {"type": "string"},
                    "stars": {"type": "array", "items": {"type": "string"}},
                    "position": {"type": "string"},
                    "moons": {"type": "array", "items": {"type": "string"}},
                    "coord": {
                        "$comment": "The coordinates of the planet (Galactic Standard)",
                        "type": "string"
                    },
                    "xyz": {"type": "string"},
                    "routes": {"type": "array", "items": {"type": "string"}},
                    "distance": {"type": "string"},
                    "lengthday": {"type": "string"},
                    "lengthyear": {"type": "string"},
                    "class": {"type": "string"},
                    "diameter": {"type": "string"},
                    "atmosphere": {
                        "$comment": "The atmosphere of the planet",
                        "type": "array", "items": {"type": "string"}
                    },
                    "climate": {"type": "array", "items": {"type": "string"}},
                    "gravity": {"type": "string"},
                    "terrain": {"type": "array", "items": {"type": "string"}},
                    "water": {"type": "string"},
                    "interest": {"type": "string"},
                    "flora": {"type": "array", "items": {"type": "string"}},
                    "fauna": {"type": "array", "items": {"type": "string"}},
                    "otherlife": {"type": "array", "items": {"type": "string"}},
                    "species": {"type": "array", "items": {"type": "string"}},
                    "otherspecies": {"type": "array", "items": {"type": "string"}},
                    "socialgroup": {"type": "string"},
                    "languages": {"type": "array", "items": {"type": "string"}},
                    "government": {"type": "string"},
                    "population": {"type": "number"},
                    "demonym": {"type": "string"},
                    "cities": {"type": "array", "items": {"type": "string"}},
                    "imports": {"type": "array", "items": {"type": "string"}},
                    "exports": {"type": "array", "items": {"type": "string"}},
                    "affiliations": {"type": "array", "items": {"type": "string"}},
                    "isCanon": {"type": "boolean"}
                },
                "required": ["name"]
            }
        }
    }


def call_openai_function(content, function_definition):
    """
    Call the OpenAI API to fill in the planet schema based on the provided text
    """
    

    response = openai.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """
                    You are an assistant that fills in the Planet Schema
                """
            },
            {
                "role": "user",
                "content": json.dumps(content)
            }
        ],
        model="gpt-4o",
        tools=[function_definition],
        tool_choice="auto"
    )
    arguments = response.choices[0].message.tool_calls[0].function.arguments
    return json.loads(arguments)
