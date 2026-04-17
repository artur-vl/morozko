from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from morozko_bot.bitrix import BitrixClient
from morozko_bot.config import settings
from morozko_bot.excel_loader import ExcelRepository
from morozko_bot.keyboards import (
    businesses_keyboard,
    manager_confirm_keyboard,
    options_keyboard,
    recalc_questions_keyboard,
    result_keyboard,
)
from morozko_bot.models import SessionData
from morozko_bot.rules_engine import Recommendation, RulesEngine
from morozko_bot.storage import LeadStorage


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("morozko")

repo = ExcelRepository(settings.excel_path)
storage = LeadStorage(settings.database_path)
bitrix = BitrixClient(settings.bitrix_webhook_base)
sessions: dict[int, SessionData] = {}


class BotContext:
    rules: RulesEngine


ctx = BotContext()


def _is_yes(value: str) -> bool:
    return str(value).strip().lower() in {"yes", "true", "1"}


def _current_data():
    if repo.data is None:
        repo.load()
    return repo.data


def _active_businesses() -> list[tuple[str, str]]:
    data = _current_data()
    df = data.businesses[data.businesses["is_active"].map(_is_yes)].copy()
    df["sort_order"] = df["sort_order"].apply(lambda x: int(x or 0))
    df = df.sort_values("sort_order")
    return [(str(row["business_code"]), str(row["business_name"])) for _, row in df.iterrows()]


def _business_group_by_code(business_code: str) -> str:
    data = _current_data()
    row = data.businesses[data.businesses["business_code"] == business_code].head(1)
    if row.empty:
        raise ValueError(f"Unknown business_code: {business_code}")
    return str(row.iloc[0]["business_group"])


def _question_list(group: str):
    data = _current_data()
    q = data.questions[
        data.questions["is_active"].map(_is_yes)
        & data.questions["business_group"].isin([group, "all", ""])
    ].copy()
    q["question_order"] = q["question_order"].apply(lambda x: int(x or 0))
    return q.sort_values("question_order")


def _options_for(question_code: str, group: str) -> list[tuple[str, str]]:
    data = _current_data()
    q = data.question_options[
        data.question_options["is_active"].map(_is_yes)
        & (data.question_options["question_code"] == question_code)
        & data.question_options["business_group"].isin([group, "all", ""])
    ].copy()
    q["sort_order"] = q["sort_order"].apply(lambda x: int(x or 0))
    q = q.sort_values("sort_order")
    return [(str(row["option_code"]), str(row["option_text"])) for _, row in q.iterrows()]


def _next_question(session: SessionData) -> dict | None:
    questions = _question_list(session.business_group or "all")
    for _, row in questions.iterrows():
        code = str(row["question_code"])
        if code not in session.answers:
            return dict(row)
    return None


def _question_meta(question_code: str) -> dict:
    data = _current_data()
    row = data.questions[data.questions["question_code"] == question_code].head(1)
    return dict(row.iloc[0]) if not row.empty else {}


def _format_recommendation(rec: Recommendation) -> str:
    lines = [
        f"🏁 Сценарий: {rec.scenario_name}",
        rec.title_text,
        rec.body_text,
        "",
        "Оборудование:",
    ]
    for item in rec.equipment[:25]:
        name = item.get("equipment_name_client") or item.get("equipment_name_internal")
        price = item.get("price_to_rub") or 0
        qty = item.get("qty_recommended") or 1
        lines.append(f"• {name} × {qty} — до {price:,} ₽".replace(",", " "))
    lines.append("")
    lines.append(f"Итого ориентировочно: {rec.total_price_rub:,} ₽".replace(",", " "))
    if rec.manager_note_text:
        lines.append(f"\n📝 {rec.manager_note_text}")
    return "\n".join(lines)


def _catalog_link(session: SessionData) -> str | None:
    data = _current_data()
    row = data.businesses[data.businesses["business_code"] == session.business_code].head(1)
    if row.empty:
        return None
    link_code = str(row.iloc[0].get("catalog_link_code", "")).strip()
    if not link_code or "links" not in data.settings.columns:
        return None
    return None


async def _ask_question(target: Message | CallbackQuery, session: SessionData, question_code: str | None = None):
    question = _question_meta(question_code) if question_code else _next_question(session)
    if question is None:
        await _send_result(target, session)
        return

    q_code = str(question["question_code"])
    options = _options_for(q_code, session.business_group or "all")
    text = str(question.get("question_text", "Выберите вариант:"))
    markup = options_keyboard(q_code, options)

    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup)


async def _send_result(target: Message | CallbackQuery, session: SessionData):
    recommendation = ctx.rules.build_recommendation(session)
    session.awaiting_question_code = None
    text = _format_recommendation(recommendation)
    can_recalc = session.recalculation_count < 4
    markup = result_keyboard(can_recalc=can_recalc, has_catalog=False)

    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup)


async def _send_to_bitrix(session: SessionData) -> tuple[bool, str]:
    recommendation = ctx.rules.build_recommendation(session)
    fields = {
        "TITLE": f"Морозко — {session.business_code} — @{session.telegram_username or 'no_username'}",
        "SOURCE_ID": settings.bitrix_source_id,
        "NAME": session.full_name or session.telegram_username or str(session.telegram_user_id),
        "COMMENTS": _format_recommendation(recommendation),
        "UF_CRM_MOROZKO_TG_ID": str(session.telegram_user_id),
        "UF_CRM_MOROZKO_USERNAME": session.telegram_username or "",
        "UF_CRM_MOROZKO_BUSINESS": session.business_code or "",
        "UF_CRM_MOROZKO_GROUP": session.business_group or "",
        "UF_CRM_MOROZKO_SCENARIO": recommendation.text_id,
        "UF_CRM_MOROZKO_TOTAL": recommendation.total_price_rub,
    }
    for index, code in enumerate(session.answers.values(), start=1):
        fields[f"UF_CRM_MOROZKO_Q{index}"] = code

    lead_id = storage.get_lead_id(session.telegram_user_id)
    if lead_id:
        await bitrix.update_lead(lead_id, fields)
        return True, f"Лид обновлён: #{lead_id}"

    new_id = await bitrix.add_lead(fields)
    storage.upsert_lead_id(session.telegram_user_id, new_id)
    session.lead_id = new_id
    return True, f"Лид создан: #{new_id}"


def _recalc_question_items(session: SessionData) -> list[tuple[str, str]]:
    qdf = _question_list(session.business_group or "all")
    items = []
    for _, row in qdf.iterrows():
        code = str(row["question_code"])
        if code in session.answers:
            label = str(row.get("short_label", "")).strip() or str(row.get("question_text", code))
            items.append((code, label[:60]))
    return items


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start_handler(message: Message):
        sessions[message.from_user.id] = SessionData(
            telegram_user_id=message.from_user.id,
            telegram_username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
        text = "Привет! Я Морозко 🤖\nПодберу оборудование по вашему формату бизнеса."
        await message.answer(text, reply_markup=businesses_keyboard(_active_businesses()))

    @dp.message(Command("reload"))
    async def reload_handler(message: Message):
        if message.from_user.id not in settings.admin_id_set:
            await message.answer("Команда доступна только администратору.")
            return
        repo.load()
        ctx.rules = RulesEngine(repo.data.result_texts, repo.data.catalog_equipment)
        await message.answer("Excel перезагружен ✅")

    @dp.callback_query(F.data.startswith("biz:"))
    async def business_handler(call: CallbackQuery):
        session = sessions.setdefault(call.from_user.id, SessionData(telegram_user_id=call.from_user.id))
        business_code = call.data.split(":", 1)[1]
        session.business_code = business_code
        session.business_group = _business_group_by_code(business_code)
        session.answers.clear()
        session.recalculation_count = 0
        await call.message.answer(f"Отлично, выбрали: {business_code}")
        await _ask_question(call, session)
        await call.answer()

    @dp.callback_query(F.data.startswith("ans:"))
    async def answer_handler(call: CallbackQuery):
        _, question_code, option_code = call.data.split(":", 2)
        session = sessions.setdefault(call.from_user.id, SessionData(telegram_user_id=call.from_user.id))
        session.answers[question_code] = option_code
        await call.answer("Сохранено")
        await _ask_question(call, session)

    @dp.callback_query(F.data == "recalc")
    async def recalc_handler(call: CallbackQuery):
        session = sessions.get(call.from_user.id)
        if not session:
            await call.answer("Начните с /start", show_alert=True)
            return
        if session.recalculation_count >= 4:
            await call.answer("Достигнут лимит 4 перерасчётов", show_alert=True)
            return
        items = _recalc_question_items(session)
        await call.message.answer("Что поменяем?", reply_markup=recalc_questions_keyboard(items))
        await call.answer()

    @dp.callback_query(F.data.startswith("edit:"))
    async def edit_handler(call: CallbackQuery):
        question_code = call.data.split(":", 1)[1]
        session = sessions.get(call.from_user.id)
        if not session:
            await call.answer("Начните с /start", show_alert=True)
            return
        session.awaiting_question_code = question_code
        await call.message.answer("Выберите новый вариант:")
        await _ask_question(call, session, question_code=question_code)
        await call.answer()

    @dp.callback_query(F.data == "manager")
    async def manager_handler(call: CallbackQuery):
        await call.message.answer(
            "Передать ваш результат менеджеру и создать/обновить лид в Bitrix24?",
            reply_markup=manager_confirm_keyboard(),
        )
        await call.answer()

    @dp.callback_query(F.data == "manager:no")
    async def manager_no_handler(call: CallbackQuery):
        await call.answer("Ок, не передаю")

    @dp.callback_query(F.data == "manager:yes")
    async def manager_yes_handler(call: CallbackQuery):
        session = sessions.get(call.from_user.id)
        if not session:
            await call.answer("Начните с /start", show_alert=True)
            return
        try:
            ok, msg = await _send_to_bitrix(session)
            await call.message.answer(msg if ok else "Ошибка передачи")
        except Exception as exc:
            logger.exception("Bitrix sync failed")
            await call.message.answer(f"Не удалось передать в Bitrix24: {exc}")
        await call.answer()

    return dp


async def main() -> None:
    Path("data").mkdir(exist_ok=True)
    repo.load()
    ctx.rules = RulesEngine(repo.data.result_texts, repo.data.catalog_equipment)

    bot = Bot(settings.telegram_token)
    dp = build_dispatcher()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
