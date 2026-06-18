# Mailgun (`mailgun`)

Send transactional emails via the Mailgun Messages API.

## Overview

| | |
|---|---|
| Addon ID | `mailgun` |
| Category | notification |
| Channels | email |
| Version | 1.0.0 |
| Category guide | [../README.md](../README.md) |

Only **one** notification provider per channel can be active at a time.

## Enable and configure

1. Install this package under `app/addons/notifications/mailgun/`
2. Open **Admin → Notifications → Mailgun** at `/admin/notifications/mailgun`
3. Enter API key, sending domain, from-address, and region
4. Enable the provider checkbox and save

## Configuration schema

| Field | Type | Description |
|-------|------|-------------|
| `api_key` | secret | Mailgun private API key |
| `domain` | string | Verified sending domain (e.g. `mg.example.com`) |
| `from_address` | string | Default **From** address on that domain |
| `region` | string | `us` or `eu` — must match your Mailgun account region |

Secrets are stored in `addon_configs`, not in `.env`.

## Routes

### Admin

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/notifications/mailgun` | Config form |
| POST | `/admin/notifications/mailgun/save` | Save config |

### Public API

None — core calls `send_email()` directly.

## Provider setup

1. Sign up at [Mailgun](https://www.mailgun.com/) and add a sending domain.
2. Add DNS records (SPF, DKIM) until the domain shows as verified.
3. Copy the **Private API key** from **Settings → API Keys**.
4. Choose **US** or **EU** region to match where your domain is hosted.
5. Set **From** to an address on the verified domain.

API endpoint: `POST /v3/{domain}/messages` on `api.mailgun.net` (US) or `api.eu.mailgun.net` (EU).

SMS and push are not supported.

## Package layout

```
mailgun/
├── README.md
├── addon.py
├── routes.py
└── templates/
    └── mailgun_config.html
```

## See also

- [Notification addon development](../README.md)
- [Oshkelosh addon guide](../../README.md)
