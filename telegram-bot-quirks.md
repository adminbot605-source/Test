---
name: Telegram bot platform quirks
description: Non-obvious constraints for the SaaS Telegram bot — connecting groups, superadmin connect, and a tooling display quirk seen in this repo.
---

## Connecting a group/channel = startgroup deep link + my_chat_member, never a direct button
A bot cannot add itself to a group. The "➕ Добавить сообщество" button must NOT try to
connect anything directly — it shows instructions plus a URL button:
`https://t.me/{bot_username}?startgroup=true&admin=delete_messages+restrict_members+invite_users`.
The actual community row is created in the `my_chat_member` handler (`chat.py:bot_added_to_chat`)
when Telegram reports the bot became `administrator`.
**Why:** a user once reported "добавить сообщество не работает" — the button simply had no
handler, and even a handler couldn't add the bot programmatically.
**How to apply:** any "add bot to X" UX = deep link + rely on my_chat_member; ensure
`resolve_used_update_types()` includes `my_chat_member` (it does as long as a handler is registered).

## Superadmins connect groups without a paid admin plan
Superadmins (telegram_id in `settings.superadmin_ids`) have no `admins` row by default.
`bot_added_to_chat` provisions one via `get_or_create` and bypasses both the plan-active gate
and the `max_communities` limit (`if not is_super and ...`). Communities need a valid `admin.id`,
hence the auto-provision.

## Tool output can display mangled substrings — verify with `read` before assuming corruption
ripgrep/bash tool *output* in this environment sometimes renders certain substrings replaced by
"n" (e.g. `подключ`→`n`, `add_community`→`n`, `def`→`n`), making intact files look corrupted and
making `rg "term"` appear to return nothing.
**Why:** wasted time suspecting a bad replace_all; the files were fine — only the displayed grep
output was mangled.
**How to apply:** when grep output looks corrupted or a known-present string "isn't found",
confirm by reading the actual file (or searching via a Python script) before editing.

## Requisites/QR: partial updates + accept either field
Admin payment details are two independent fields (`payment_requisites` text + `qr_code_file_id`).
`AdminRepository.update_requisites` must update ONLY the field(s) explicitly passed (None = leave
untouched) — never pass `requisites=""` from the QR-upload path or it wipes the saved text.
Any "show payment details" gate (e.g. user buy flow) must pass when EITHER field is set:
`if not admin or (not admin.payment_requisites and not admin.qr_code_file_id)`.
**Why:** uploading a QR used to blank the text, and the buy flow only checked the text field, so
QR-only admins got the "contact admin" fallback even though a QR existed.

## Two requisites tiers (mirror the tariff split)
Like tariffs, requisites are two independent tiers and must not be conflated:
- Platform requisites (PlatformSettings, set_platform_req/set_platform_qr, superadmin menu) — admins pay the superadmin for plans.
- Admin/community requisites (Admin.payment_requisites/qr_code_file_id, set_requisites/set_qr) — what BUYERS see when purchasing community access; buy flow reads community.admin's row.
A superadmin who owns a community needs the ADMIN tier too — add it to the superadmin menu and reuse the admin set_requisites/set_qr callbacks (they write by from_user.id, not role-gated), after ensuring the superadmin has an Admin row (get_or_create).
