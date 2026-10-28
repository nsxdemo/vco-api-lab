import json
import requests
from urllib.parse import urlparse


class VCOClient:
    def __init__(self, host, token, verify_ssl=True):
        host = host.strip().rstrip("/")
        if host.startswith("http://") or host.startswith("https://"):
            parsed = urlparse(host)
            self.rest_url = f"{parsed.scheme}://{parsed.netloc}/portal/rest"
            self.rpc_url = f"{parsed.scheme}://{parsed.netloc}/portal/"
        else:
            self.rest_url = f"https://{host}/portal/rest"
            self.rpc_url = f"https://{host}/portal/"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {token}",
        }
        self.verify_ssl = verify_ssl

    def rest_post(self, endpoint, payload, timeout=30):
        url = f"{self.rest_url}/{endpoint}"
        resp = requests.post(
            url, json=payload, headers=self.headers,
            verify=self.verify_ssl, timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json(), {"url": url, "payload": payload}

    def rpc_call(self, method, params, call_id=1, timeout=60):
        payload = {
            "id": call_id,
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        resp = requests.post(
            self.rpc_url, json=payload, headers=self.headers,
            verify=self.verify_ssl, timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json(), payload


def as_list(data):
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, ValueError):
            return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


def wrap_errors(func):
    def wrapper(vco, eid, params):
        try:
            return func(vco, eid, params)
        except requests.exceptions.SSLError as exc:
            return {"success": False, "errors": [f"SSL verification failed: {exc}"]}
        except requests.exceptions.ConnectionError as exc:
            return {"success": False, "errors": [f"Connection failed: {exc}"]}
        except requests.exceptions.HTTPError as exc:
            body = exc.response.text[:500] if exc.response is not None else ""
            return {"success": False, "errors": [f"HTTP {exc.response.status_code}: {body}"]}
        except Exception as exc:
            return {"success": False, "errors": [str(exc)]}
    return wrapper
