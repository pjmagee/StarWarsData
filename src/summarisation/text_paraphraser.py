import torch

from transformers import BartForConditionalGeneration, BartTokenizer, pipeline


class TextParaphraser:
    """
    A class to perform text paraphrasing using the Hugging Face Transformers library.
    """
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = BartForConditionalGeneration.from_pretrained('eugenesiow/bart-paraphrase')
        self.model = self.model.to(self.device)
        self.tokenizer = BartTokenizer.from_pretrained('eugenesiow/bart-paraphrase')

    def paraphrase(self, text: str):
        batch = self.tokenizer(text=text,
                               return_tensors="pt").to(self.device)  # Move the batch to the same device as the model
        generated_ids = self.model.generate(batch['input_ids'])
        generated_sentence = self.tokenizer.decode(
            generated_ids[0],
            max_new_tokens=150,
            skip_special_tokens=True)
        return generated_sentence
