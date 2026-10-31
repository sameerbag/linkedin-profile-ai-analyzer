import re
import html
from typing import Optional


def clean_html_text(raw_text: Optional[str]) -> str:
    """
    Cleans raw HTML descriptions from job portals (Indeed, LinkedIn, Glassdoor, etc.)
    into clean, readable Markdown/text.
    
    - Decodes HTML entities (&amp;, &nbsp;, &quot;, &#39;, etc.)
    - Converts tags (<p>, <strong>, <ul>, <li>, <br>) into formatted Markdown
    - Removes residual scripts, styles, and unparsed tags
    - Normalizes spacing and redundant newlines
    """
    if not raw_text or not isinstance(raw_text, str) or raw_text.strip().lower() == "nan":
        return ""

    text = raw_text.strip()

    # Quick check: does it have HTML tags or entities?
    has_html = bool(re.search(r"<[a-zA-Z\/][^>]*>", text)) or ("&" in text and ";" in text)
    if not has_html:
        return text

    # Step 1: Decode HTML entities first (&amp; -> &, &nbsp; -> space, etc.)
    text = html.unescape(text)

    # Step 2: Try converting with markdownify for clean bullet points & bolding
    try:
        import markdownify
        # Remove script and style elements before converting
        cleaned = re.sub(r"<(script|style)[^>]*>[\s\S]*?<\/\1>", "", text, flags=re.IGNORECASE)
        converted = markdownify.markdownify(cleaned, heading_style="ATX", bullets="-")
        if converted and len(converted.strip()) > 10:
            text = converted
    except Exception:
        # Fallback to BeautifulSoup if markdownify encounters an issue
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text(separator="\n")
        except Exception:
            # Regex fallback
            text = re.sub(r"<br\s*\/?>", "\n", text, flags=re.IGNORECASE)
            text = re.sub(r"<\/p>", "\n\n", text, flags=re.IGNORECASE)
            text = re.sub(r"<li>", "• ", text, flags=re.IGNORECASE)
            text = re.sub(r"<\/li>", "\n", text, flags=re.IGNORECASE)
            text = re.sub(r"<[^>]+>", "", text)

    # Step 3: Clean up non-breaking spaces and leftover entity artifacts
    text = text.replace("\xa0", " ").replace("&nbsp;", " ")
    
    # Step 4: Remove any leftover lone HTML tags that might have slipped through
    text = re.sub(r"<\/?(div|span|section|article|font|center)[^>]*>", "", text, flags=re.IGNORECASE)

    # Step 5: Normalize excessive empty newlines (collapse 3+ into 2)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    return text.strip()


def clean_text_field(raw_field: Optional[str]) -> str:
    """Cleans title, company, or location fields of HTML entities like &amp;"""
    if not raw_field or not isinstance(raw_field, str):
        return ""
    cleaned = html.unescape(raw_field).replace("\xa0", " ").strip()
    # Strip any stray tags
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    return cleaned.strip()
