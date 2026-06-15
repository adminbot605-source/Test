---
name: Two-tier tariff system & role-gated menus
description: Why "tariff editing doesn't work" reports happen — two distinct tariff concepts gated by role menu.
---

# Two tiers of "tariffs" in this bot

There are TWO unrelated tariff concepts, reached from DIFFERENT role menus:

1. **Admin subscription plans** (`AdminPlan`, table `admin_plans`) — what the
   super-admin sells to community admins. Reached ONLY from the **super-admin menu**
   → "📦 Тарифные планы". Callbacks: `sa_plan:`, `sa_edit:`, `sa_plans_list`.
2. **Community tariffs** (`SubscriptionPlan`) — what a community admin sells to end
   users. Reached ONLY from the **admin menu** → "📋 Тарифы". Callbacks: `plan_info:`,
   `edit_plan:`, `comm_plans:`.

**Why this matters:** `get_main_menu` in `handlers/start.py` is role-exclusive — a
super-admin sees ONLY the super-admin menu and can never reach the admin community
tariff flow. So a super-admin reporting "can't edit tariff price" means the
**admin-plan** flow (tier 1), NOT community tariffs. Fix the right tier.

**How to apply:** When a "button does nothing / не работает" report comes in, first
identify the user's ROLE (super-admin id in `SUPERADMIN_IDS`), then grep that every
`callback_data=` in that role's keyboards has a matching `F.data` handler. Missing
handlers show as `aiogram.event ... is not handled` in logs.

**Single-tester quirk:** the only tester is a super-admin, so "кнопки нет" reports
usually mean a user-facing feature (buy_access, become_admin, about_bot) that only
lives in `UserKeyboards.main_menu`. The super-admin menu now also exposes those
buttons so the tester can reach the full user flow. Message-handlers for those texts
live in `handlers/user.py` (matched by `F.text.in_(...)`), role-agnostic, so adding
the buttons to any reply menu just works.

**Two payment streams must stay separate.** Community-access payments and platform
admin-plan payments are distinct tables/flows. **Why:** the community `Payment` row is
hard-tied to a community (`community_id` + plan FK, both NOT NULL), so it cannot
represent "admin pays the platform." Keep them apart — don't try to overload one table.
The free 3-day trial (`admin_trial`) is the no-payment path to becoming an admin.

**Re-using a PG `Enum(...)` column type across a 2nd table breaks `create_all`.**
It tries to `CREATE TYPE` twice → DuplicateObject on a live DB. **Fix/convention:**
store status as plain `String` holding the enum's `.value` in any additional table.
Also: `Base.metadata.create_all` only ADDS missing tables (safe on a running bot);
it never alters existing columns — schema changes to existing tables need a migration.

**Money-status transitions must be atomic when multiple approvers exist.** With several
super-admins, confirm/reject must use a conditional `UPDATE ... WHERE status='pending'`
and check `rowcount`; only the winning call activates the plan / notifies. **Why:** a
read-then-write check lets a confirm+reject race both pass, activating a plan that's
also marked rejected.

**Trial admins need their own community quota.** `Admin.max_communities` is a property;
if it only reads `self.plan` it returns 0 for trials (no plan row) → the connect-group
check `len(existing) >= max_communities` (0>=0) silently rejects EVERY group with a
"plan limit" message. **Fix:** the property returns 1 while an unexpired trial is active.
Any access tier that grants `is_plan_active=True` must also grant a non-zero quota.

**Core moderation requires the bot to be a group ADMINISTRATOR, not just a member.**
**Why:** Telegram group privacy mode hides normal messages from non-admin bots, so a
member-only bot never sees (or can delete) non-subscriber messages. On `my_chat_member`,
only create the community when the bot's new status is `administrator`; if added as a
plain member, prompt the owner to promote it. Also: the `group_message_filter` must treat
users with NO `User` row as non-subscribers (delete them too), skip chat
admins/creator via `get_chat_member` (checked only for non-subscribers to save API
calls), and fail-safe to NOT deleting if that membership check errors.
