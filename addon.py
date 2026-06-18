"""Mailgun email notification integration."""

from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Literal

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field, SecretStr

from app.addons.notifications.base import NotificationAddon
from app.addons.notifications.helpers import post_json_webhook
from app.addons.log import info, warning
from app.addons.config_serialization import dump_addon_config

MailgunRegion = Literal["us", "eu"]

_API_BASES: dict[MailgunRegion, str] = {
    "us": "https://api.mailgun.net/v3",
    "eu": "https://api.eu.mailgun.net/v3",
}


class MailgunConfig(BaseModel):
    api_key: SecretStr = Field(default=..., description="Mailgun API key")
    domain: str = Field(default=..., description="Sending domain")
    from_address: str = Field(default=..., description="Default From email address")
    region: MailgunRegion = Field(default="us", description="API region (us or eu)")

    @classmethod
    def config_model(cls):
        return cls


class MailgunAddon(NotificationAddon):
    addon_id: str = "mailgun"
    addon_name: str = "Mailgun"
    addon_description: str = "Send transactional emails via Mailgun."
    addon_category: str = "notification"
    version: str = "1.0.0"
    is_enabled: bool = False
    supported_channels: ClassVar[list[str]] = ["email"]

    _config: Dict[str, Any] | None = None
    _api_key: str | None = None
    _domain: str | None = None
    _from_address: str | None = None
    _region: MailgunRegion = "us"

    @classmethod
    def config_schema(cls):
        return MailgunConfig

    async def initialize(self, config: dict) -> None:
        validated = self.config_schema()(**config)
        self._config = dump_addon_config(validated)
        self._api_key = validated.api_key.get_secret_value()
        self._domain = validated.domain
        self._from_address = validated.from_address
        self._region = validated.region
        self.is_enabled = True
        info("Mailgun", "Initialized (domain={}, region={})", self._domain, self._region)

    async def validate_config(self, config: dict) -> None:
        from app.core.exceptions import ValidationError

        validated = self.config_schema()(**config)
        api_key = validated.api_key.get_secret_value()
        if not api_key:
            return
        api_base = _API_BASES[validated.region]
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{api_base}/domains/{validated.domain}",
                auth=("api", api_key),
            )
        if resp.status_code == 401:
            raise ValidationError(message="Invalid API key — check your credentials")
        if resp.status_code == 403:
            raise ValidationError(
                message="API key is valid but missing required permissions: domains:read"
            )
        if resp.status_code >= 400:
            raise ValidationError(message="Mailgun rejected the API key")

    async def shutdown(self) -> None:
        self._api_key = None
        self._domain = None
        self._from_address = None
        self.is_enabled = False

    def _messages_url(self) -> str:
        return f"{_API_BASES[self._region]}/{self._domain}/messages"

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
    ) -> Dict[str, Any]:
        if not self._api_key or not self._domain or not self._from_address:
            return {"success": False, "message_id": "", "error": "Not configured", "to": to}

        data: dict[str, str] = {
            "from": self._from_address,
            "to": to,
            "subject": subject,
        }
        if html:
            data["html"] = body
        else:
            data["text"] = body

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    self._messages_url(),
                    auth=("api", self._api_key),
                    data=data,
                )
                resp.raise_for_status()
                result = resp.json()
                return {
                    "success": True,
                    "message_id": result.get("id", ""),
                    "to": to,
                }
        except Exception as exc:
            warning("Mailgun", "send_email to={} error: {}", to, exc)
            return {"success": False, "message_id": "", "error": str(exc), "to": to}

    async def send_sms(self, to: str, body: str) -> Dict[str, Any]:
        return self.channel_not_supported("sms", to)

    async def send_push(
        self,
        to: str,
        title: str,
        body: str,
        data: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return self.channel_not_supported("push", to)

    async def send_webhook(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        result = await post_json_webhook(url, payload)
        if not result.get("success"):
            warning("Mailgun", "send_webhook to={} error: {}", url, result.get("error"))
        return result

    def get_routers(self) -> List[APIRouter]:
        return []

    def get_admin_routes(self) -> List[APIRouter]:
        from app.addons.notifications.mailgun.routes import admin_router

        return [admin_router]

    def get_admin_templates(self) -> str:
        from pathlib import Path

        return str(Path(__file__).resolve().parent / "templates")

    def get_admin_static(self) -> str:
        from pathlib import Path

        return str(Path(__file__).resolve().parent / "static")
