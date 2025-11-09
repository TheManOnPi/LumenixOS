#!/usr/bin/env python3
from flask import Flask, jsonify, request
from flask_cors import CORS
import platform
import subprocess
import shlex

app = Flask(__name__)
# Allow common local origins (adjust if you host the extension differently)
CORS(app, origins=["http://localhost:8000", "http://127.0.0.1:8000"], supports_credentials=True)

SYSTEM = platform.system().lower()

def run_cmd(cmd, shell=False):
    try:
        if shell:
            proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        else:
            parts = shlex.split(cmd)
            proc = subprocess.run(parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return -1, '', str(e)

@app.route('/networks')
def networks():
    if SYSTEM == 'linux':
        code, out, err = run_cmd('nmcli -t -f SSID,SIGNAL,SECURITY device wifi list')
        if code != 0:
            return jsonify({'error': err or 'nmcli failed'}), 500
        nets = []
        for line in out.splitlines():
            if not line: continue
            ssid, sig, sec = line.split(':') if ':' in line else (line, '', '')
            nets.append({'ssid': ssid, 'signal': sig, 'secured': bool(sec and sec != '--')})
        return jsonify(nets)
    elif SYSTEM == 'darwin':
        code, out, err = run_cmd('/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s', shell=True)
        if code != 0:
            return jsonify({'error': err or 'airport failed'}), 500
        nets = []
        for line in out.splitlines()[1:]:
            parts = line.strip().split()
            if not parts: continue
            ssid = parts[0]
            nets.append({'ssid': ssid, 'signal': None, 'secured': True})
        return jsonify(nets)
    elif SYSTEM == 'windows':
        code, out, err = run_cmd('netsh wlan show networks mode=Bssid')
        if code != 0:
            return jsonify({'error': err or 'netsh failed'}), 500
        nets = []
        for line in out.splitlines():
            line = line.strip()
            if line.startswith('SSID '):
                parts = line.split(':', 1)
                if len(parts) > 1:
                    ssid = parts[1].strip()
                    nets.append({'ssid': ssid, 'signal': None, 'secured': True})
        return jsonify(nets)
    else:
        return jsonify({'error': f'Unsupported OS: {SYSTEM}'}), 500

@app.route('/current')
def current():
    if SYSTEM == 'linux':
        code, out, err = run_cmd('nmcli -t -f ACTIVE,SSID dev wifi')
        if code != 0:
            return jsonify({'error': err or 'nmcli failed'}), 500
        for line in out.splitlines():
            parts = line.split(':')
            if len(parts) >= 2 and parts[0] == 'yes':
                return jsonify({'ssid': parts[1]})
        return jsonify({'ssid': None})
    elif SYSTEM == 'darwin':
        code, out, err = run_cmd("/usr/sbin/networksetup -getairportnetwork $(networksetup -listallhardwareports | awk '/Wi-Fi|AirPort/{getline; print $2}')", shell=True)
        if code != 0:
            return jsonify({'error': err or 'networksetup failed'}), 500
        if ':' in out:
            return jsonify({'ssid': out.split(':',1)[1].strip()})
        return jsonify({'ssid': None})
    elif SYSTEM == 'windows':
        code, out, err = run_cmd('netsh wlan show interfaces')
        if code != 0:
            return jsonify({'error': err or 'netsh failed'}), 500
        for line in out.splitlines():
            line = line.strip()
            if line.lower().startswith('ssid') and ':' in line:
                return jsonify({'ssid': line.split(':',1)[1].strip()})
        return jsonify({'ssid': None})
    else:
        return jsonify({'error': f'Unsupported OS: {SYSTEM}'}), 500

@app.route('/join', methods=['POST'])
def join():
    data = request.get_json(force=True)
    ssid = data.get('ssid')
    password = data.get('password', '')
    if not ssid:
        return jsonify({'error': 'ssid required'}), 400

    if SYSTEM == 'linux':
        cmd = f"nmcli device wifi connect '{ssid}'"
        if password:
            cmd += f" password '{password}'"
        code, out, err = run_cmd(cmd, shell=True)
        if code != 0:
            return jsonify({'error': err or out}), 500
        return jsonify({'ok': True})
    elif SYSTEM == 'darwin':
        dev = 'en0'
        cmd = f"networksetup -setairportnetwork {dev} '{ssid}' '{password}'" if password else f"networksetup -setairportnetwork {dev} '{ssid}'"
        code, out, err = run_cmd(cmd, shell=True)
        if code != 0:
            return jsonify({'error': err or out}), 500
        return jsonify({'ok': True})
    elif SYSTEM == 'windows':
        cmd = f'netsh wlan connect ssid="{ssid}" name="{ssid}"'
        code, out, err = run_cmd(cmd, shell=True)
        if code != 0:
            return jsonify({'error': err or out}), 500
        return jsonify({'ok': True})
    else:
        return jsonify({'error': f'Unsupported OS: {SYSTEM}'}), 500

@app.route('/disconnect', methods=['POST'])
def disconnect():
    if SYSTEM == 'linux':
        code, out, err = run_cmd('nmcli networking off && nmcli networking on', shell=True)
        if code != 0:
            return jsonify({'error': err or out}), 500
        return jsonify({'ok': True})
    elif SYSTEM == 'darwin':
        code, out, err = run_cmd('networksetup -setairportpower en0 off && networksetup -setairportpower en0 on', shell=True)
        if code != 0:
            return jsonify({'error': err or out}), 500
        return jsonify({'ok': True})
    elif SYSTEM == 'windows':
        code, out, err = run_cmd('netsh wlan disconnect', shell=True)
        if code != 0:
            return jsonify({'error': err or out}), 500
        return jsonify({'ok': True})
    else:
        return jsonify({'error': f'Unsupported OS: {SYSTEM}'}), 500

if __name__ == '__main__':
    print('Starting WiFi helper on http://127.0.0.1:8234 — Ctrl+C to stop')
    app.run(host='127.0.0.1', port=8234, debug=False)
