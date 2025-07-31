"""Crypto screener module.

This module provides helper functions to retrieve trending Google search
queries and newly listed cryptocurrency coins, then attempts to match the two
using simple fuzzy string matching.

The external APIs used in this module require internet access. In offline
environments the functions will fail unless data is supplied manually.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Iterable

import requests
from fuzzywuzzy import fuzz
from pytrends.request import TrendReq

log = logging.getLogger(__name__)


def fetch_trending_searches(region: str = "united_states", top: int = 20) -> List[str]:
    """Fetch recent trending Google searches.

    Args:
        region: Region code passed to :class:`pytrends.request.TrendReq`.
        top: Number of trending terms to return.

    Returns:
        A list of trending search query strings.
    """

    pytrends = TrendReq()
    try:
        df = pytrends.trending_searches(pn=region)
    except Exception as exc:  # pragma: no cover - network call
        log.error("Failed to fetch trending searches: %s", exc)
        raise

    terms = df[0].tolist()
    return terms[:top]


def fetch_new_coins(limit: int = 100) -> List[Dict[str, str]]:
    """Retrieve newly listed cryptocurrency coins from Coinpaprika.

    Args:
        limit: Maximum number of coins to return.

    Returns:
        List of coin objects containing at least ``name`` and ``symbol``.
    """

    url = "https://api.coinpaprika.com/v1/coins"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as exc:  # pragma: no cover - network call
        log.error("Failed to fetch new coin data: %s", exc)
        raise

    coins = [coin for coin in resp.json() if coin.get("is_new")]
    return coins[:limit]


def match_trends_to_coins(
    trends: Iterable[str], coins: Iterable[Dict[str, str]], threshold: int = 60
) -> List[Dict[str, str]]:
    """Match trending search terms to coins using fuzzy matching.

    Args:
        trends: Iterable of trending search strings.
        coins: Iterable of coin dictionaries.
        threshold: Minimum fuzzy match score required to consider a match.

    Returns:
        List of match dictionaries containing ``trend``, ``coin`` and ``score``.
    """

    results = []
    for term in trends:
        for coin in coins:
            name = coin.get("name", "")
            symbol = coin.get("symbol", "")
            score_name = fuzz.partial_ratio(term.lower(), name.lower())
            score_symbol = fuzz.partial_ratio(term.lower(), symbol.lower())
            score = max(score_name, score_symbol)
            if score >= threshold:
                results.append({"trend": term, "coin": coin, "score": score})
    return results


if __name__ == "__main__":  # pragma: no cover - manual execution
    logging.basicConfig(level=logging.INFO)
    trends = fetch_trending_searches()
    coins = fetch_new_coins()
    matches = match_trends_to_coins(trends, coins)
    for match in matches:
        coin = match["coin"]
        print(
            f"{match['trend']}: {coin['name']} ({coin['symbol']}) - score {match['score']}"
        )
