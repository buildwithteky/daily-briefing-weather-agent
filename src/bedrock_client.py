"""Amazon Bedrock via the Converse API (works across model providers)."""
from __future__ import annotations

from .config import Config
from .utils import log, timed


class BedrockClient:
    def __init__(self, cfg: Config):
        import boto3  # imported lazily so --no-ai works without boto3
        from botocore.config import Config as BotoConfig
        self.cfg = cfg
        self.client = boto3.client(
            "bedrock-runtime", region_name=cfg.bedrock_region,
            config=BotoConfig(read_timeout=60, retries={"max_attempts": 3, "mode": "standard"}))

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        with timed("bedrock.invoke", model_id=self.cfg.model_id, region=self.cfg.bedrock_region):
            resp = self.client.converse(
                modelId=self.cfg.model_id,
                system=[{"text": system_prompt}],
                messages=[{"role": "user", "content": [{"text": user_prompt}]}],
                inferenceConfig={"maxTokens": self.cfg.max_tokens,
                                 "temperature": self.cfg.temperature},
            )
        usage = resp.get("usage", {})
        log("bedrock.usage", input_tokens=usage.get("inputTokens"),
            output_tokens=usage.get("outputTokens"), stop_reason=resp.get("stopReason"))
        parts = resp["output"]["message"]["content"]
        return "".join(p.get("text", "") for p in parts).strip()
