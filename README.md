
# VCO Web Dashboard

A lightweight web dashboard for querying Arista SD-WAN VeloCloud Orchestrator (VCO) APIs. Built with Python's standard library HTTP server and a single-page HTML frontend — no frameworks, no build step.

## Features

- **Token-based authentication** — connects to any VCO using an Enterprise Admin API token
- **Enterprise ID display** — shows the Enterprise ID, name, and account number on successful connection
- **Modular design** — each API query is an independent module in `modules/`
- **Raw JSON inspector** — view the exact API request/response for every query
- **Dark mode** — follows system preference automatically

### Modules

| Module | Description | API Endpoint |
|--------|-------------|--------------|
| **Edges** | Lists edge appliances with state, model, software version, serial | `enterprise/getEnterpriseEdges` |
| **Top Applications** | Top apps by bandwidth over a configurable lookback window | `metrics/getEnterpriseFlowMetrics` |
| **Route Table** | IPv4 route table with preferred exits and route type attributes | `enterprise/getEnterpriseRouteTable` |

## Requirements

- Python 3.8+
- `requests` library

## Setup

```bash
git clone https://github.com/nsxdemo/vco-api-lab.git
cd vco-web
pip install requests
```

## Usage

```bash
python3 server.py [--port PORT]
```

Default port is `8080`. Open `http://localhost:8080` in your browser.

### Connecting to a VCO

1. Enter your **API Token** (Enterprise Admin token from the VCO portal)
2. Enter the **VCO Hostname** (e.g., `vco12-usvi1.velocloud.net`)
3. Optionally uncheck **SSL** if the VCO uses a self-signed certificate
4. Click **Connect**

On success, the Enterprise ID badge appears in the top bar and all modules become available.

### Running a Module

1. Select a module in the sidebar
2. Adjust parameters if available (e.g., lookback hours, top N)
3. Click **Run** — results render in the main panel
4. Click **JSON** to inspect the raw API request and response

## Project Structure

```
vco-web/
├── server.py              # HTTP server — serves index.html and /api endpoints
├── index.html             # Single-page frontend (HTML + CSS + JS, no build step)
├── modules/
│   ├── __init__.py
│   ├── base.py            # VCOClient (REST + JSON-RPC), shared helpers
│   ├── edges.py           # Edge list module
│   ├── topapps.py         # Top applications module
│   └── routetable.py      # Route table module
└── README.md
```

### Local Testing

```bash
# Start the server
python3 server.py

# Verify it serves the UI
curl -s http://localhost:8080 | head -5

# Test the connect endpoint (replace with your credentials)
curl -s -X POST http://localhost:8080/api/connect \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_API_TOKEN","vco_url":"YOUR_VCO_HOST","verify_ssl":true}'

# Test a module (replace eid with your Enterprise ID)
curl -s -X POST http://localhost:8080/api/run/edges \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_API_TOKEN","vco_url":"YOUR_VCO_HOST","verify_ssl":true,"eid":123}'
```

Tokens are never stored — they live only in the browser session.
