import json
import os
import re
from typing import Any, Dict, List
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup


DEFAULT_SAMPLE_URL = "https://books.toscrape.com/"


def normalize_url(url: str) -> str:
    cleaned = url.strip()
    if not cleaned:
        raise ValueError("Please enter a valid URL.")
    if "://" not in cleaned:
        cleaned = f"https://{cleaned}"
    return cleaned


def parse_price(raw_price: Any) -> float:
    if raw_price is None:
        return 0.0
    if isinstance(raw_price, (int, float)):
        return round(float(raw_price), 2)
    text = str(raw_price)
    digits = re.sub(r"[^\d.]", "", text)
    if not digits:
        return 0.0
    return round(float(digits), 2)


def parse_rating(raw_rating: Any) -> str:
    if not raw_rating:
        return "N/A"
    text = str(raw_rating).strip().lower()
    if not text:
        return "N/A"
    rating_map = {
        "one": "1★",
        "two": "2★",
        "three": "3★",
        "four": "4★",
        "five": "5★",
        "1": "1★",
        "2": "2★",
        "3": "3★",
        "4": "4★",
        "5": "5★",
    }
    return rating_map.get(text, text)


def build_image_url(image_url: str, base_url: str) -> str:
    if not image_url:
        return ""
    if image_url.startswith("http"):
        return image_url
    if image_url.startswith("//"):
        return f"https:{image_url}"
    return f"{base_url.rstrip('/')}/{image_url.lstrip('/')}"


def sample_products() -> List[Dict[str, object]]:
    return [
        {
            "name": "The Midnight Library",
            "price": "£12.00",
            "price_value": 12.0,
            "rating": "4★",
            "image": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=300&q=80",
            "category": "Fiction",
        },
        {
            "name": "Atomic Habits",
            "price": "£14.99",
            "price_value": 14.99,
            "rating": "5★",
            "image": "https://images.unsplash.com/photo-1495446815901-a7297e633e8d?auto=format&fit=crop&w=300&q=80",
            "category": "Self-Help",
        },
        {
            "name": "Sapiens",
            "price": "£16.50",
            "price_value": 16.5,
            "rating": "4★",
            "image": "https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=300&q=80",
            "category": "History",
        },
    ]


def _extract_text(node: Any) -> str:
    if not node:
        return ""
    text = node.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text)


def _extract_image(tag: Any, base_url: str) -> str:
    if not tag:
        return ""
    image_url = tag.get("src") or tag.get("data-src") or tag.get("data-original") or tag.get("srcset") or ""
    if isinstance(image_url, list):
        image_url = image_url[0] if image_url else ""
    if isinstance(image_url, str):
        if image_url.startswith("data:"):
            return ""
        if "," in image_url:
            image_url = image_url.split(",")[0]
        return build_image_url(image_url, base_url)
    return ""


def _extract_rating(node: Any) -> str:
    if not node:
        return "N/A"
    classes = [cls for cls in node.get("class", []) if isinstance(cls, str)]
    for cls in classes:
        if cls.lower() in {"one", "two", "three", "four", "five"}:
            return parse_rating(cls)
    text = _extract_text(node).lower()
    if "five" in text:
        return "5★"
    if "four" in text:
        return "4★"
    if "three" in text:
        return "3★"
    if "two" in text:
        return "2★"
    if "one" in text:
        return "1★"
    return "N/A"


def _extract_price(node: Any) -> tuple[str, float]:
    if not node:
        return "N/A", 0.0
    price_text = _extract_text(node)
    if not price_text:
        return "N/A", 0.0
    return price_text, parse_price(price_text)


def _extract_product_from_jsonld(data: Any, base_url: str) -> List[Dict[str, object]]:
    products: List[Dict[str, object]] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            node_type = node.get("@type")
            if isinstance(node_type, list):
                types = [str(item) for item in node_type]
            else:
                types = [str(node_type)] if node_type else []
            if "Product" in types:
                name = node.get("name") or ""
                offers = node.get("offers") or {}
                price_value = 0.0
                price_text = "N/A"
                if isinstance(offers, dict):
                    price_text = str(offers.get("price") or "N/A")
                    price_value = parse_price(offers.get("price"))
                elif isinstance(offers, list) and offers:
                    first_offer = offers[0] if isinstance(offers[0], dict) else {}
                    price_text = str(first_offer.get("price") or "N/A")
                    price_value = parse_price(first_offer.get("price"))
                image_value = node.get("image") or ""
                if isinstance(image_value, list):
                    image_value = image_value[0] if image_value else ""
                rating_value = "N/A"
                aggregate_rating = node.get("aggregateRating") or {}
                if isinstance(aggregate_rating, dict):
                    rating_value = str(aggregate_rating.get("ratingValue") or "N/A")
                if name:
                    products.append({
                        "name": str(name),
                        "price": price_text,
                        "price_value": price_value,
                        "rating": parse_rating(rating_value),
                        "image": build_image_url(str(image_value), base_url),
                        "category": node.get("category") or "General",
                    })
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return products


def parse_products_from_html(html: str, base_url: str) -> List[Dict[str, object]]:
    soup = BeautifulSoup(html, "html.parser")
    products: List[Dict[str, object]] = []

    for script in soup.select("script[type='application/ld+json']"):
        payload = script.string or ""
        if not payload.strip():
            continue
        try:
            parsed_payload = json.loads(payload)
        except json.JSONDecodeError:
            continue
        products.extend(_extract_product_from_jsonld(parsed_payload, base_url))

    if products:
        return products

    for card in soup.select("article.product_pod"):
        heading = card.select_one("h3 a") or card.select_one("h3") or card.select_one("a")
        price_node = card.select_one("p.price_color") or card.select_one(".price")
        rating_node = card.select_one("p.star-rating") or card.select_one(".rating")
        image_node = card.select_one("img")
        name = _extract_text(heading) or card.get("title") or ""
        price_text, price_value = _extract_price(price_node)
        products.append({
            "name": name.strip(),
            "price": price_text,
            "price_value": price_value,
            "rating": _extract_rating(rating_node),
            "image": _extract_image(image_node, base_url),
            "category": "Books",
        })

    if products:
        return products

    for card in soup.select("article, li, div, section"):
        classes = " ".join(card.get("class", [])).lower()
        if not any(keyword in classes for keyword in ["product", "item", "card", "tile", "sku"]):
            continue
        heading = card.select_one("h2, h3, h4, .title, .product-title, .name") or card.select_one("a")
        price_node = card.select_one(".price, .price_color, .amount, [class*='price']")
        rating_node = card.select_one(".rating, .stars, .star-rating, [class*='star']")
        image_node = card.select_one("img")
        name = _extract_text(heading)
        price_text, price_value = _extract_price(price_node)
        if not name or not price_text or price_text == "N/A":
            continue
        products.append({
            "name": name.strip(),
            "price": price_text,
            "price_value": price_value,
            "rating": _extract_rating(rating_node),
            "image": _extract_image(image_node, base_url),
            "category": "General",
        })

    seen = set()
    unique_products: List[Dict[str, object]] = []
    for product in products:
        key = (product.get("name", "").strip().lower(), str(product.get("price", "")))
        if key in seen:
            continue
        seen.add(key)
        unique_products.append(product)
    return unique_products


def scrape_products(url: str) -> List[Dict[str, object]]:
    normalized_url = normalize_url(url)

    try:
        response = requests.get(normalized_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        products = parse_products_from_html(response.text, normalized_url)
        if products:
            return products
        raise RuntimeError("No products found.")
    except requests.RequestException as exc:
        raise RuntimeError(f"Website unreachable or blocked: {exc}") from exc


def export_products_to_csv(products: List[Dict[str, object]], file_path: str) -> str:
    df = pd.DataFrame(products)
    output_path = os.path.abspath(file_path)
    df.to_csv(output_path, index=False)
    return output_path


def export_products_to_json(products: List[Dict[str, object]], file_path: str) -> str:
    output_path = os.path.abspath(file_path)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(products, fh, indent=2)
    return output_path


def export_products_to_excel(products: List[Dict[str, object]], file_path: str) -> str:
    df = pd.DataFrame(products)
    output_path = os.path.abspath(file_path)
    df.to_excel(output_path, index=False)
    return output_path
