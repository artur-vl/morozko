from __future__ import annotations

import asyncio

import httpx


class BitrixClient:
    def __init__(self, webhook_base: str):
        self.webhook_base = webhook_base.rstrip("/")

    async def add_lead(self, fields: dict) -> int:
        response = await self._post("crm.lead.add", {"fields": fields})
        return int(response["result"])

    async def update_lead(self, lead_id: int, fields: dict) -> bool:
        response = await self._post("crm.lead.update", {"id": lead_id, "fields": fields})
        return bool(response["result"])

    async def _post(self, method: str, payload: dict, retries: int = 3) -> dict:
        if not self.webhook_base:
            raise RuntimeError("BITRIX_WEBHOOK_BASE is not configured")

        url = f"{self.webhook_base}/{method}.json"
        last_error: Exception | None = None

        for attempt in range(1, retries + 1):
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                if "error" in data:
                    raise RuntimeError(f"Bitrix error: {data['error']} :: {data.get('error_description', '')}")
                return data
            except Exception as exc:
                last_error = exc
                if attempt < retries:
                    await asyncio.sleep(0.5 * attempt)
        raise RuntimeError(f"Bitrix request failed after retries: {last_error}")
