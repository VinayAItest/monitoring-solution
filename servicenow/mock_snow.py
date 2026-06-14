from flask import Flask, request, jsonify
import json, datetime

app = Flask(__name__)
incidents = []

@app.route('/api/now/table/incident', methods=['POST'])
def create_incident():
    data = request.get_json()
    incident = {
        'sys_id': f'INC{len(incidents)+1:07d}',
        'number': f'INC{len(incidents)+1:07d}',
        'short_description': data.get('short_description'),
        'priority': data.get('priority'),
        'urgency': data.get('urgency'),
        'state': 'New',
        'created': datetime.datetime.now().isoformat()
    }
    incidents.append(incident)
    print(f"[INCIDENT CREATED] {incident['number']}: {incident['short_description']}")
    return jsonify({'result': incident}), 201

@app.route('/api/now/table/incident', methods=['GET'])
def list_incidents():
    return jsonify({'result': incidents})

@app.route('/incidents', methods=['GET'])
def view_incidents():
    html = '<h2>Mock ServiceNow Incidents</h2><table border=1>'
    html += '<tr><th>Number</th><th>Description</th><th>Priority</th><th>State</th><th>Created</th></tr>'
    for i in incidents:
        html += f"<tr><td>{i['number']}</td><td>{i['short_description']}</td><td>{i['priority']}</td><td>{i['state']}</td><td>{i['created']}</td></tr>"
    html += '</table>'
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
