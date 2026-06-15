"""Live currency conversion based on the user's selected language.

Rates are fetched from the free, key-less open.er-api.com endpoint and cached
in memory for one hour. If the API is unreachable, callers fall back to the
original price/currency so purchases never break.
"""
import time
import asyncio
import logging
import aiohttp

logger = logging.getLogger(__name__)

# Which currency each interface language maps to.
LANG_CURRENCY = {
    "ru": "RUB",
    "en": "USD",
    "kg": "KGS",
    "kz": "KZT",
    "uz": "UZS",
}

# Currencies shown without decimals (small unit value / cash-like).
_ZERO_DECIMAL = {"KGS", "KZT", "UZS", "RUB"}

_API_URL = "https://open.er-api.com/v6/latest/USD"
_TTL_SECONDS = 3600
_cache: dict = {"rates": None, "ts": 0.0}
_refresh_lock = asyncio.Lock()


def currency_for_lang(lang: str) -> str:
    return LANG_CURRENCY.get(lang, "USD")


def _round_amount(amount: float, currency: str) -> float:
    if currency.upper() in _ZERO_DECIMAL:
        return float(round(amount))
    return float(round(amount, 2))


def format_price(amount: float, currency: str) -> str:
    if currency.upper() in _ZERO_DECIMAL:
        return f"{int(round(amount))} {currency}"
    return f"{amount:.2f} {currency}"


def _cache_fresh() -> bool:
    return bool(_cache["rates"]) and time.time() - _cache["ts"] < _TTL_SECONDS


async def _get_rates() -> dict | None:
    if _cache_fresh():
        return _cache["rates"]
    async with _refresh_lock:
        # Another coroutine may have refreshed while we waited for the lock.
        if _cache_fresh():
            return _cache["rates"]
        try:
            async with aiohttp.ClientSession() as http:
                async with http.get(_API_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()
            if data.get("result") == "success" and data.get("rates"):
                _cache["rates"] = data["rates"]
                _cache["ts"] = time.time()
                return _cache["rates"]
            logger.warning("Exchange API returned no rates: %s", data.get("result"))
        except Exception as exc:  # network/JSON errors → use stale cache if present
            logger.warning("Failed to fetch exchange rates: %s", exc)
    return _cache["rates"]


async def convert(amount: float, from_cur: str, to_cur: str) -> float | None:
    """Convert amount between currencies. Returns None if conversion is impossible."""
    from_cur = from_cur.upper()
    to_cur = to_cur.upper()
    if from_cur == to_cur:
        return _round_amount(amount, to_cur)
    rates = await _get_rates()
    if not rates or from_cur not in rates or to_cur not in rates:
        return None
    usd = amount / rates[from_cur]  # rates are per 1 USD
    return _round_amount(usd * rates[to_cur], to_cur)


async def convert_for_lang(amount: float, from_cur: str, lang: str) -> tuple[float, str]:
    """Convert to the language's currency, falling back to the original on failure."""
    target = currency_for_lang(lang)
    converted = await convert(amount, from_cur, target)
    if converted is None:
        return float(amount), from_cur
    return converted, target
