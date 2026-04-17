from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def businesses_keyboard(items: list[tuple[str, str]]):
    kb = InlineKeyboardBuilder()
    for code, text in items:
        kb.button(text=text, callback_data=f"biz:{code}")
    kb.adjust(1)
    return kb.as_markup()


def options_keyboard(question_code: str, options: list[tuple[str, str]]):
    kb = InlineKeyboardBuilder()
    for option_code, option_text in options:
        kb.button(text=option_text, callback_data=f"ans:{question_code}:{option_code}")
    kb.adjust(1)
    return kb.as_markup()


def result_keyboard(can_recalc: bool, has_catalog: bool):
    kb = InlineKeyboardBuilder()
    if can_recalc:
        kb.button(text="Пересчитать", callback_data="recalc")
    kb.button(text="Менеджер", callback_data="manager")
    if has_catalog:
        kb.button(text="Каталог", callback_data="catalog")
    kb.adjust(2)
    return kb.as_markup()


def recalc_questions_keyboard(items: list[tuple[str, str]]):
    kb = InlineKeyboardBuilder()
    for question_code, label in items:
        kb.button(text=label, callback_data=f"edit:{question_code}")
    kb.adjust(1)
    return kb.as_markup()


def manager_confirm_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Да, передать", callback_data="manager:yes")
    kb.button(text="Нет", callback_data="manager:no")
    kb.adjust(2)
    return kb.as_markup()
