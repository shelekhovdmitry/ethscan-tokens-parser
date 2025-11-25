#!/usr/bin/env python3
import argparse
import json
import os
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_URL = "https://etherscan.io/tokens"

PRICE_PATTERN = re.compile(
    r"\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)"
)


@dataclass
class TokenInfo:
    name: str
    price_usd: float
    url: Optional[str]


def parse_price(text: str) -> Optional[float]:
    if not text:
        return None

    for match in PRICE_PATTERN.finditer(text):
        start = match.start()
        end = match.end()
        fragment = text[max(0, start - 4): end + 1]

        if "$" not in fragment:
            continue

        number_str = match.group(1).replace(",", "")
        try:
            return float(number_str)
        except ValueError:
            continue

    return None


def guess_base_url(source_hint: Optional[str], soup: BeautifulSoup) -> str:
    candidates = []

    if source_hint:
        candidates.append(source_hint)

    base_tag = soup.find("base", href=True)
    if base_tag:
        candidates.append(base_tag["href"])

    canon = soup.find("link", rel=lambda v: v and "canonical" in v.lower(), href=True)
    if canon:
        candidates.append(canon["href"])

    candidates.append(DEFAULT_URL)

    for cand in candidates:
        try:
            parsed = urlparse(cand)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            continue

    return DEFAULT_URL


def _store_token(
    storage: Dict,
    name: str,
    price: Optional[float],
    href: Optional[str],
    base_url: str,
) -> None:
    if price is None:
        return

    full_url = urljoin(base_url.rstrip("/") + "/", href) if href else None
    key = (name, full_url)

    if key in storage:
        return

    storage[key] = TokenInfo(name=name, price_usd=float(price), url=full_url)


def extract_tokens(html: str, source_hint: Optional[str]) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    base_url = guess_base_url(source_hint, soup)

    collected: Dict = {}

    token_links = soup.select(
        'a[href*="/token/"], a[href*="/tokens/"], a[href*="/tokenholdings"]'
    )

    for a in token_links:
        href = (a.get("href") or "").strip()
        if not href:
            continue

        row = a.find_parent("tr")
        if row is None:
            row = a.find_parent(
                lambda tag: tag
                and tag.name in {"tr", "div", "li"}
                and (tag.get("role") == "row" or tag.name in {"tr", "div", "li"})
            )

        pieces = []
        if row is not None:
            pieces.append(row.get_text(" ", strip=True))
        text_from_link = a.get_text(" ", strip=True)
        if text_from_link:
            pieces.append(text_from_link)

        context = " | ".join(pieces)
        price = parse_price(context)

        symbol = None
        candidate_attrs = ["data-symbol", "data-coin-symbol", "data-symbol-short"]
        for attr in candidate_attrs:
            symbol = row.get(attr) if row is not None else None
            if not symbol:
                symbol = a.get(attr)
            if symbol:
                symbol = symbol.strip()
                break

        name = symbol or text_from_link or "UNKNOWN"
        _store_token(collected, name, price, href, base_url)

    if not collected:
        for row in soup.select("tr"):
            row_text = row.get_text(" ", strip=True)
            price = parse_price(row_text)
            if price is None:
                continue

            anchor = row.find("a", href=True)
            if not anchor:
                continue

            href = anchor["href"]
            label = (
                anchor.get("data-symbol")
                or anchor.get("data-coin-symbol")
                or anchor.get_text(" ", strip=True)
                or "UNKNOWN"
            )
            _store_token(collected, label, price, href, base_url)

    result = [asdict(t) for t in collected.values()]
    result.sort(key=lambda x: x["price_usd"], reverse=True)
    return result


def load_source(source: Optional[str]) -> str:
    target = source or DEFAULT_URL

    try:
        parsed = urlparse(target)
        if parsed.scheme in {"http", "https"}:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            resp = requests.get(target, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.text
    except Exception:
        pass

    if os.path.isfile(target):
        with open(target, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    raise SystemExit(
        f"Не удалось получить HTML-источник: {target}\n"
        f"Укажите существующий URL или путь к локальному .html файлу."
    )


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Парсит страницу Etherscan с токенами и сохраняет JSON."
    )
    parser.add_argument(
        "-s",
        "--source",
        help="URL или путь к локальному .html (по умолчанию: https://etherscan.io/tokens)",
        default=None,
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=1000,
        help="Максимальное количество записей в выводе (по умолчанию 1000)",
    )
    parser.add_argument(
        "-o",
        "--out",
        default="tokens.json",
        help="Имя/путь JSON-файла для результата",
    )
    return parser.parse_args()


def main() -> None:
    args = cli()

    html = load_source(args.source)
    tokens = extract_tokens(html, args.source)

    if args.limit and args.limit > 0:
        tokens = tokens[: args.limit]

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)

    print(f"Сохранено {len(tokens)} записей в {args.out}")
    if tokens:
        print("Первые примеры:")
        for item in tokens[:3]:
            print(f"- {item['name']} | ${item['price_usd']} | {item['url']}")


if __name__ == "__main__":
    main()
