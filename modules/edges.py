from modules.base import as_list, wrap_errors


@wrap_errors
def run(vco, eid, params):
    data, req_info = vco.rest_post("enterprise/getEnterpriseEdges", {"enterpriseId": eid})
    edges = []
    for edge in as_list(data):
        if not isinstance(edge, dict):
            continue
        edges.append({
            "name": edge.get("name"),
            "edgeState": edge.get("edgeState"),
            "logicalId": edge.get("logicalId"),
            "edgeId": edge.get("id"),
            "serialNumber": edge.get("serialNumber", ""),
            "modelNumber": edge.get("modelNumber", ""),
            "softwareVersion": edge.get("softwareVersion", ""),
        })
    return {
        "success": True,
        "errors": [],
        "edges": edges,
        "_request": req_info,
        "_response": data,
    }
