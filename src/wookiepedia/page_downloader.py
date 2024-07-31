import concurrent.futures
import json
import logging
import os
import re
import requests
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from wookiepedia import Output, PageProperties
from wookiepedia.types import JSON


class PageDownloader:
    """
    A class to download and process pages from the Star Wars Wookiepedia API
    """

    url: str = "https://starwars.fandom.com/api.php"
    trim: str = "\"',.:-"
    value_elems = ["sup", "br", "li"]
    output_dir = "output/raw"

    """
    Sections to ignore when requesting 'sections' from the API
    """
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

    def __init__(self, output_dir: str = "output/raw"):
        self.output_dir = output_dir

    @staticmethod
    def get_safe_file_name(template: str, page_id: int, title: str) -> str:
        safe_template = re.sub(r'[^\w\s-]', '_', template)
        safe_title = re.sub(r'[^\w\s-]', '_', title).replace(' ', '_')
        return f"{page_id}_{safe_template}_{safe_title}.json"

    def process_page(self, page: JSON):
        title = str(page['title'])
        page_id = int(page['pageid'])

        # Load additional data
        page_properties = self.get_page_props(title=title)
        page_categories = self.get_page_categories(title=title)
        page_sections: dict[str, str] = {}

        for page_section in page_properties.sections:
            html_content = self.get_section_content(
                page_title=title,
                section_index=page_section['index'])
            content = self.cleanup_section_html(html=html_content)
            page_sections[page_section['line']] = content

        page_infobox = page_properties.infoboxes[0] if len(page_properties.infoboxes) == 1 else None

        # Create output object
        output = Output(
            title=title,
            page_id=page_id,
            categories=page_categories,
            infobox=page_infobox,
            sections=page_sections)

        self.write_to_file(output)

    def download_pages_with_infoboxes(self):
        should_continue = True
        params = {
            "action": "query",
            "list": "pageswithprop",
            "pwppropname": "infoboxes",
            "pwplimit": "max",
            "pwpcontinue": 1,
            "format": "json"
        }
        full_url = f"{self.url}?{urlencode(params)}"
        logging.info(f"Making request to {full_url}")

        os.makedirs("output", exist_ok=True)

        while should_continue:
            response = requests.get(self.url, params=params)
            data = response.json()
            should_continue = data.get("continue", False)

            if should_continue:
                params['pwpcontinue'] = data["continue"]["pwpcontinue"]

            pages = data['query']['pageswithprop']
            pages = filter(lambda page: page['ns'] == 0, pages)

            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(self.process_page, pages)

    def write_to_file(self, output: Output):

        template_name = output.infobox['template']

        file_name = self.get_safe_file_name(
            template=template_name,
            page_id=output.page_id,
            title=output.title)

        file_path = os.path.join("output", "raw", template_name, file_name)

        directory = os.path.dirname(file_path)
        os.makedirs(name=directory, exist_ok=True)

        with open(file_path, 'w') as file:
            json.dump(output.to_dict(), file, indent=4)

    def get_category_members(self, name: str = "Planets", limit: int = 10):
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": "Category:" + name,
            "cmlimit": limit,
            "format": "json"
        }

        full_url = f"{self.url}?{urlencode(params)}"
        logging.info(f"Making request to {full_url}")

        response = requests.get(self.url, params=params)
        data = response.json()
        return data['query']['categorymembers']

    def get_page_props(self, title: str) -> PageProperties:
        params = {
            "action": "parse",
            "page": title,
            "format": "json",
            "prop": "sections|properties"
        }
        full_url = f"{self.url}?{urlencode(params)}"
        logging.info(f"Making request to {full_url}")
        response = requests.get(self.url, params=params)
        data = response.json()
        sections = data['parse']['sections']
        sections = filter(lambda section: section['index'] != "", sections)
        sections = filter(lambda section: section['line'] not in self.ignore_sections, sections)
        infoboxes = []

        for prop in data['parse']['properties']:
            name = prop['name']
            value = prop['*']
            if name == 'infoboxes' and value is not None:
                infoboxes.append(self.parse_infobox(value))

        return PageProperties(
            title=title,
            sections=sections,
            infoboxes=infoboxes
        )

    def get_section_content(self,
                            page_title: str,
                            section_index: str | int) -> str:
        params = {
            "action": "parse",
            "page": page_title,
            "prop": "text",
            "section": section_index,
            "format": "json"
        }
        full_url = f"{self.url}?{urlencode(params)}"
        logging.info(f"Making request to {full_url}")
        response = requests.get(self.url, params=params)
        data = response.json()
        return data["parse"]["text"]["*"]

    template_ns = 10

    def get_infobox_templates(self):
        params = {
            "action": "query",
            "list": "allpages",
            "apprefix": "Infobox",
            "apnamespace": self.template_ns,
            "aplimit": "max",
            "format": "json"
        }
        full_url = f"{self.url}?{urlencode(params)}"
        logging.info(f"Making request to {full_url}")
        response = requests.get(self.url, params=params)
        data = response.json()
        templates = [page['title'] for page in data['query']['allpages']]
        return templates

    def get_page_categories(self, title: str) -> list[str]:
        params = {
            "action": "parse",
            "page": title,
            "format": "json",
            "prop": "categories"
        }
        full_url = f"{self.url}?{urlencode(params)}"
        logging.info(f"Making request to {full_url}")
        response = requests.get(self.url, params=params)
        data = response.json()
        categories = [cat["*"] for cat in data["parse"]["categories"]]
        return categories

    def cleanup_section_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(strip=True, separator=" ")
        text = re.sub(r'\[\\]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def parse_infobox(self, json_string: str) -> JSON:
        infobox_data = json.loads(json_string)

        parsed_data = {
            "template": None,
            "infobox": {}
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
                group_name_html = BeautifulSoup(item['data']['value'][0]['data']['value'], "html.parser")
                group_name = group_name_html.get_text(strip=True, separator=", ").strip(self.trim)
                parsed_data['infobox'][group_name] = {}

                for group_item in item['data']['value']:
                    if group_item['type'] == 'data':
                        soup_label = BeautifulSoup(group_item['data']['label'], "html.parser")
                        for tag in soup_label.find_all("sup"):
                            tag.decompose()

                        soup_value = BeautifulSoup(group_item['data']['value'], "html.parser")
                        for tag in soup_value.find_all(self.value_elems):
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
                                "text": link.get_text(strip=True).strip(self.trim)
                            })

                        label = (soup_label
                                 .get_text(strip=True, separator=", ")
                                 .replace("  ", " ")
                                 .replace("\\", "")
                                 .strip(self.trim))

                        value = (soup_value
                                 .get_text(strip=True, separator=", ")
                                 .replace("  ", " ")
                                 .replace("\\", "")
                                 .strip(self.trim))

                        parsed_data['infobox'][group_name][label] = {
                            "value": value,
                            "links": links
                        }
        return parsed_data
