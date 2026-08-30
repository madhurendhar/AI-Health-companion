from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

from backend.services.nwdp.config import BASE_URL, NwdpResource


class NwdpClient:
    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout_s: float = 30.0,
        retries: int = 2,
        retry_delay_s: float = 1.0,
    ):
        self.base_url = base_url
        self.timeout_s = timeout_s
        self.retries = retries
        self.retry_delay_s = retry_delay_s

    def _filters(self, res: NwdpResource) -> dict[str, str]:
        return {"State": res.state, "District": res.district, "Agency": res.agency}

    def search(
        self,
        res: NwdpResource,
        *,
        limit: int = 100,
        offset: int = 0,
        sort: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "resource_id": res.resource_id,
            "filters": json.dumps(self._filters(res)),
            "limit": limit,
            "offset": offset,
        }
        if sort:
            params["sort"] = sort
        last_exc: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_s) as client:
                    r = client.get(self.base_url, params=params)
                    r.raise_for_status()
                    body = r.json()
                if not body.get("success"):
                    raise RuntimeError(f"NWDP error: {body.get('error')}")
                return body["result"]
            except Exception as exc:
                last_exc = exc
                if attempt < self.retries:
                    time.sleep(self.retry_delay_s * (attempt + 1))
        raise last_exc  # type: ignore[misc]

    def fetch_all(self, res: NwdpResource, *, page_size: int = 500, max_records: int | None = None) -> list[dict]:
        offset = 0
        all_recs: list[dict] = []
        while True:
            result = self.search(res, limit=page_size, offset=offset)
            records = result.get("records") or []
            if not records:
                break
            all_recs.extend(records)
            if max_records and len(all_recs) >= max_records:
                return all_recs[:max_records]
            total = result.get("total")
            offset += len(records)
            if total is not None and offset >= total:
                break
            if len(records) < page_size:
                break
        return all_recs

    def fetch_recent(self, res: NwdpResource, *, limit: int = 500) -> list[dict]:
        result = self.search(res, limit=limit, sort="Data Acquisition Time desc")
        records = result.get("records") or []
        records.reverse()
        return records


class FileCache:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, key: str) -> Path:
        safe = key.replace("/", "_").replace(" ", "_")
        return self.root / f"{safe}.json"

    def get(self, key: str, ttl_s: float) -> dict | None:
        p = self.path(key)
        if not p.exists():
            return None
        age = time.time() - p.stat().st_mtime
        if age > ttl_s:
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def set(self, key: str, payload: dict) -> None:
        p = self.path(key)
        payload = {**payload, "cached_at_s": time.time()}
        p.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def get_stale(self, key: str) -> dict | None:
        p = self.path(key)
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))
