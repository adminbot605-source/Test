---
name: Currency auto-conversion
description: How community tariff prices convert to the buyer's currency by language, and the provider/product choices behind it.
---

# Community tariff currency auto-conversion

Buyers see and pay community tariffs in the currency of their selected interface
language (mapping in `app/utils/exchange.py`: ru→RUB, en→USD, kg→KGS, kz→KZT, uz→UZS).
The converted amount+currency is what gets stored in the Payment row and shown to the
admin in the receipt notification.

**Rate source:** `https://open.er-api.com/v6/latest/USD` — key-less, free, and (unlike
frankfurter.app / ECB feeds) actually supports the CIS currencies KGS/KZT/UZS/RUB.
Rates cached in-memory 1h with an asyncio single-flight lock; on API failure callers
fall back to the ORIGINAL price+currency so purchases never break.

**Why buyers pay in their own currency (not just informational):** explicit user choice.
**Known tradeoff the user accepted:** the admin's requisites (card/QR) are still in the
admin's own currency, so a cross-currency buyer must convert when actually transferring —
the bot only converts the displayed/recorded amount.

**Scope:** only the end-user community buy flow converts. The admin→platform plan
purchase flow is intentionally left hardcoded in KGS (admins pay the superadmin).
