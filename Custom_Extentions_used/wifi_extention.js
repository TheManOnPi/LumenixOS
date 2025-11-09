(function (Scratch) {
  'use strict';

  if (!Scratch.extensions.unsandboxed) {
    throw new Error('This extension must run unsandboxed');
  }

  const API_BASE = 'http://127.0.0.1:8234';

  class WifiExtension {
    getInfo() {
      return {
        id: 'wifi', // fixed to valid lowercase ID
        name: 'Wi-Fi (local helper)',
        color1: '#1E90FF',
        color2: '#1C86EE',
        color3: '#1874CD',
        blocks: [
          {
            opcode: 'listNetworks',
            blockType: Scratch.BlockType.REPORTER,
            text: 'list available networks'
          },
          {
            opcode: 'currentNetwork',
            blockType: Scratch.BlockType.REPORTER,
            text: 'current network'
          },
          {
            opcode: 'joinNetwork',
            blockType: Scratch.BlockType.COMMAND,
            text: 'join network [SSID] password [PASSWORD]',
            arguments: {
              SSID: { type: Scratch.ArgumentType.STRING, defaultValue: '' },
              PASSWORD: { type: Scratch.ArgumentType.STRING, defaultValue: '' }
            }
          },
          {
            opcode: 'disconnect',
            blockType: Scratch.BlockType.COMMAND,
            text: 'disconnect wifi'
          }
        ]
      };
    }

    async _fetchJSON(path, options = {}) {
      const url = API_BASE + path;
      try {
        const resp = await Scratch.fetch(url, options);
        if (!resp.ok) {
          const text = await resp.text();
          console.error('WiFi helper error:', resp.status, text);
          return `ERROR: ${resp.status} ${text}`;
        }
        const data = await resp.json();
        return data;
      } catch (e) {
        console.error('Network error when contacting WiFi helper:', e);
        return `ERROR: ${e.message}`;
      }
    }

    async listNetworks() {
      const r = await this._fetchJSON('/networks');
      if (typeof r === 'string') return r;
      if (!Array.isArray(r)) return 'ERROR: unexpected response';
      return r.map(n => n.ssid + (n.secured ? ' (secure)' : '')).join(', ');
    }

    async currentNetwork() {
      const r = await this._fetchJSON('/current');
      if (typeof r === 'string') return r;
      if (!r || !r.ssid) return 'NONE';
      return r.ssid;
    }

    async joinNetwork(args) {
      const { SSID, PASSWORD } = args;
      const body = JSON.stringify({ ssid: String(SSID), password: String(PASSWORD) });
      const r = await this._fetchJSON('/join', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body
      });
      if (typeof r === 'string') return r;
      return;
    }

    async disconnect() {
      await this._fetchJSON('/disconnect', { method: 'POST' });
    }
  }

  // correct instantiation and registration
  Scratch.extensions.register(new WifiExtension());
})(Scratch);
