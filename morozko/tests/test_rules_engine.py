import pandas as pd

from morozko_bot.models import SessionData
from morozko_bot.rules_engine import RulesEngine


def test_rules_engine_filters_and_prioritizes():
    result_texts = pd.DataFrame(
        [
            {
                "text_id": "base",
                "business_group": "foodservice",
                "priority": 10,
                "scenario_name": "Base",
                "title_text": "T1",
                "body_text": "B1",
                "manager_note_text": "",
                "is_active": "yes",
                "budget_codes": "economy",
                "strategy_mode": "strategic",
            },
            {
                "text_id": "fallback",
                "business_group": "foodservice",
                "priority": 1,
                "scenario_name": "Fallback",
                "title_text": "T2",
                "body_text": "B2",
                "manager_note_text": "",
                "is_active": "yes",
                "budget_codes": "",
                "strategy_mode": "all",
            },
        ]
    )
    equipment = pd.DataFrame(
        [
            {
                "item_code": "a",
                "entity_type": "category",
                "equipment_name_client": "A",
                "required_class": "must_have",
                "priority_score": 5,
                "is_active": "yes",
                "business_group": "foodservice",
                "budget_codes": "economy",
                "strategy_modes": "strategic",
                "price_to_rub": 100,
                "qty_recommended": 1,
            },
            {
                "item_code": "b",
                "entity_type": "model",
                "equipment_name_client": "B",
                "required_class": "optional",
                "priority_score": 1,
                "is_active": "yes",
                "business_group": "foodservice",
                "budget_codes": "",
                "strategy_modes": "all",
                "price_to_rub": 50,
                "qty_recommended": 1,
            },
        ]
    )
    session = SessionData(telegram_user_id=1, business_group="foodservice", answers={"Q5": "economy"})

    rec = RulesEngine(result_texts, equipment).build_recommendation(session)

    assert rec.text_id == "base"
    assert [item["item_code"] for item in rec.equipment] == ["a", "b"]
    assert rec.total_price_rub == 150
