from dataclasses import dataclass, field


FIT_CODE_FIELDS = [
    "revenue_core_codes",
    "client_flow_codes",
    "org_model_codes",
    "area_codes",
    "budget_codes",
    "timing_codes",
]


@dataclass
class SessionData:
    telegram_user_id: int
    telegram_username: str | None = None
    full_name: str | None = None
    business_code: str | None = None
    business_group: str | None = None
    answers: dict[str, str] = field(default_factory=dict)
    recalculation_count: int = 0
    lead_id: int | None = None
    awaiting_question_code: str | None = None

    def selected_option_codes(self) -> set[str]:
        return set(self.answers.values())
