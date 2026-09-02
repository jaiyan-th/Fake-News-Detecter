"""
Source Credibility and Reputation Metadata Service
Provides descriptive metadata, domain classification, and tier markers for news organizations.
NOTE: Credibility tier is contextual metadata used to assist verification, NOT an automated true/false override.
"""

from typing import Dict, Any
from urllib.parse import urlparse


class SourceCredibilityService:
    # Established international news organizations and wire services
    WIRE_AND_PRIMARY = {
        "reuters.com", "apnews.com", "afp.com", "bloomberg.com", "pti.in", "aninews.in"
    }

    ESTABLISHED_MAINSTREAM = {
        "bbc.com", "bbc.co.uk", "theguardian.com", "nytimes.com", "washingtonpost.com",
        "wsj.com", "ft.com", "economist.com", "aljazeera.com", "npr.org", "pbs.org",
        "thehindu.com", "indianexpress.com", "ndtv.com", "hindustantimes.com", "timesofindia.indiatimes.com",
        "indiatoday.in", "economictimes.indiatimes.com", "newindianexpress.com", "outlookindia.com",
        "deccanherald.com", "livemint.com", "theprint.in", "scroll.in", "thequint.com", "moneycontrol.com",
        "financialexpress.com", "business-standard.com", "telegraphindia.com", "tribuneindia.com",
        "firstpost.com", "dw.com", "france24.com", "abcnews.go.com", "cbsnews.com", "nbcnews.com",
        "cricbuzz.com", "espncricinfo.com", "icc-cricket.com"
    }

    GOVERNMENT_AND_ACADEMIC = {
        "gov", "gov.in", "gov.uk", "europa.eu", "un.org", "who.int", "edu", "ac.uk"
    }

    def get_source_metadata(self, source_name: str, url: str) -> Dict[str, Any]:
        """
        Derive metadata and credibility tier for a given source name and URL.
        """
        domain = urlparse(url).netloc.lower().replace("www.", "") if url else ""
        source_lower = source_name.lower().strip() if source_name else ""

        # Check government / institutional
        if any(domain.endswith(f".{suffix}") or domain == suffix for suffix in self.GOVERNMENT_AND_ACADEMIC):
            return {
                "domain": domain,
                "tier": "INSTITUTIONAL_OFFICIAL",
                "label": "Official / Government / Academic Source",
                "weight_hint": 1.0
            }

        # Check wire services
        if domain in self.WIRE_AND_PRIMARY or any(w in source_lower for w in ["reuters", "associated press", "ap news", "pti", "ani"]):
            return {
                "domain": domain,
                "tier": "WIRE_AND_PRIMARY_AGENCY",
                "label": "Primary Wire / News Agency",
                "weight_hint": 0.95
            }

        # Check established mainstream
        mainstream_keywords = [
            "bbc", "guardian", "hindu", "indian express", "new york times", "ndtv",
            "times of india", "hindustan times", "india today", "economic times",
            "outlook", "deccan herald", "tribune", "livemint", "moneycontrol",
            "firstpost", "cricbuzz", "icc", "al jazeera", "reuters", "associated press"
        ]
        if domain in self.ESTABLISHED_MAINSTREAM or any(m in source_lower for m in mainstream_keywords):
            return {
                "domain": domain,
                "tier": "ESTABLISHED_NEWS_ORGANIZATION",
                "label": "Established News Organization",
                "weight_hint": 0.90
            }

        return {
            "domain": domain,
            "tier": "GENERAL_WEB_SOURCE",
            "label": "General Online Media / Web Publication",
            "weight_hint": 0.60
        }
