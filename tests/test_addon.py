"""Minimal unit tests for the mailgun addon."""

from app.addons.notifications.mailgun.addon import MailgunAddon


def test_addon_identity():
    assert MailgunAddon.addon_id == "mailgun"
    assert MailgunAddon.addon_category == "notification"
