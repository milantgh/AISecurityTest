# -*- coding: utf-8 -*-
"""
OpenAI-compatible target adapter
Supports OpenAI/DeepSeek/Moonshot/self-hosted OpenAI-compatible gateways, etc.
"""
import json
import time
import urllib.request
import urllib.error

from .base import Target, TargetResponse


class OpenAITarget(Target):
    name = "openai_compat"

    def __init__(self, endpoint, api_key="", model="gpt-4o-mini",
                 system_prompt=None, timeout=60):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt
        self.timeout = timeout

    def send(self, payload, **kwargs):
        # type: (str, **Any) -> TargetResponse
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": payload})

        body = json.dumps({
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
        }).encode("utf-8")

        req = urllib.request.Request(
            self.endpoint + "/v1/chat/completions",
            data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("Authorization", "Bearer %s" % self.api_key)

        t0 = time.time()
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        latency = int((time.time() - t0) * 1000)

        text = ""
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            pass

        usage = data.get("usage", {}) if isinstance(data, dict) else {}

        return TargetResponse(
            text=text,
            raw=data,
            latency_ms=latency,
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
        )