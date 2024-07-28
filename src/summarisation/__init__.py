# summarizer = pipeline(task="summarization", model="facebook/bart-large-cnn")
# chunks = tokenize_content(section_text, summarizer.tokenizer)
# summary = summarize_chunks(chunks, summarizer.tokenizer, summarizer.model)
# o.sections[page_section['line']] = summary