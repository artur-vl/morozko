from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    excel_path: str = Field(default="./data/Morozko_master_data_template_v4_1_equipment_PI_codes.xlsx", alias="MOROZKO_EXCEL_PATH")
    bitrix_webhook_base: str = Field(default="", alias="BITRIX_WEBHOOK_BASE")
    bitrix_source_id: str = Field(default="WEB", alias="BITRIX_SOURCE_ID")
    admin_ids: str = Field(default="", alias="BOT_ADMIN_IDS")
    database_path: str = Field(default="./data/morozko.db", alias="DATABASE_PATH")

    @property
    def admin_id_set(self) -> set[int]:
        if not self.admin_ids.strip():
            return set()
        return {int(x.strip()) for x in self.admin_ids.split(",") if x.strip()}


settings = Settings()
