"""
Auto-discover OpenAPI and generate Locust tasks.
Locust 2.x best practices: HttpUser, @task, between, events; no deprecated TaskSet.
"""

import json
import os
import random
import re
import string
from urllib.parse import urlencode

from locust import HttpUser, task, between, events

OPENAPI_PATH = os.getenv("OPENAPI_PATH", "/openapi.json")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")  # e.g. "Bearer xxx"
EXTRA_HEADERS = json.loads(os.getenv("EXTRA_HEADERS", "{}"))  # JSON string for custom headers

# 你可以在這裡手動加權重要路徑（正則）
WEIGHT_RULES = [
    (re.compile(r"^/$"), 5),                # 首頁
    (re.compile(r".*(/)?query.*", re.I), 5) # 查詢
]

# 路徑白名單/黑名單（正則）
INCLUDE_PATHS = os.getenv("INCLUDE_PATHS")  # e.g. r"^/|^/query|^/api/.*"
EXCLUDE_PATHS = os.getenv("EXCLUDE_PATHS", r"/docs|/redoc|/metrics|/openapi\.json|/ws")

include_re = re.compile(INCLUDE_PATHS) if INCLUDE_PATHS else None
exclude_re = re.compile(EXCLUDE_PATHS) if EXCLUDE_PATHS else re.compile(r"$^")  # match nothing by default


def _rand_str(n=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def _rand_num(min_v=0, max_v=1000):
    return random.randint(min_v, max_v)


def _sample_from_schema(sch):
    """
    Very small JSON Schema sampler for common scalar/object/array types.
    Uses 'example', 'default', 'enum' when present. Best-effort only.
    """
    if not isinstance(sch, dict):
        return None

    if "example" in sch:
        return sch["example"]
    if "default" in sch:
        return sch["default"]
    if "enum" in sch and sch["enum"]:
        return random.choice(sch["enum"])

    t = sch.get("type")
    fmt = sch.get("format")

    if t == "string":
        if fmt == "uuid":
            return _rand_str(8) + "-" + _rand_str(4) + "-" + _rand_str(4) + "-" + _rand_str(4) + "-" + _rand_str(12)
        if fmt == "date-time":
            return "2025-01-01T00:00:00Z"
        if fmt == "date":
            return "2025-01-01"
        return _rand_str()
    if t == "integer":
        return _rand_num()
    if t == "number":
        return random.random() * 100
    if t == "boolean":
        return random.choice([True, False])
    if t == "array":
        item_sch = sch.get("items", {})
        return [_sample_from_schema(item_sch)]
    if t == "object" or "properties" in sch:
        props = sch.get("properties", {})
        obj = {}
        # include required if defined; else take a few fields
        required = set(sch.get("required", []))
        keys = list(props.keys())
        chosen = keys if required else keys[: min(3, len(keys))]
        for k in chosen:
            obj[k] = _sample_from_schema(props[k])
        return obj

    # fallback
    return _rand_str()


def _build_query_from_params(params_spec):
    """
    Build query dict using parameter specs.
    """
    q = {}
    for p in params_spec:
        if p.get("in") != "query":
            continue
        schema = p.get("schema", {}) or {}
        name = p.get("name", _rand_str(5))
        q[name] = _sample_from_schema(schema)
    return q


def _fill_path_params(path_template, params_spec):
    """
    Replace {id} style params using either enum/default/example or a random value.
    """
    used = {}

    def repl(m):
        name = m.group(1)
        # try find schema
        val = None
        for p in params_spec:
            if p.get("in") == "path" and p.get("name") == name:
                val = _sample_from_schema(p.get("schema", {}))
                break
        if val is None:
            # fallback: numeric id or slug
            val = str(_rand_num()) if "id" in name.lower() else _rand_str()
        used[name] = val
        return str(val)

    path = re.sub(r"\{([^}]+)\}", repl, path_template)
    return path, used


def _headers():
    headers = {}
    if AUTH_TOKEN:
        headers["Authorization"] = AUTH_TOKEN
    headers.update(EXTRA_HEADERS)
    return headers


class APIDiscovery:
    def __init__(self, client):
        self.client = client
        self.endpoints = []  # list of dict: {method, path, weight, has_body, build()}

    def load(self):
        resp = self.client.get(OPENAPI_PATH, name=OPENAPI_PATH)
        if resp.status_code != 200:
            # 如果抓不到 openapi，就只測常見路徑
            self.endpoints = [
                {"method": "GET", "path": "/", "weight": 5},
                {"method": "GET", "path": "/query", "weight": 5},
            ]
            return

        spec = resp.json()
        paths = spec.get("paths", {})

        for path, item in paths.items():
            if exclude_re.search(path):
                continue
            if include_re and not include_re.search(path):
                continue

            for method in list(item.keys()):
                m_lower = method.lower()
                if m_lower not in ("get", "post", "put", "patch", "delete"):
                    continue

                op = item[method] or {}
                params = op.get("parameters", []) + item.get("parameters", [])
                request_body = op.get("requestBody", {})
                has_body = bool(request_body.get("content", {}).get("application/json"))

                weight = 1
                for rx, w in WEIGHT_RULES:
                    if rx.search(path):
                        weight = max(weight, w)

                self.endpoints.append({
                    "method": m_lower.upper(),
                    "path": path,
                    "params": params,
                    "request_body": request_body,
                    "has_body": has_body,
                    "weight": weight,
                })

        # 去掉完全無法組參的 GET（需要 path param 但 schema 不明也算可試）
        if not self.endpoints:
            self.endpoints = [
                {"method": "GET", "path": "/", "weight": 5},
                {"method": "GET", "path": "/query", "weight": 5},
            ]


class AutoUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # 抓一次 OpenAPI
        self.headers = _headers()
        self.discovery = APIDiscovery(self.client)
        self.discovery.load()

        # 動態依權重建立一份可輪詢的工作清單
        self._work = []
        for ep in self.discovery.endpoints:
            self._work.extend([ep] * ep["weight"])

        random.shuffle(self._work)

    @task
    def hit_dynamic(self):
        if not self._work:
            return

        ep = random.choice(self._work)
        method = ep["method"]
        path_template = ep["path"]
        params_spec = ep.get("params", [])
        request_body = ep.get("request_body", {})
        has_body = ep.get("has_body", False)

        # 路徑參數
        path, _ = _fill_path_params(path_template, params_spec)

        # Query 參數
        q = _build_query_from_params(params_spec)
        query_str = f"?{urlencode({k: v for k, v in q.items() if v is not None})}" if q else ""
        url = f"{path}{query_str}"

        # JSON body
        json_payload = None
        if has_body:
            try:
                # 只處理 application/json
                media = request_body["content"]["application/json"]
                sch = media.get("schema", {})
                json_payload = _sample_from_schema(sch)
            except Exception:
                json_payload = {}

        # 發送
        if method == "GET":
            self.client.get(url, headers=self.headers, name=path)
        elif method == "POST":
            self.client.post(url, headers=self.headers, json=json_payload, name=path)
        elif method == "PUT":
            self.client.put(url, headers=self.headers, json=json_payload, name=path)
        elif method == "PATCH":
            self.client.patch(url, headers=self.headers, json=json_payload, name=path)
        elif method == "DELETE":
            self.client.delete(url, headers=self.headers, name=path)


# ===== 可選：在測試開始/結束時印出提示 =====
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    base = environment.parsed_options.host or "(no host set)"
    print(f"[Locust] Test starting. Host={base}. Will fetch {OPENAPI_PATH} to auto-generate tasks.")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("[Locust] Test finished. Check CSV/HTML reports if enabled.")