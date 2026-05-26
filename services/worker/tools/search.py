import httpx
import re
from html.parser import HTMLParser
from typing import Dict, Any, List

class DuckDuckGoHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: List[Dict[str, str]] = []
        self.in_snippet = False
        self.current_snippet = ""

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attrs_dict = dict(attrs)
        # DuckDuckGo HTML search results list snippets inside <td class="result-snippet"> or <a class="result__snippet">
        if tag == "td" and attrs_dict.get("class") == "result-snippet":
            self.in_snippet = True
            self.current_snippet = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self.in_snippet:
            self.in_snippet = False
            self.results.append({"snippet": self.current_snippet.strip()})

    def handle_data(self, data: str) -> None:
        if self.in_snippet:
            self.current_snippet += data

class SearchTool:
    name: str = "web_search"
    description: str = "Queries DuckDuckGo to obtain relevant search summaries."

    async def execute(self, query: str) -> Dict[str, Any]:
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, data={"q": query}, headers=headers)
            response.raise_for_status()
            
            parser = DuckDuckGoHTMLParser()
            parser.feed(response.text)
            
            snippets = [r["snippet"] for r in parser.results if r.get("snippet")]
            if not snippets:
                # Regex backup fallback extraction to handle HTML structural updates in DDG response
                snippets = re.findall(r'<td class="result-snippet"[^>]*>(.*?)</td>', response.text, re.DOTALL)
                snippets = [re.sub(r'<[^>]*>', '', s).strip() for s in snippets]

            return {
                "status": "success",
                "results": snippets[:3] if snippets else ["No snippets found in live search output."]
            }
