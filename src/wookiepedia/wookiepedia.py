import json
import logging
from typing import Union, Dict, Any, List
from urllib.parse import urlencode

import openai
import requests
from bs4 import BeautifulSoup

JSON = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


openai.api_key = 'sk-proj-XuQ7eeJ9hu3kv8lcoph0T3BlbkFJmmTeDhvkvJX0tdR7N4wo'
trim_values: str = "\"',.:-"
trim_contents: str = "\"',."

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
url = "https://starwars.fandom.com/api.php"

ignore_sections = [
    "Appearances",
    "Sources",
    "Notes and references",
    "External links",
    "Behind the scenes",
    "Non-canon appearances",
    "Real-world similarities",
    "Non-canon sources"
]


def process_pages_with_infoboxes():
    should_continue = True
    params = {
        "action": "query",
        "list": "pageswithprop",
        "pwppropname": "infoboxes",
        "pwplimit": "max",
        "pwpcontinue": 1,
        "format": "json"
    }
    full_url = f"{url}?{urlencode(params)}"
    logging.info(f"Making request to {full_url}")

    while should_continue:
        response = requests.get(url, params=params)
        data = response.json()
        should_continue = data.get("continue", False)

        if should_continue:
            params['pwpcontinue'] = data["continue"]["pwpcontinue"]

        for item in data['query']['pageswithprop']:
            title = str(item['title'])
            pageid = int(item['pageid'])
            page_properties = get_page_props(title)

            o = Output()
            o.title = title
            o.id = pageid
            o.categories.extend(get_page_categories(title))

            for page_section in page_properties.sections:
                section_html = get_section_content(title, page_section['index'])
                section_text = text_cleanup(section_html)
                o.sections[page_section['line']] = section_text

            for infobox in page_properties.infoboxes:
                o.infoboxes.append(infobox)

            logging.info(json.dumps(o.to_dict(), indent=2, ensure_ascii=False))


def get_category_members(name: str = "Planets", limit: int = 10):
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": "Category:" + name,
        "cmlimit": limit,
        "format": "json"
    }

    full_url = f"{url}?{urlencode(params)}"
    logging.info(f"Making request to {full_url}")

    response = requests.get(url, params=params)
    data = response.json()
    return data['query']['categorymembers']


class PageProperties:
    title: str
    sections: list[str] = []
    infoboxes: list[dict] = []

    def __init__(self, title: str, sections: list[str], infoboxes: list[dict]):
        self.title = title
        self.sections = sections
        self.infoboxes = infoboxes

    def to_dict(self):
        return {
            "title": self.title,
            "sections": self.sections,
            "infoboxes": self.infoboxes
        }

def get_page_props(title: str) -> PageProperties:
    params = {
        "action": "parse",
        "page": title,
        "format": "json",
        "prop": "sections|properties"
    }
    full_url = f"{url}?{urlencode(params)}"
    logging.info(f"Making request to {full_url}")
    response = requests.get(url, params=params)
    data = response.json()
    all_sections = data['parse']['sections']
    page_sections = [section for section in all_sections if section['line'] not in ignore_sections]
    page_infoboxes = []

    for prop in data['parse']['properties']:
        name = prop['name']
        value = prop['*']
        if name == 'infoboxes' and value is not None:
            page_infoboxes.append(parse_infobox(value))

    return PageProperties(
        title=title,
        sections=page_sections,
        infoboxes=page_infoboxes
    )


def get_section_content(page_title, section_index) -> str:
    params = {
        "action": "parse",
        "page": page_title,
        "prop": "text",
        "section": section_index,
        "format": "json"
    }
    full_url = f"{url}?{urlencode(params)}"
    logging.info(f"Making request to {full_url}")
    response = requests.get(url, params=params)
    data = response.json()
    return data["parse"]["text"]["*"]


def get_infobox_templates():
    params = {
        "action": "query",
        "list": "allpages",
        "apprefix": "Infobox",
        "apnamespace": 10,  # Namespace 10 is for templates
        "aplimit": "max",
        "format": "json"
    }
    full_url = f"{url}?{urlencode(params)}"
    logging.info(f"Making request to {full_url}")
    response = requests.get(url, params=params)
    data = response.json()
    templates = [page['title'] for page in data['query']['allpages']]
    return templates


def get_page_categories(title: str) -> list[str]:
    params = {
        "action": "parse",
        "page": title,
        "format": "json",
        "prop": "categories"
    }
    full_url = f"{url}?{urlencode(params)}"
    logging.info(f"Making request to {full_url}")
    response = requests.get(url, params=params)
    data = response.json()
    categories = [cat["*"] for cat in data["parse"]["categories"]]
    return categories


def create_function_fill_planet_schema():
    return {
        "type": "function",
        "function": {
            "name": "fill_planet_schema",
            "description": "Fill in the planet schema based on the provided text from the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "region": {"type": "string"},
                    "sector": {"type": "string"},
                    "system": {"type": "string"},
                    "stars": {"type": "array", "items": {"type": "string"}},
                    "position": {"type": "string"},
                    "moons": {"type": "array", "items": {"type": "string"}},
                    "coord": {
                        "$comment": "The coordinates of the planet (Galactic Standard)",
                        "type": "string"
                    },
                    "xyz": {"type": "string"},
                    "routes": {"type": "array", "items": {"type": "string"}},
                    "distance": {"type": "string"},
                    "lengthday": {"type": "string"},
                    "lengthyear": {"type": "string"},
                    "class": {"type": "string"},
                    "diameter": {"type": "string"},
                    "atmosphere": {
                        "$comment": "The atmosphere of the planet",
                        "type": "array", "items": {"type": "string"}
                    },
                    "climate": {"type": "array", "items": {"type": "string"}},
                    "gravity": {"type": "string"},
                    "terrain": {"type": "array", "items": {"type": "string"}},
                    "water": {"type": "string"},
                    "interest": {"type": "string"},
                    "flora": {"type": "array", "items": {"type": "string"}},
                    "fauna": {"type": "array", "items": {"type": "string"}},
                    "otherlife": {"type": "array", "items": {"type": "string"}},
                    "species": {"type": "array", "items": {"type": "string"}},
                    "otherspecies": {"type": "array", "items": {"type": "string"}},
                    "socialgroup": {"type": "string"},
                    "languages": {"type": "array", "items": {"type": "string"}},
                    "government": {"type": "string"},
                    "population": {"type": "number"},
                    "demonym": {"type": "string"},
                    "cities": {"type": "array", "items": {"type": "string"}},
                    "imports": {"type": "array", "items": {"type": "string"}},
                    "exports": {"type": "array", "items": {"type": "string"}},
                    "affiliations": {"type": "array", "items": {"type": "string"}},
                    "isCanon": {"type": "boolean"}
                },
                "required": ["name"]
            }
        }
    }


def call_openai_function(content, function_definition):
    """
    Call the OpenAI API to fill in the planet schema based on the provided text
    """

    response = openai.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """
                    You are an assistant that fills in the Planet Schema
                """
            },
            {
                "role": "user",
                "content": json.dumps(content)
            }
        ],
        model="gpt-4o",
        tools=[function_definition],
        tool_choice="auto"
    )
    arguments = response.choices[0].message.tool_calls[0].function.arguments
    return json.loads(arguments)


class Output:
    title: str
    id: int
    sections: dict[str, str] = {}
    categories: list[str] = []
    infoboxes: list[JSON] = []

    def to_dict(self):
        return {
            "title": self.title,
            "id": self.id,
            "sections": self.sections,
            "categories": self.categories,
            "infoboxes": self.infoboxes
        }


def text_cleanup(html: str):
    soup = BeautifulSoup(html, "html.parser")
    for footnote in soup.find_all("sup"):
        footnote.decompose()
    for stub in soup.find_all(attrs={"class": "stub"}):
        stub.decompose()
    text = soup.get_text(strip=True, separator=" ")
    return text

value_elems = ["sup", "br", "li"]

def parse_infobox(json_string: str) -> JSON:
    infobox_data = json.loads(json_string)
    parsed_data = {}

    for item in infobox_data[0]['data']:
        if item['type'] == 'image':
            parsed_data['image'] = item['data'][0]['url']
        elif item['type'] == 'title':
            parsed_data['title'] = item['data']['value']
        elif item['type'] == 'group':
            group_name = item['data']['value'][0]['data']['value']
            parsed_data[group_name] = {}
            for group_item in item['data']['value']:
                if group_item['type'] == 'data':

                    soup_label = BeautifulSoup(group_item['data']['label'], "html.parser")
                    for tag in soup_label.find_all("sup"):
                        tag.decompose()

                    soup_value = BeautifulSoup(group_item['data']['value'], "html.parser")
                    for tag in soup_value.find_all(value_elems):
                        if tag.name == "li":
                            tag.insert_before("\n")
                        if tag.name == "br":
                            tag.insert_before("\n")
                        if tag.name == "sup":
                            tag.decompose()

                    links = []
                    for link in soup_value.find_all("a", href=True):
                        links.append({
                            "href": link['href'],
                            "text": link.get_text(strip=True).strip(trim_contents)
                        })

                    label = (soup_label
                             .get_text(strip=True, separator=", ")
                             .replace("  ", " ")
                             .replace("\\", "")
                             .strip(trim_contents))

                    value = (soup_value
                             .get_text(strip=True, separator=", ")
                             .replace("  ", " ")
                             .replace("\\", "")
                             .strip(trim_contents))

                    parsed_data[group_name][label] = {
                        "value": value,
                        "links": links
                    }
    return parsed_data


def main():
    pages = get_category_members(name="Planets", limit=500)
    for page in pages:

        title = page['title']
        page_properties = get_page_props(title)

        o = Output()
        o.title = title
        o.categories = get_page_categories(title)

        for page_section in page_properties.sections:
            section_html = get_section_content(page['title'], page_section['index'])
            section_text = text_cleanup(section_html)
            o.sections[page_section['line']] = section_text

        for ib in page_properties.infoboxes:
            o.infoboxes.append(ib)

        logging.info(json.dumps(o.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # main()
    print(process_pages_with_infoboxes())
