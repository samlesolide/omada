from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/wifi/<action>', methods=['POST'])
def wifi_control(action):
    if action not in ['enable', 'disable']:
        return jsonify({'error': 'Invalid action'}), 400
    try:
        # Appel du script principal (adapter le chemin si besoin)
        result = subprocess.run(
            ['python3', 'omada_ssid_main.py', action],
            capture_output=True, text=True, timeout=30
        )
        return jsonify({
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }), 200 if result.returncode == 0 else 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ssid/<action>', methods=['POST'])
def ssid_filtrage(action):
    if action not in ['enable', 'disable', 'list']:
        return jsonify({'error': 'Invalid action'}), 400
    ssid = request.json.get('ssid') if request.is_json else None
    cmd = ['python3', 'omada_ssid_filtrage.py', action]
    if ssid:
        cmd += ['--ssid', ssid]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        return jsonify({
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }), 200 if result.returncode == 0 else 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005) 