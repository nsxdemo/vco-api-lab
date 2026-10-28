from datetime import datetime, timedelta, timezone
from modules.base import wrap_errors


@wrap_errors
def run(vco, eid, params):
    lookback_hours = int(params.get("lookback_hours", 144))
    top_n = int(params.get("top_n", 10))

    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=lookback_hours)

    flow_payload = {
        "enterpriseId": eid,
        "interval": {
            "start": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "end": now.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        },
        "viewBy": "application",
        "sort": "totalBytes",
        "metrics": ["totalBytes"],
        "limit": top_n,
    }
    top_apps, flow_req = vco.rest_post(
        "metrics/getEnterpriseFlowMetrics", flow_payload, timeout=60,
    )

    result = {
        "success": True,
        "errors": [],
        "top_apps": top_apps,
        "_request": flow_req,
        "_response": top_apps,
    }

    app_ids = []
    if isinstance(top_apps, list):
        for a in top_apps:
            aid = a.get("applicationId") or a.get("appId") or a.get("id")
            if aid is None:
                val = a.get("name", "")
                try:
                    aid = int(val)
                except (ValueError, TypeError):
                    pass
            if aid is not None:
                app_ids.append(int(aid))

    if app_ids:
        try:
            resp_data, req_payload = vco.rpc_call(
                "configuration/getIdentifiableApplications",
                {"enterpriseId": eid, "applicationIds": app_ids},
                call_id=20, timeout=30,
            )
            result["_request2"] = {"url": vco.rpc_url, "payload": req_payload}
            result["_response2"] = resp_data
            inner = resp_data.get("result", resp_data) if isinstance(resp_data, dict) else resp_data
            app_list = inner.get("applications", inner) if isinstance(inner, dict) else inner
            if isinstance(app_list, list):
                app_map = {}
                for app in app_list:
                    if isinstance(app, dict):
                        aid = app.get("id") or app.get("appId")
                        if aid is not None:
                            app_map[str(aid)] = {
                                "name": app.get("name", ""),
                                "displayName": app.get("displayName", ""),
                            }
                result["app_names"] = app_map
        except Exception as exc:
            result["errors"].append(f"App name lookup: {exc}")

    return result
