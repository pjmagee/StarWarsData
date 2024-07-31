import logging
from typing import Union, Dict, Any, List

from wookiepedia.output import Output
from wookiepedia.page_properties import PageProperties
from wookiepedia.page_downloader import PageDownloader

# Initialize the logger at the module level
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
