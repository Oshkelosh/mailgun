"""Mailgun addon routes."""

from __future__ import annotations

from typing import Any

from app.addons.notifications.shared_routes import build_notification_routers


def _parse_mailgun_config_form(form: Any) -> tuple[dict[str, Any], bool]:
    region = form.get("region", "us")
    if region not in ("us", "eu"):
        region = "us"
    return (
        {
            "api_key": form.get("api_key", ""),
            "domain": form.get("domain", ""),
            "from_address": form.get("from_address", ""),
            "region": region,
        },
        form.get("is_enabled") == "on",
    )


admin_router, jinja_env = build_notification_routers(
    "mailgun",
    template_name="mailgun_config.html",
    page_title="Mailgun Settings",
    secret_keys=("api_key",),
    parse_config_form=_parse_mailgun_config_form,
)
