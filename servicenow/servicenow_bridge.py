"""
ServiceNow Bridge
Receives Alertmanager webhook → creates/resolves ServiceNow incidents
"""

from flask import Flask, request, jsonify
import requests
import os
import logging
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── ServiceNow Configuration ────────────────
SNOW_INSTANCE  = os.environ.get("SNOW_INSTANCE", "your-instance.service-now.com")
SNOW_USER      = os.environ.get("SNOW_USER", "admin")
SNOW_PASS      = os.environ.get("SNOW_PASS", "password")
SNOW_API_URL   = f"https://{SNOW_INSTANCE}/api/now/table/incident"

# Priority mapping: Prometheus severity → ServiceNow priority
PRIORITY_MAP = {
    "critical": "1",   # Critical
    "warning":  "3",   # Moderate
    "info":     "4",   # Low
}

URGENCY_MAP = {
    "critical": "1",
    "warning":  "2",
    "info":     "3",
}


def get_snow_headers():
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def create_incident(alert: dict) -> dict:
    """Create a ServiceNow incident from an alert."""
    labels      = alert.get("labels", {})
    annotations = alert.get("annotations", {})
    severity    = labels.get("severity", "warning")

    payload = {
        "short_description": annotations.get("summary", f"Alert: {labels.get('alertname', 'Unknown')}"),
        "description": (
            f"Alert: {labels.get('alertname', 'N/A')}\n"
            f"Severity: {severity}\n"
            f"Instance: {labels.get('instance', 'N/A')}\n"
            f"Details: {annotations.get('description', 'No details')}\n"
            f"Started at: {alert.get('startsAt', 'N/A')}"
        ),
        "urgency":        URGENCY_MAP.get(severity, "2"),
        "priority":       PRIORITY_MAP.get(severity, "3"),
        "category":       "Software",
        "subcategory":    "Application",
        "assignment_group": "DevOps",
        "caller_id":      "prometheus-alertmanager",
        "cmdb_ci":        labels.get("job", "monitoring-app"),
    }

    response = requests.post(
        SNOW_API_URL,
        auth=(SNOW_USER, SNOW_PASS),
        headers=get_snow_headers(),
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    result = response.json().get("result", {})
    logger.info(f"Created incident: {result.get('number')} for alert {labels.get('alertname')}")
    return result


def resolve_incident(alert: dict) -> None:
    """Resolve a ServiceNow incident when alert resolves."""
    labels     = alert.get("labels", {})
    alert_name = labels.get("alertname", "")

    # Find open incidents matching this alert
    search_url = (
        f"{SNOW_API_URL}?sysparm_query="
        f"short_descriptionLIKE{alert_name}^state!=6"
        f"&sysparm_fields=sys_id,number&sysparm_limit=5"
    )

    resp = requests.get(
        search_url,
        auth=(SNOW_USER, SNOW_PASS),
        headers=get_snow_headers(),
        timeout=10,
    )
    resp.raise_for_status()
    incidents = resp.json().get("result", [])

    for incident in incidents:
        sys_id = incident["sys_id"]
        requests.patch(
            f"{SNOW_API_URL}/{sys_id}",
            auth=(SNOW_USER, SNOW_PASS),
            headers=get_snow_headers(),
            json={
                "state":              "6",       # Resolved
                "close_code":         "Solved (Permanently)",
                "close_notes":        f"Alert {alert_name} resolved automatically by Prometheus.",
                "resolved_by":        "prometheus-alertmanager",
            },
            timeout=10,
        )
        logger.info(f"Resolved incident {incident['number']}")


# ─── Webhook endpoint ─────────────────────────
@app.route("/alert", methods=["POST"])
def handle_alert():
    data = request.get_json(force=True)
    logger.info(f"Received {len(data.get('alerts', []))} alert(s), status={data.get('status')}")

    results = []
    for alert in data.get("alerts", []):
        status = alert.get("status", "firing")
        try:
            if status == "firing":
                result = create_incident(alert)
                results.append({"incident": result.get("number"), "action": "created"})
            elif status == "resolved":
                resolve_incident(alert)
                results.append({"action": "resolved", "alert": alert.get("labels", {}).get("alertname")})
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
            results.append({"error": str(e)})

    return jsonify({"processed": len(results), "results": results}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
