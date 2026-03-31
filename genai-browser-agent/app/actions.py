from __future__ import annotations

from app.browser import BrowserController

OPEN_URL = "open_url"
CLICK = "click"
TYPE = "type"
STOP = "stop"

SUPPORTED_ACTIONS = {OPEN_URL, CLICK, TYPE, STOP}


def make_action(action: str, **kwargs: str) -> dict:
    return {"action": action, "args": kwargs}


def execute(action: dict, browser: BrowserController) -> dict:
    name = action.get("action", "")
    args = action.get("args", {})

    if name not in SUPPORTED_ACTIONS:
        return {"success": False, "message": f"Unknown action: {name}"}

    if name == STOP:
        return {"success": True, "message": "Agent stopped."}

    try:
        if name == OPEN_URL:
            browser.open_url(args["url"])
        elif name == CLICK:
            browser.click(args["target"])
        elif name == TYPE:
            browser.type(args["target"], args["text"])
    except KeyError as exc:
        return {"success": False, "message": f"Missing required arg: {exc}"}
    except Exception as exc:
        return {"success": False, "message": str(exc)}

    return {"success": True, "message": f"{name} executed."}