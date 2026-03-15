"""
PestGuard AI — AI Engine
Handles:
  1. Natural language → structured application log parsing
  2. Smart chemical product matching
  3. Compliance summary generation

Uses OpenAI GPT-4o if API key is present.
Falls back to a smart rule-based parser for demo mode.
"""

import os
import re
import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional

from epa_products import (
    search_products, get_by_reg_no, get_by_name,
    PEST_ALIASES, METHOD_ALIASES, EPA_PRODUCTS
)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o"


# ── OpenAI API Call ────────────────────────────────────────────────────────────

def _call_openai(system_prompt: str, user_message: str) -> Optional[str]:
    """Make a raw OpenAI API call. Returns response text or None."""
    if not OPENAI_API_KEY:
        return None

    payload = json.dumps({
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.1,
        "max_tokens": 1000,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[AI] OpenAI call failed: {e}")
        return None


# ── Smart Rule-Based Parser (Demo / Fallback Mode) ────────────────────────────

def _smart_parse(text: str) -> dict:
    """
    Extract structured log data from natural language input.
    Handles phrases like:
      'Treated 123 Main St for roaches with Talstar Pro, 2 oz spray, sunny and 78°F'
    """
    text_lower = text.lower()
    result = {}

    # ── Date Extraction ──────────────────────────────────────────────────────
    date_patterns = [
        r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b',
        r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',
        r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{1,2}),?\s+(\d{4})\b',
        r'\b(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{4})\b',
    ]
    month_map = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
                 "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
    for pat in date_patterns:
        m = re.search(pat, text_lower)
        if m:
            try:
                groups = m.groups()
                if groups[0].isdigit() and len(groups[0]) == 4:
                    d = datetime(int(groups[0]), int(groups[1]), int(groups[2]))
                elif groups[0][:3] in month_map:
                    d = datetime(int(groups[2]), month_map[groups[0][:3]], int(groups[1]))
                elif groups[1][:3] in month_map:
                    d = datetime(int(groups[2]), month_map[groups[1][:3]], int(groups[0]))
                else:
                    d = datetime(int(groups[2]), int(groups[0]), int(groups[1]))
                result["date_applied"] = d.strftime("%Y-%m-%d")
                break
            except ValueError:
                pass
    if not result.get("date_applied"):
        result["date_applied"] = datetime.now().strftime("%Y-%m-%d")

    # ── Product Detection ────────────────────────────────────────────────────
    matched_product = None
    for prod in EPA_PRODUCTS:
        if prod["product_name"].lower() in text_lower:
            matched_product = prod
            break
    if not matched_product:
        # Try active ingredient
        for prod in EPA_PRODUCTS:
            ai = prod["active_ingredient"].lower().split()[0]
            if len(ai) > 5 and ai in text_lower:
                matched_product = prod
                break

    if matched_product:
        result["pesticide_name"] = matched_product["product_name"]
        result["epa_reg_no"] = matched_product["epa_reg_no"]
        result["active_ingredient"] = matched_product["active_ingredient"]
    else:
        # Try to grab any quoted or capitalized product name
        m = re.search(r'"([^"]+)"', text)
        if m:
            result["pesticide_name"] = m.group(1)
        # Try to find EPA reg number pattern
        m = re.search(r'\b(\d{2,6}-\d{1,5})\b', text)
        if m:
            result["epa_reg_no"] = m.group(1)
            prod = get_by_reg_no(m.group(1))
            if prod:
                result["pesticide_name"] = prod["product_name"]
                result["active_ingredient"] = prod["active_ingredient"]

    # ── Target Pest Extraction ────────────────────────────────────────────────
    for alias, canonical in PEST_ALIASES.items():
        if alias in text_lower:
            result["target_pest"] = canonical
            break
    if not result.get("target_pest"):
        # Common words
        pests = ["ants","cockroaches","termites","fleas","ticks","mosquitoes",
                 "spiders","mice","rats","bed bugs","flies","wasps","hornets"]
        for pest in pests:
            if pest in text_lower:
                result["target_pest"] = pest
                break

    # ── Application Site ─────────────────────────────────────────────────────
    sites = {
        "kitchen": "Kitchen", "bathroom": "Bathroom", "garage": "Garage",
        "attic": "Attic", "basement": "Basement", "crawl space": "Crawl Space",
        "perimeter": "Exterior Perimeter", "exterior": "Exterior",
        "lawn": "Lawn", "yard": "Yard", "outdoor": "Outdoor",
        "interior": "Interior General", "inside": "Interior General",
        "restaurant": "Commercial Kitchen", "office": "Office",
        "warehouse": "Warehouse",
    }
    for kw, site_name in sites.items():
        if kw in text_lower:
            result["application_site"] = site_name
            break
    if not result.get("application_site"):
        result["application_site"] = "Interior General"

    # ── Site Address ─────────────────────────────────────────────────────────
    addr_pattern = re.search(
        r'\b(\d{1,5}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:St|Ave|Rd|Blvd|Dr|Ln|Way|Ct|Pl|Street|Avenue|Road|Drive|Lane|Court|Pkwy|Highway|Hwy)\.?(?:\s+(?:Apt|Unit|Suite|#)\s*\d+)?)',
        text
    )
    if addr_pattern:
        result["site_address"] = addr_pattern.group(1)

    # ── Amount & Unit ────────────────────────────────────────────────────────
    amount_m = re.search(r'(\d+(?:\.\d+)?)\s*(oz|ounce|ml|gallon|gal|lb|pound|g|gram|kg|bag|unit)s?', text_lower)
    if amount_m:
        result["amount_applied"] = float(amount_m.group(1))
        unit_map = {"oz":"oz","ounce":"oz","ml":"ml","gallon":"gallon","gal":"gallon",
                    "lb":"lbs","pound":"lbs","g":"g","gram":"g","kg":"kg","bag":"bag","unit":"unit"}
        result["unit"] = unit_map.get(amount_m.group(2), amount_m.group(2))

    # ── Application Method ────────────────────────────────────────────────────
    for kw, method in METHOD_ALIASES.items():
        if kw in text_lower:
            result["application_method"] = method
            break

    # ── Weather ──────────────────────────────────────────────────────────────
    weather_parts = []
    weather_kws = {
        "sunny": "Sunny", "cloudy": "Cloudy", "overcast": "Overcast",
        "clear": "Clear", "windy": "Windy", "calm": "Calm winds",
        "humid": "Humid", "dry": "Dry", "raining": "Rain",
    }
    for kw, label in weather_kws.items():
        if kw in text_lower:
            weather_parts.append(label)

    temp_m = re.search(r'(\d{2,3})\s*°?\s*f', text_lower)
    if temp_m:
        result["temperature_f"] = float(temp_m.group(1))
        weather_parts.append(f"{temp_m.group(1)}°F")

    wind_m = re.search(r'(\d+)\s*(?:mph|km\/h|knots?)?\s*wind', text_lower)
    if wind_m:
        result["wind_speed_mph"] = float(wind_m.group(1))
        weather_parts.append(f"Wind {wind_m.group(1)} mph")

    if weather_parts:
        result["weather_conditions"] = ", ".join(weather_parts)

    # ── PPE ──────────────────────────────────────────────────────────────────
    ppe_items = []
    if "glove" in text_lower: ppe_items.append("gloves")
    if "goggle" in text_lower or "eye protection" in text_lower: ppe_items.append("eye protection")
    if "respirator" in text_lower or "mask" in text_lower: ppe_items.append("respirator")
    if "suit" in text_lower or "coverall" in text_lower: ppe_items.append("coveralls")
    if "boot" in text_lower: ppe_items.append("boots")
    if ppe_items:
        result["ppe_worn"] = ", ".join(ppe_items)

    # ── Parsing Mode Flag ────────────────────────────────────────────────────
    result["_parse_mode"] = "rule-based"
    result["_confidence"] = _estimate_confidence(result)

    return result


def _estimate_confidence(parsed: dict) -> str:
    filled = sum(1 for k in ["pesticide_name", "epa_reg_no", "target_pest",
                              "application_site", "site_address", "date_applied"]
                 if parsed.get(k))
    if filled >= 5: return "high"
    if filled >= 3: return "medium"
    return "low"


# ── OpenAI-Powered Parser ─────────────────────────────────────────────────────

PARSE_SYSTEM_PROMPT = """You are a pest control compliance assistant.
Parse the user's natural language log entry into a structured JSON object.
Return ONLY valid JSON with these fields (omit fields you can't determine):
{
  "pesticide_name": "...",
  "epa_reg_no": "...",
  "active_ingredient": "...",
  "target_pest": "...",
  "application_site": "...",
  "site_address": "...",
  "date_applied": "YYYY-MM-DD",
  "amount_applied": 0.0,
  "unit": "oz|ml|gallon|lbs|g",
  "application_method": "Sprayer|Gel Application|Bait Placement|Granular|Fogging|Injection|Dust Application|Trap Placement|Bait Station",
  "weather_conditions": "...",
  "temperature_f": 0.0,
  "wind_speed_mph": 0.0,
  "ppe_worn": "...",
  "notes": "..."
}
Use today's date if no date given. Normalize pest names to plural lowercase (ants, cockroaches, etc.)."""


def parse_log_entry(raw_text: str) -> dict:
    """
    Parse natural language log entry into structured fields.
    Uses OpenAI if available, otherwise rule-based parser.
    """
    if OPENAI_API_KEY:
        response = _call_openai(PARSE_SYSTEM_PROMPT, raw_text)
        if response:
            try:
                # Strip markdown code blocks if present
                cleaned = re.sub(r"```(?:json)?", "", response).strip()
                parsed = json.loads(cleaned)
                parsed["_parse_mode"] = "openai"
                parsed["_confidence"] = "high"
                parsed["_raw_input"] = raw_text
                return parsed
            except json.JSONDecodeError:
                print("[AI] OpenAI returned invalid JSON, falling back to rule-based")

    # Fallback: rule-based
    parsed = _smart_parse(raw_text)
    parsed["_raw_input"] = raw_text
    return parsed


# ── Compliance Summary Generator ──────────────────────────────────────────────

def generate_compliance_summary(compliance_result: dict, log: dict) -> str:
    """Generate a human-readable compliance summary for a log entry."""
    if OPENAI_API_KEY:
        prompt = f"""
Summarize this compliance check result in 2-3 plain-English sentences for a pest control business owner.
Be direct, professional, and actionable.

Application: {log.get('pesticide_name', 'Unknown')} at {log.get('site_address', 'Unknown location')}
Status: {compliance_result['status'].upper()}
Score: {compliance_result['score']}/100
Issues: {json.dumps([i['message'] for i in compliance_result['issues']])}
"""
        result = _call_openai(
            "You are a compliance advisor for pest control businesses. Be concise and helpful.",
            prompt
        )
        if result:
            return result

    # Fallback
    return compliance_result.get("summary", "Compliance check complete.")


# ── Chemical Product Matcher ──────────────────────────────────────────────────

def match_chemical(query: str) -> list:
    """AI-enhanced chemical product search."""
    # Direct search first
    results = search_products(query)
    if results:
        return results

    # Try common abbreviations and brand names
    aliases = {
        "tc": "Termidor SC",
        "ts": "Taurus SC",
        "talstar": "Talstar Pro",
        "suspend": "Suspend SC",
        "demand": "Demand CS",
        "phantom": "Phantom",
        "gentrol": "Gentrol IGR",
        "advion": "Advion Ant Bait Gel",
        "temprid": "Temprid SC",
    }
    for alias, name in aliases.items():
        if alias in query.lower():
            prod = get_by_name(name)
            if prod:
                return [prod]

    return []
