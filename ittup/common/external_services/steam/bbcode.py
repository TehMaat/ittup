# -*- coding: utf-8 -*-
import re
from html.parser import HTMLParser

# The label Steam puts before the requirements ('<strong>Minimi:</strong><br>'): the description has its own
REQUIREMENTS_LABEL = re.compile(r"^\s*<strong>[^<]*:\s*</strong>\s*(<br\s*/?>\s*)?", re.IGNORECASE)


class BBCodeParser(HTMLParser):
    """
    The simple HTML of Steam in BBCode: <strong> → [b], <ul>/<li> → [list]/[*], <br> → new line.
    The other tags are removed, the HTML entities decoded
    """

    START = {"strong": "[b]", "ul": "\n[list]\n", "li": "[*]", "br": "\n"}
    END = {"strong": "[/b]", "ul": "[/list]\n", "li": "\n"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        self.parts.append(self.START.get(tag, ""))

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        self.parts.append(self.START.get(tag, ""))

    def handle_endtag(self, tag: str) -> None:
        self.parts.append(self.END.get(tag, ""))

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def bbcode(self) -> str:
        # One item for each line, without the empty lines left by the tags
        lines = (line.strip() for line in "".join(self.parts).splitlines())
        return "\n".join(line for line in lines if line)


def html_to_bbcode(html_text: str) -> str:
    parser = BBCodeParser()
    parser.feed(html_text or "")
    parser.close()
    return parser.bbcode()


def requirements_to_bbcode(html_text: str) -> str:
    """ The requirements of Steam in BBCode, without Steam's own label ('Minimi:', 'Consigliati:') """
    return html_to_bbcode(REQUIREMENTS_LABEL.sub("", html_text or ""))
