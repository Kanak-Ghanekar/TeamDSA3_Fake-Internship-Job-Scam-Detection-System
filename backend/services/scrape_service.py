"""
Scrape Service — fetches a job-posting URL server-side and extracts structured
fields (title, company, location, salary, description) from the raw HTML.

Works generically across platforms (LinkedIn, Naukri, Indeed, company career
pages, etc.) using a layered strategy:
  1. JSON-LD structured data (schema.org/JobPosting) — most reliable when present.
  2. OpenGraph / meta tags — common fallback used by most job boards.
  3. Visible-text heuristics (largest heading = title, body text = description).

No platform-specific scraping logic or API keys are required. If a site blocks
scraping or the page can't be parsed, the service returns whatever partial
data it could extract plus a flag so the frontend can ask the user to fill
the rest manually.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

REQUEST_TIMEOUT = 8  # seconds
MAX_HTML_BYTES = 3_000_000


class ScrapeError(Exception):
    """Raised when a URL cannot be fetched or parsed at all."""


def _clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_domain(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:
        return ""


def _find_jobposting_jsonld(soup: BeautifulSoup) -> Optional[dict]:
    """Look for schema.org JobPosting structured data, the gold-standard source."""
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string or tag.get_text() or ""
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue

        candidates = data if isinstance(data, list) else [data]
        # Some sites nest the real objects under "@graph"
        flat: list = []
        for c in candidates:
            if isinstance(c, dict) and "@graph" in c and isinstance(c["@graph"], list):
                flat.extend(c["@graph"])
            else:
                flat.append(c)

        for obj in flat:
            if not isinstance(obj, dict):
                continue
            obj_type = obj.get("@type", "")
            types = obj_type if isinstance(obj_type, list) else [obj_type]
            if any(str(t).lower() == "jobposting" for t in types):
                return obj
    return None


def _parse_jsonld_jobposting(obj: dict) -> dict:
    title = _clean_text(obj.get("title"))

    company = ""
    org = obj.get("hiringOrganization")
    if isinstance(org, dict):
        company = _clean_text(org.get("name"))
    elif isinstance(org, str):
        company = _clean_text(org)

    location = ""
    loc = obj.get("jobLocation")
    if isinstance(loc, list) and loc:
        loc = loc[0]
    if isinstance(loc, dict):
        addr = loc.get("address")
        if isinstance(addr, dict):
            parts = [
                addr.get("addressLocality"),
                addr.get("addressRegion"),
                addr.get("addressCountry"),
            ]
            location = _clean_text(", ".join(p for p in parts if p))
        elif isinstance(addr, str):
            location = _clean_text(addr)
    if not location and obj.get("jobLocationType"):
        location = _clean_text(str(obj.get("jobLocationType")))

    salary = ""
    base = obj.get("baseSalary")
    if isinstance(base, dict):
        val = base.get("value")
        if isinstance(val, dict):
            min_v, max_v = val.get("minValue"), val.get("maxValue")
            unit = val.get("unitText", "")
            if min_v and max_v:
                salary = f"{min_v}-{max_v} {unit}".strip()
            elif val.get("value"):
                salary = f"{val.get('value')} {unit}".strip()
        elif val:
            salary = _clean_text(str(val))

    description_html = obj.get("description") or ""
    description = _clean_text(BeautifulSoup(description_html, "html.parser").get_text(" "))

    return {
        "title": title,
        "company": company,
        "location": location,
        "salary": salary,
        "description": description,
    }


def _meta_content(soup: BeautifulSoup, *names: str) -> str:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find(
            "meta", attrs={"name": name}
        )
        if tag and tag.get("content"):
            return _clean_text(tag["content"])
    return ""


def _fallback_extract(soup: BeautifulSoup) -> dict:
    title = _meta_content(soup, "og:title", "twitter:title")
    if not title and soup.title:
        title = _clean_text(soup.title.get_text())
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = _clean_text(h1.get_text())

    description = _meta_content(soup, "og:description", "twitter:description", "description")

    # If meta description is short/missing, pull the largest visible text block
    if len(description) < 120:
        for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
            tag.decompose()
        candidates = soup.find_all(["article", "main", "section", "div"])
        best = ""
        for c in candidates:
            text = _clean_text(c.get_text(" "))
            if len(text) > len(best) and len(text) < 20000:
                best = text
        if len(best) > len(description):
            description = best[:6000]

    company = _meta_content(soup, "og:site_name")

    return {
        "title": title,
        "company": company,
        "location": "",
        "salary": "",
        "description": description,
    }


def scrape_job_url(url: str) -> dict[str, Any]:
    """
    Fetches the given URL and extracts job-posting fields.
    Returns a dict with keys: title, company, location, salary, description,
    domain, source_url, extraction_method, partial (bool).
    Raises ScrapeError if the page could not be fetched at all.
    """
    if not url or not url.strip():
        raise ScrapeError("No URL provided.")

    url = url.strip()
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url

    domain = _extract_domain(url)

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
            stream=True,
        )
        resp.raise_for_status()
        content = resp.raw.read(MAX_HTML_BYTES, decode_content=True)
        html = content.decode(resp.encoding or "utf-8", errors="ignore")
    except requests.exceptions.RequestException as e:
        logger.warning("Failed to fetch job URL %s: %s", url, e)
        raise ScrapeError(
            f"Could not reach that URL ({type(e).__name__}). "
            "The site may block automated requests, or the link may be incorrect."
        ) from e

    soup = BeautifulSoup(html, "html.parser")

    jsonld = _find_jobposting_jsonld(soup)
    if jsonld:
        fields = _parse_jsonld_jobposting(jsonld)
        method = "jsonld"
    else:
        fields = _fallback_extract(soup)
        method = "heuristic"

    fields["domain"] = domain
    fields["source_url"] = url
    fields["extraction_method"] = method
    fields["partial"] = not (fields.get("title") and fields.get("description"))

    return fields
