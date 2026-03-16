from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


DEFAULT_MASSIVE_BASE_URL = "https://api.massive.com"


@dataclass(frozen=True, slots=True)
class MassiveConfig:
    api_key: str
    base_url: str
    access_key_id: str | None = None
    secret_access_key: str | None = None
    s3_endpoint: str | None = None
    bucket: str | None = None

    def safe_summary(self) -> dict[str, str | bool | None]:
        return {
            "base_url": self.base_url,
            "has_api_key": bool(self.api_key),
            "has_access_key_id": bool(self.access_key_id),
            "has_secret_access_key": bool(self.secret_access_key),
            "s3_endpoint": self.s3_endpoint,
            "bucket": self.bucket,
        }


def load_massive_config(repo_root: Path, env: dict[str, str] | None = None) -> MassiveConfig:
    merged_env = {**_load_env_file(repo_root / ".env"), **os.environ}
    if env:
        merged_env.update(env)

    api_key = merged_env.get("MASSIVE_API_KEY")
    if not api_key:
        raise ValueError("MASSIVE_API_KEY is required for the Massive backfill workflow.")

    return MassiveConfig(
        api_key=api_key,
        base_url=merged_env.get("MASSIVE_BASE_URL", DEFAULT_MASSIVE_BASE_URL).rstrip("/"),
        access_key_id=merged_env.get("MASSIVE_ACCESS_KEY_ID"),
        secret_access_key=merged_env.get("MASSIVE_SECRET_ACCESS_KEY"),
        s3_endpoint=merged_env.get("MASSIVE_S3_ENDPOINT"),
        bucket=merged_env.get("MASSIVE_BUCKET"),
    )


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("//"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values
