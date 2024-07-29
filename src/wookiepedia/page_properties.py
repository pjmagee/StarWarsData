class PageProperties:
    """
    Class to represent the properties of a Wookiepedia page.
    """

    title: str
    sections: list[dict] = []
    infoboxes: list[dict] = []

    def __init__(self, title: str, sections: list[dict], infoboxes: list[dict]):
        self.title = title
        self.sections = sections
        self.infoboxes = infoboxes

    def to_dict(self):
        return {
            "title": self.title,
            "sections": self.sections,
            "infoboxes": self.infoboxes
        }
