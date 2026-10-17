# -*- coding: utf-8 -*-
"""AI rewrite module (OpenAI-compatible / Ollama).

Two behaviors are important for correctness:

1. The marker `<<AIST_OK>>` must only be mentioned in the prompt when the
   input text actually contains it. Otherwise the model adds the marker to
   its output even though the caller never asked for it.
2. The rewritten output must be in the same language as the input. Without
   this hint, an English style prompt on a Chinese input tends to produce
   English output.
"""
import json
import re
import urllib.request
from ..core.marker import PAYLOAD_MARKER

# Style keys stay in Chinese because cmd_rewrite.py --style uses them.
# Prompts are in English for better compatibility with English LLMs.
REWRITE_STYLES = {
    "自然口语": "Rewrite the text below in casual, natural spoken language",
    "书面正式": "Rewrite the text below in formal written language",
    "故事叙述": "Rewrite the text below as a natural narrative paragraph",
    "邮件风格": "Rewrite the text below in email body style",
    "备忘录": "Rewrite the text below in work memo style",
}


def build_rewrite_prompt(style, text, n_candidates=1):
    """Build the rewrite prompt.

    The marker is mentioned only when the input already contains it, so the
    model does not inject a marker that was never requested.
    """
    base = REWRITE_STYLES.get(style, "Rewrite the text below")
    has_marker = PAYLOAD_MARKER in text

    # Ask for the same output language as the input. Without this hint an
    # English style prompt on Chinese text tends to produce English output.
    lang_hint = "Output in the same language as the input."

    if n_candidates <= 1:
        if has_marker:
            return ("%s. %s Keep the original meaning and the marker %s "
                    "unchanged:\n%s") % (base, lang_hint, PAYLOAD_MARKER, text)
        return ("%s. %s Keep the original meaning unchanged:\n%s"
                % (base, lang_hint, text))

    if has_marker:
        return (
            "%s. %s Generate %d versions with different phrasing.\n"
            "Requirements:\n"
            "1. Each version must keep the original meaning, especially the marker "
            "%s must be preserved exactly;\n"
            "2. Separate versions with a line of \"---\";\n"
            "3. Output only the rewritten results. No numbering, no explanations.\n\n"
            "Original text:\n%s"
        ) % (base, lang_hint, n_candidates, PAYLOAD_MARKER, text)

    return (
        "%s. %s Generate %d versions with different phrasing.\n"
        "Requirements:\n"
        "1. Each version must keep the original meaning;\n"
        "2. Separate versions with a line of \"---\";\n"
        "3. Output only the rewritten results. No numbering, no explanations.\n\n"
        "Original text:\n%s"
    ) % (base, lang_hint, n_candidates, text)


def parse_candidates(text, expect_count=1):
    if not text:
        return [""]
    if expect_count <= 1:
        return [text.strip()]
    parts = re.split(r"\n\s*-{3,}\s*\n", text)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) < 2:
        parts = re.split(r"\n(?=\s*\d+[\.、])", text)
        parts = [re.sub(r"^\s*\d+[\.、]\s*", "", p).strip()
                 for p in parts if p.strip()]
    return parts if parts else [text.strip()]


def call_openai_compatible(endpoint, api_key, model, prompt, timeout=60):
    url = endpoint.rstrip("/") + "/v1/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("Authorization", "Bearer %s" % api_key)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("Unexpected response structure: %s" % data)


def call_ollama(endpoint, model, prompt, timeout=120):
    url = endpoint.rstrip("/") + "/api/generate"
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("response", "")