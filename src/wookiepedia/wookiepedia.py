import json
import logging
import os
import re
import ai
import time
from typing import Union, Dict, Any, List
from urllib.parse import urlencode
from transformers import pipeline, Pipeline
import requests
from bs4 import BeautifulSoup

JSON = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


class PageProperties:
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


class Output:
    title: str
    page_id: int
    sections: dict[str, str]
    categories: set[str]
    infobox: JSON
    completion: JSON | None

    def __init__(self):
        self.title = ""
        self.page_id = 0
        self.sections = {}
        self.categories = set()
        self.infobox = {}
        self.completion = None

    def to_dict(self):
        return {
            "title": self.title,
            "id": self.page_id,
            "sections": self.sections,
            "categories": list(self.categories),
            "infobox": self.infobox,
            "completion": self.completion
        }


url = "https://starwars.fandom.com/api.php"

trim_values: str = "\"',.:-"
trim_contents: str = "\"',."
value_elems = ["sup", "br", "li"]

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


def get_safe_file_name(template: str, page_id: int, title: str) -> str:
    """
    Get a safe file name for the given page id and title
    :param template: the infobox template name
    :param page_id: the page id
    :param title: the title of the page
    :return: a safe file name
    """
    template = re.sub(r'[^\w\s-]', '_', template)
    safe_title = re.sub(r'[^\w\s-]', '_', title)
    safe_title = safe_title.replace(' ', '_')
    return f"{page_id}_{template}_{safe_title}.json"


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

    os.makedirs("output", exist_ok=True)

    while should_continue:
        response = requests.get(url, params=params)
        data = response.json()
        should_continue = data.get("continue", False)

        if should_continue:
            params['pwpcontinue'] = data["continue"]["pwpcontinue"]

        for item in data['query']['pageswithprop']:
            title = str(item['title'])
            page_id = int(item['pageid'])
            page_properties = get_page_props(title)

            o = Output()
            o.title = title
            o.page_id = page_id

            for category in get_page_categories(title):
                o.categories.add(category)

            o.infobox = page_properties.infoboxes[0]

            for page_section in page_properties.sections:
                section_html = get_section_content(title, page_section['index'])
                section_text = cleanup_section_html(section_html)
                # summarizer = pipeline(task="summarization", model="facebook/bart-large-cnn")
                # chunks = tokenize_content(section_text, summarizer.tokenizer)
                # summary = summarize_chunks(chunks, summarizer.tokenizer, summarizer.model)
                # o.sections[page_section['line']] = summary
                o.sections[page_section['line']] = section_text

            write_to_file(o)
            time.sleep(1)


def tokenize_content(content, tokenizer, max_length=1024):
    tokens = tokenizer(content,
                       return_tensors="pt",
                       truncation=True,
                       padding='longest',
                       max_length=max_length)
    input_ids = tokens.input_ids[0]
    chunks = [input_ids[i:i + max_length] for i in range(0, len(input_ids), max_length)]
    return chunks


def summarize_chunks(chunks, tokenizer, model):
    summaries = []
    for chunk in chunks:
        inputs = {"input_ids": chunk.unsqueeze(0)}
        summary_ids = model.generate(
            **inputs,
            max_length=100,
            min_length=20,
            length_penalty=1.5,
            num_beams=2,
            early_stopping=True)
        summaries.append(tokenizer.decode(summary_ids[0], skip_special_tokens=True))
    return ' '.join(summaries)


def write_to_file(o: Output):
    template_name = o.infobox['template']
    file_name = get_safe_file_name(template_name, o.page_id, o.title)
    file_path = os.path.join("output", template_name, file_name)

    directory = os.path.dirname(file_path)
    os.makedirs(directory, exist_ok=True)

    with open(file_path, 'w') as file:
        json.dump(o.to_dict(), file, indent=4)


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


def cleanup_section_html(html: str):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(strip=True, separator=" ")
    return " ".join(text.split())


def parse_infobox(json_string: str) -> JSON:

    infobox_data = json.loads(json_string)

    parsed_data = {
        "template": None,
        "infobox": {},
    }

    for item in infobox_data[0]['data']:
        if item['type'] == 'image':
            parsed_data['infobox']['image'] = item['data'][0]['url']
        elif item['type'] == 'navigation':
            navigation = BeautifulSoup(item['data']['value'], "html.parser")
            anchor = navigation.find("a")
            parsed_data['template'] = anchor['href'].split(":")[-1]
        elif item['type'] == 'title':
            parsed_data['infobox']['title'] = item['data']['value']
        elif item['type'] == 'group':
            group_name = item['data']['value'][0]['data']['value']
            parsed_data['infobox'][group_name] = {}

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

                    parsed_data['infobox'][group_name][label] = {
                        "value": value,
                        "links": links
                    }
    return parsed_data
