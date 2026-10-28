from modules.base import wrap_errors


@wrap_errors
def run(vco, eid, params):
    route_limit = int(params.get("route_limit", 256))

    rt_params = {
        "enterpriseId": eid,
        "filter": {
            "limit": route_limit,
            "rules": [{"field": "ipVersion", "op": "is", "values": ["IPv4"]}],
        },
    }

    resp_data, req_payload = vco.rpc_call(
        "enterprise/getEnterpriseRouteTable",
        rt_params, call_id=30, timeout=60,
    )

    result = {
        "success": True,
        "errors": [],
        "_request": {"url": vco.rpc_url, "payload": req_payload},
        "_response": resp_data,
    }

    rt_inner = resp_data
    if isinstance(resp_data, dict) and "result" in resp_data:
        rt_inner = resp_data["result"]
    if isinstance(rt_inner, dict):
        result["route_table"] = rt_inner.get("data", rt_inner.get("routes", []))
    elif isinstance(rt_inner, list):
        result["route_table"] = rt_inner
    else:
        result["route_table"] = []

    return result
