"""
Modification Log:
------------------
| Date       | Author         | MOD TAG            | Description                                                                                         |
|------------|----------------|--------------------|-----------------------------------------------------------------------------------------------------|
| 2024-11-05 | AAK7S          | CWE-20             | Updated `post_webhook` function to add secure hostname parsing for URL verification.                |
|            |                |                    | **Old Code:** Used substring checks for service identification, which could allow bypasses.         |
|            |                |                    | **New Code:** Parse URLs using `urlparse` to extract and verify the hostname accurately.            |

"""

import json
import logging
from urllib.parse import urlparse

import requests
from open_webui.config import WEBUI_FAVICON_URL
from open_webui.env import SRC_LOG_LEVELS, VERSION

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["WEBHOOK"])


def post_webhook(name: str, url: str, message: str, event_data: dict) -> bool:
    """
    Sends a webhook request to a specified URL with a given message and event data.
    
    :param url: Webhook URL to which the request will be sent.
    :param message: Message content to be included in the webhook payload.
    :param event_data: Additional event data to include in the payload.
    :return: True if the request was successful, False otherwise.
    
    MOD: CWE-20  - Added URL parsing to verify hostnames.
    """
    try:
        log.debug(f"post_webhook: {url}, {message}, {event_data}")
        payload = {}

        # Parse the hostname from the URL for secure verification
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname

        # Slack and Google Chat Webhooks
        #if "https://hooks.slack.com" in url or "https://chat.googleapis.com" in url:
        if hostname == "hooks.slack.com" or hostname == "chat.googleapis.com":
            payload["text"] = message
        # Discord Webhooks
        #elif "https://discord.com/api/webhooks" in url:
        elif hostname == "discord.com":
            payload["content"] = (
                message
                if len(message) < 2000
                else f"{message[: 2000 - 20]}... (truncated)"
            )
        # Microsoft Teams Webhooks
        #elif "webhook.office.com" in url:
        elif hostname == "webhook.office.com":
            action = event_data.get("action", "undefined")
            facts = [
                {"name": name, "value": value}
                for name, value in json.loads(event_data.get("user", {})).items()
            ]
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "0076D7",
                "summary": message,
                "sections": [
                    {
                        "activityTitle": message,
                        "activitySubtitle": f"{name} ({VERSION}) - {action}",
                        "activityImage": WEBUI_FAVICON_URL,
                        "facts": facts,
                        "markdown": True,
                    }
                ],
            }
        # Default Payload
        else:
            payload = {**event_data}

        log.debug(f"payload: {payload}")
        r = requests.post(url, json=payload)
        r.raise_for_status()
        log.debug(f"r.text: {r.text}")
        return True
    except Exception as e:
        log.exception(e)
        return False
