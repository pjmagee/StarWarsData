from transformers import pipeline
from summarisation.text_paraphraser import TextParaphraser


class TextSummariser:
    """
    A class to perform text summarization using the Hugging Face Transformers library.
    """

    def __init__(self):
        self.summarization_pipeline = None
        self.paraphraser = TextParaphraser()

    def load_model(self, model_name):
        self.summarization_pipeline = pipeline(
            task="summarization",
            model=model_name)

    def summarize(self, content: str, max_length=1024):

        if len(content) <= 250:
            return self.paraphraser.paraphrase(content)

        chunks = self.tokenize_content(
            content=content,
            max_length=max_length)
        return self.summarize_chunks(chunks=chunks)

    def tokenize_content(self, content, max_length=1024):
        tokens = (self.summarization_pipeline.
                  tokenizer(content,
                            return_tensors="pt",
                            truncation=True,
                            padding='longest',
                            max_length=max_length))
        input_ids = tokens.input_ids[0]
        chunks = []

        for i in range(0, len(input_ids), max_length):
            chunk = self.summarization_pipeline.tokenizer.decode(
                input_ids[i:i + max_length],
                skip_special_tokens=True)
            chunks.append(chunk)

        return chunks

    def summarize_chunks(self, chunks):
        summaries = []
        for chunk in chunks:
            summary = self.summarization_pipeline(
                chunk,
                max_length=250,
                min_length=20,
                length_penalty=1.5,
                num_beams=4,
                early_stopping=True)
            decoded = summary[0]['summary_text']
            summaries.append(decoded)

        return ''.join(summaries)
