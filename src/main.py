import ai
from summarisation import RawFileProcessor
from wookiepedia import PageDownloader
from schemas import SchemaProcessor

if __name__ == "__main__":

    # if False:
    #     page_downloader = PageDownloader(output_dir="output/raw")
    #     page_downloader.download_pages_with_infoboxes()
    # 
    # if False:
    #     raw_file_processor = RawFileProcessor(input_dir="output\\raw", output_dir="output\\summarised")
    #     raw_file_processor.process_raw_files()

    if True:

        character_schema = ai.load_json_schema("character")

        if character_schema is not None:
            schema_processor = SchemaProcessor(input_dir="output\\raw\\Character", output_dir="output\\schemas\\Character", json_schema=character_schema)
            schema_processor.process_raw_files()
