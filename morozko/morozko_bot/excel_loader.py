from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


REQUIRED_SHEETS = {
    "businesses",
    "questions",
    "question_options",
    "result_texts",
    "catalog_equipment",
    "settings",
}


@dataclass
class ExcelData:
    businesses: pd.DataFrame
    questions: pd.DataFrame
    question_options: pd.DataFrame
    result_texts: pd.DataFrame
    catalog_equipment: pd.DataFrame
    settings: pd.DataFrame


class ExcelRepository:
    def __init__(self, path: str):
        self.path = Path(path)
        self.data: ExcelData | None = None

    def load(self) -> ExcelData:
        if not self.path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.path}")

        workbook = pd.read_excel(self.path, sheet_name=None)
        missing = REQUIRED_SHEETS - set(workbook)
        if missing:
            raise ValueError(f"Missing sheets in workbook: {', '.join(sorted(missing))}")

        def normalize(df: pd.DataFrame) -> pd.DataFrame:
            out = df.copy()
            out.columns = [str(col).strip() for col in out.columns]
            out = out.fillna("")
            return out

        self.data = ExcelData(
            businesses=normalize(workbook["businesses"]),
            questions=normalize(workbook["questions"]),
            question_options=normalize(workbook["question_options"]),
            result_texts=normalize(workbook["result_texts"]),
            catalog_equipment=normalize(workbook["catalog_equipment"]),
            settings=normalize(workbook["settings"]),
        )
        self._validate_minimum_schema(self.data)
        return self.data

    @staticmethod
    def _validate_minimum_schema(data: ExcelData) -> None:
        required_columns = {
            "businesses": {"business_code", "business_name", "business_group", "is_active", "sort_order"},
            "questions": {"question_code", "business_group", "question_order", "question_text", "is_active"},
            "question_options": {"question_code", "business_group", "option_code", "option_text", "is_active", "sort_order"},
            "result_texts": {"text_id", "business_group", "priority", "scenario_name", "is_active"},
            "catalog_equipment": {"item_code", "entity_type", "equipment_name_client", "required_class", "is_active"},
        }
        table_map = {
            "businesses": data.businesses,
            "questions": data.questions,
            "question_options": data.question_options,
            "result_texts": data.result_texts,
            "catalog_equipment": data.catalog_equipment,
        }
        for table, req in required_columns.items():
            missing = req - set(table_map[table].columns)
            if missing:
                raise ValueError(f"Missing columns in sheet '{table}': {', '.join(sorted(missing))}")
