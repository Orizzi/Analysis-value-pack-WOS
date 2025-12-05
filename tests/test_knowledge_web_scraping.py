from pathlib import Path

import requests

from wos_pack_value.knowledge.web_scraping import scrape_wosnerds


class DummyResp:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None


def test_scrape_wosnerds_uses_local_html(monkeypatch):
    html = """
    <html><body>
    <table>
      <tr><th>Name</th><th>Power</th></tr>
      <tr><td>Hero C</td><td>9000</td></tr>
    </table>
    </body></html>
    """

    def fake_get(url, timeout=10):
        return DummyResp(html)

    monkeypatch.setattr(requests, "get", fake_get)
    entities = scrape_wosnerds("whiteout_survival", "http://example.com", paths=["/heroes"])
    assert len(entities) == 1
    assert entities[0].name == "Hero C"
