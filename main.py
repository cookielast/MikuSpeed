import json
from flask import Flask, render_template, jsonify, request, Response
import speedtest
import http.client
import time

app = Flask(__name__)

def load_servers():
    with open('servers.json', 'r') as f:
        return json.load(f)

class IP:
    @staticmethod
    def get_ip():
        conn = http.client.HTTPConnection("ifconfig.me")
        conn.request("GET", "/ip")
        response = conn.getresponse()
        return response.read().decode('utf-8')

@app.route('/')
def index():
    servers = load_servers()
    return render_template('index.html', servers=servers)

@app.route('/speedtest', methods=['POST'])
def speedtest_view():
    try:
        server_id = int(request.json.get('server_id'))
        servers = load_servers()
        selected_server = next((s for s in servers if s['id'] == server_id), None)

        if not selected_server:
            return jsonify({'error': 'Server not found'}), 404

        st = speedtest.Speedtest()

        st.get_servers([selected_server['url']])

        ip_address = IP.get_ip()

        ping = st.results.ping

        download_speed = st.download() / 1_000_000

        upload_speed = st.upload() / 1_000_000

        return jsonify({
            'ip': ip_address,
            'ping': round(ping, 2),
            'download': round(download_speed, 2),
            'upload': round(upload_speed, 2),
            'server': selected_server['name']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stream')
def stream():
    def generate():
        st = speedtest.Speedtest()
        st.get_best_server()

        ip_address = IP.get_ip()

        yield f"data: {json.dumps({'ip': ip_address})}\n\n"

        ping = st.results.ping
        yield f"data: {json.dumps({'ping': round(ping, 2)})}\n\n"

        download_speed = st.download() / 1_000_000
        yield f"data: {json.dumps({'download': round(download_speed, 2)})}\n\n"

        upload_speed = st.upload() / 1_000_000
        yield f"data: {json.dumps({'upload': round(upload_speed, 2)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5585)