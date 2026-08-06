from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.config import Settings


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thanh list PaperRecord."""
    import re
    from core.utils import safe_slug, normalize_whitespace
    
    records = []
    items = payload.get("message", {}).get("items", [])
    for item in items:
        doi = item.get("DOI")
        if not doi:
            continue
            
        # paper_id dung safe_slug cua DOI
        paper_id = safe_slug(doi)
        
        # Title
        titles = item.get("title", [])
        if not titles:
            continue
        title = normalize_whitespace(titles[0])
        
        # Summary (abstract)
        abstract = item.get("abstract", "")
        if not abstract:
            continue
        # Clean XML/HTML tags from abstract (e.g. <jats:p>, </jats:p>)
        abstract_clean = re.sub(r"<[^>]+>", "", abstract)
        summary = normalize_whitespace(abstract_clean)
        if not summary:
            continue
            
        # Authors
        authors_list = item.get("author", [])
        authors = []
        for a in authors_list:
            given = a.get("given", "").strip()
            family = a.get("family", "").strip()
            name = f"{given} {family}".strip()
            if name:
                authors.append(name)
                
        # Categories (subject)
        categories = item.get("subject", [])
        primary_category = categories[0] if categories else "unknown"
        
        # Parse published date
        # published format ISO YYYY-MM-DD
        # Check published, issued, created
        pub_dict = item.get("published") or item.get("issued") or item.get("created")
        pub_date_str = "1970-01-01"
        if pub_dict and "date-parts" in pub_dict:
            date_parts = pub_dict["date-parts"]
            if date_parts and len(date_parts[0]) > 0:
                parts = date_parts[0]
                year = parts[0]
                month = parts[1] if len(parts) > 1 else 1
                day = parts[2] if len(parts) > 2 else 1
                try:
                    pub_date_str = f"{year:04d}-{month:02d}-{day:02d}"
                except Exception:
                    pub_date_str = "1970-01-01"
        
        # Updated date (default to published)
        updated_dict = item.get("created")
        updated_date_str = pub_date_str
        if updated_dict and "date-parts" in updated_dict:
            date_parts = updated_dict["date-parts"]
            if date_parts and len(date_parts[0]) > 0:
                parts = date_parts[0]
                year = parts[0]
                month = parts[1] if len(parts) > 1 else 1
                day = parts[2] if len(parts) > 2 else 1
                try:
                    updated_date_str = f"{year:04d}-{month:02d}-{day:02d}"
                except Exception:
                    updated_date_str = pub_date_str
                    
        # URL (abs_url)
        abs_url = item.get("URL", f"https://doi.org/{doi}")
        
        # pdf_url
        pdf_url = ""
        links = item.get("link", [])
        for link in links:
            url_val = link.get("URL", "")
            content_type = link.get("content-type", "")
            if "pdf" in content_type.lower() or "pdf" in url_val.lower():
                pdf_url = url_val
                break
        if not pdf_url and links:
            pdf_url = links[0].get("URL", "")
            
        # Comment (taking publisher or subtype)
        comment = item.get("subtype", "") or item.get("publisher", "")
        
        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=pub_date_str,
                updated=updated_date_str,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Goi source API, luu raw response, parse thanh records."""
    import requests
    import time
    from core.utils import write_json
    
    url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results
    }
    headers = {
        "User-Agent": "antigravity-agent/1.0 (mailto:agent@example.com)"
    }
    
    response_data = {}
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                response_data = response.json()
                break
            elif response.status_code in (429, 503):
                time.sleep(2 * (attempt + 1))
            else:
                response.raise_for_status()
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed to fetch Crossref data after {max_retries} attempts: {e}")
            time.sleep(2 * (attempt + 1))
            
    # Luu raw response
    write_json(settings.paths.raw_api_response, response_data)
    
    # Parse records
    records = parse_crossref_payload(response_data)
    
    # Luu raw records json
    records_dict = [
        {
            "paper_id": r.paper_id,
            "title": r.title,
            "summary": r.summary,
            "authors": r.authors,
            "categories": r.categories,
            "primary_category": r.primary_category,
            "published": r.published,
            "updated": r.updated,
            "abs_url": r.abs_url,
            "pdf_url": r.pdf_url,
            "comment": r.comment
        }
        for r in records
    ]
    write_json(settings.paths.raw_records_json, records_dict)
    
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot va map thanh `PaperRecord`."""
    from core.utils import read_json
    
    raw_data = read_json(path)
    records = []
    for item in raw_data:
        records.append(
            PaperRecord(
                paper_id=item["paper_id"],
                title=item["title"],
                summary=item["summary"],
                authors=item["authors"],
                categories=item["categories"],
                primary_category=item["primary_category"],
                published=item["published"],
                updated=item["updated"],
                abs_url=item["abs_url"],
                pdf_url=item["pdf_url"],
                comment=item["comment"],
            )
        )
    return records
