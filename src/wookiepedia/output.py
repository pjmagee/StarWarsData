from typing import Iterable

from wookiepedia.page_downloader import JSON


class Output:
    """
    Represents the output of the Wookiepedia page parser.
    """
    
    title: str
    page_id: int
    sections: dict[str, str]
    categories: set[str]
    infobox: JSON

    def __init__(self,
                 title: str,
                 page_id: int,
                 categories: Iterable[str],
                 sections: dict[str, str],
                 infobox: dict[str, any] | None):
        self.title = title
        self.page_id = page_id
        self.sections = sections
        self.categories = set(categories)
        self.infobox = infobox

    def to_dict(self):
        return {
            "title": self.title,
            "id": self.page_id,
            "sections": self.sections,
            "categories": list(self.categories),
            "infobox": self.infobox
        }
