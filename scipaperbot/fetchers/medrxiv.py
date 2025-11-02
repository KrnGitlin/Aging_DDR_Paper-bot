from datetime import datetime
from typing import List

from .biorxiv import fetch_rxiv
from ..models import Paper


def fetch_medrxiv(start_date: datetime, end_date: datetime, max_results: int = 1000) -> List[Paper]:
    """Thin wrapper for medRxiv using the bioRxiv API server switch."""
    return fetch_rxiv("medrxiv", start_date, end_date, max_results)
