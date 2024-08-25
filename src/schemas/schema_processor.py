import json
import os

import ai


class SchemaProcessor:
    """
    A class to process raw files and summarise their content.
    """

    input_dir: str = "output/raw"
    output_dir: str = "output/schemas"
    json_schema: ai.JsonSchema | None = None

    def __init__(self, input_dir: str, output_dir: str, json_schema: ai.JsonSchema):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.json_schema = json_schema

    def process_raw_files(self):
        for root, dirs, files in os.walk(self.input_dir):
            for input_file in files:
                if input_file.endswith(".json"):
                    relative_path = os.path.relpath(root, self.input_dir)
                    output_file_dir = os.path.join(self.output_dir, relative_path)
                    os.makedirs(output_file_dir, exist_ok=True)
                    output_file = os.path.join(output_file_dir, input_file)
                    input_file_path = os.path.join(root, input_file)
                    self.process_file(input_file_path, output_file)

    def process_file(self, input_file, output_file):

        function_definition = ai.get_function_definition(
            name=self.json_schema["title"],
            description="Fill in the schema based on the provided text",
            json_schema=self.json_schema)

        with open(input_file, "r") as i:
            data = json.load(i)
            # loop hashmap of 'sections' field (key-value of string:string)
            title = data["infobox"]["infobox"]["title"]

            response = ai.call_openai_function(title, function_definition)

            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir, exist_ok=True)

            with open(output_file, "w") as output:
                json.dump(response, output, indent=4)
