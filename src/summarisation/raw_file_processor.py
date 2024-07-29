import json
import os

from summarisation.text_summariser import TextSummariser


class RawFileProcessor:
    """
    A class to process raw files and summarise their content.
    """

    input_dir: str = "output/raw"
    output_dir: str = "output/summarised"

    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.summarizer = TextSummariser()
        self.summarizer.load_model("sshleifer/distilbart-cnn-12-6")

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
        with open(input_file, "r") as input:
            data = json.load(input)
            # loop hashmap of 'sections' field (key-value of string:string)
            for section_name, content in data["sections"].items():
                data["sections"][section_name] = self.summarizer.summarize(content)

            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir, exist_ok=True)

            with open(output_file, "w") as output:
                json.dump(data, output, indent=4)
