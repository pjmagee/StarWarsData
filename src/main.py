import logging

from wookiepedia import wookiepedia

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    wookiepedia.process_pages_with_infoboxes()