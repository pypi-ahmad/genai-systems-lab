from __future__ import annotations

import logging
import re

from app.browser import BrowserController
from shared.llm.gemini import generate_text_from_image

logger = logging.getLogger(__name__)

MAX_CHARS = 4000
VISION_MODEL = "gemini-3-flash-preview"

VISION_PROMPT = (
    "Describe this browser screenshot concisely for an autonomous web agent. "
    "List the main visible content, interactive elements (buttons, links, inputs) "
    "with their labels, and the current page state. "
    "Be factual and brief. Do not speculate about hidden content."
)


def get_observation(browser: BrowserController, use_vision: bool = False) -> str:
    text_obs = _get_text_observation(browser)

    if not use_vision:
        return text_obs

    vision_obs = _get_vision_observation(browser)
    if vision_obs:
        return f"## Text Content\n{text_obs}\n\n## Visual Description\n{vision_obs}"
    return text_obs


def _get_text_observation(browser: BrowserController) -> str:
    raw = browser.get_page_text()
    text = _clean(raw)
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n...[truncated]"
    return text


def _get_vision_observation(browser: BrowserController) -> str:
    try:
        screenshot = browser.screenshot()
        return generate_text_from_image(
            prompt=VISION_PROMPT,
            image=screenshot,
            model=VISION_MODEL,
        )
    except Exception:
        logger.warning("Vision observation failed, falling back to text only.", exc_info=True)
        return ""


def _clean(text: str) -> str:
    text = text.replace("\t", " ")
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()