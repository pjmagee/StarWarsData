from summarisation import RawFileProcessor

if __name__ == "__main__":
    # page_downloader = PageDownloader(output_dir="output/raw")
    # page_downloader.download_pages_with_infoboxes()

    raw_file_processor = RawFileProcessor(
        input_dir="output\\raw",
        output_dir="output\\summarised")

    raw_file_processor.process_raw_files()
