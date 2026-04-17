from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from morozko_bot.models import FIT_CODE_FIELDS, SessionData


REQUIRED_CLASS_RANK = {
    "must_have": 0,
    "core": 1,
    "optional": 2,
    "upgrade": 3,
}


@dataclass
class Recommendation:
    scenario_name: str
    text_id: str
    title_text: str
    body_text: str
    manager_note_text: str
    strategy_mode: str
    equipment: list[dict]
    total_price_rub: int


class RulesEngine:
    def __init__(self, result_texts: pd.DataFrame, catalog_equipment: pd.DataFrame):
        self.result_texts = result_texts
        self.catalog_equipment = catalog_equipment

    def build_recommendation(self, session: SessionData) -> Recommendation:
        option_codes = session.selected_option_codes()
        strategy_mode = self._resolve_strategy_mode(option_codes)
        result_row = self._pick_result_text(session, option_codes, strategy_mode)
        equipment = self._pick_equipment(session, option_codes, strategy_mode)
        total = sum(item.get("price_to_rub") or 0 for item in equipment)

        return Recommendation(
            scenario_name=str(result_row.get("scenario_name", "Базовый сценарий")),
            text_id=str(result_row.get("text_id", "n/a")),
            title_text=str(result_row.get("title_text", "")),
            body_text=str(result_row.get("body_text", "")),
            manager_note_text=str(result_row.get("manager_note_text", "")),
            strategy_mode=strategy_mode,
            equipment=equipment,
            total_price_rub=int(total),
        )

    def _pick_result_text(self, session: SessionData, option_codes: set[str], strategy_mode: str) -> dict:
        active = self.result_texts[self.result_texts["is_active"].str.lower().isin(["yes", "true", "1"])]
        group_ok = active[active["business_group"].isin([session.business_group, "all", ""])]
        if "business_code" in group_ok.columns and session.business_code:
            group_ok = group_ok[group_ok["business_code"].isin([session.business_code, "", None])]

        matched = [row for _, row in group_ok.iterrows() if self._row_matches(row, option_codes, strategy_mode)]
        if not matched:
            matched = [row for _, row in group_ok.iterrows()]
        matched.sort(key=lambda r: int(r.get("priority") or 0), reverse=True)
        return dict(matched[0]) if matched else {}

    def _pick_equipment(self, session: SessionData, option_codes: set[str], strategy_mode: str) -> list[dict]:
        active = self.catalog_equipment[self.catalog_equipment["is_active"].str.lower().isin(["yes", "true", "1"])]
        candidates = active[active["business_group"].isin([session.business_group, "all", ""])]
        matched = [
            self._normalize_equipment_row(dict(row))
            for _, row in candidates.iterrows()
            if self._row_matches(row, option_codes, strategy_mode)
        ]
        matched.sort(
            key=lambda x: (
                REQUIRED_CLASS_RANK.get(str(x.get("required_class", "optional")).lower(), 9),
                -int(x.get("priority_score") or 0),
            )
        )
        return matched

    def _resolve_strategy_mode(self, option_codes: set[str]) -> str:
        if any(code in option_codes for code in {"economy", "budget", "up_to_15"}):
            return "strategic"
        return "flexible"

    @staticmethod
    def _split_codes(value: object) -> set[str]:
        text = str(value or "").strip()
        if not text:
            return set()
        return {part.strip() for part in text.split(";") if part.strip()}

    def _row_matches(self, row: pd.Series | dict, option_codes: set[str], strategy_mode: str) -> bool:
        row_dict = dict(row)
        strategy_raw = str(row_dict.get("strategy_mode") or row_dict.get("strategy_modes") or "all").lower()
        strategy_set = self._split_codes(strategy_raw)
        if strategy_set and "all" not in strategy_set and strategy_mode not in strategy_set:
            return False

        for field in FIT_CODE_FIELDS:
            if field not in row_dict:
                continue
            required = self._split_codes(row_dict.get(field, ""))
            if required and required.isdisjoint(option_codes):
                return False
        return True

    @staticmethod
    def _normalize_equipment_row(row: dict) -> dict:
        row["price_from_rub"] = int(float(row.get("price_from_rub") or 0))
        row["price_to_rub"] = int(float(row.get("price_to_rub") or 0))
        row["qty_recommended"] = int(float(row.get("qty_recommended") or 0))
        return row
