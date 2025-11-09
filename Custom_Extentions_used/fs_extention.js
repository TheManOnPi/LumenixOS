(function (Scratch) {
  'use strict';
  if (!Scratch.extensions.unsandboxed) {
    throw new Error('Filesystem extension must run unsandboxed');
  }

  const BASE_URL = 'http://127.0.0.1:8765';

  // Helper for safe JSON and Base64 handling
  function decodeBase64Array(base64String) {
    try {
      const json = atob(base64String);
      const parsed = JSON.parse(json);
      if (Array.isArray(parsed)) return parsed;
      return [];
    } catch (e) {
      console.error('Base64 decode failed:', e);
      return [];
    }
  }

  async function request(method, path, data = null, headers = {}) {
    const options = { method, headers };
    if (data) {
      options.body = JSON.stringify(data);
      options.headers['Content-Type'] = 'application/json';
    }
    try {
      const response = await fetch(`${BASE_URL}${path}`, options);
      return await response.json();
    } catch (e) {
      console.error('Request failed:', e);
      return { ok: false, error: e.message };
    }
  }

  class FilesystemExtension {
    getInfo() {
      return {
        id: 'filesystemlocal',
        name: 'Filesystem',
        color1: '#2d89ef',
        color2: '#1b5fbd',
        blocks: [
          {
            opcode: 'listDir',
            blockType: Scratch.BlockType.REPORTER,
            text: 'list directory [PATH]',
            arguments: {
              PATH: { type: Scratch.ArgumentType.STRING, defaultValue: '.' }
            }
          },
          {
            opcode: 'readFile',
            blockType: Scratch.BlockType.REPORTER,
            text: 'read file [PATH]',
            arguments: {
              PATH: { type: Scratch.ArgumentType.STRING, defaultValue: './file.txt' }
            }
          },
          {
            opcode: 'writeFile',
            blockType: Scratch.BlockType.COMMAND,
            text: 'write [TEXT] to [PATH] as binary [BINARY?]',
            arguments: {
              TEXT: { type: Scratch.ArgumentType.STRING },
              PATH: { type: Scratch.ArgumentType.STRING, defaultValue: './file.txt' },
              BINARY: { type: Scratch.ArgumentType.BOOLEAN, defaultValue: false }
            }
          },
          {
            opcode: 'makeDir',
            blockType: Scratch.BlockType.COMMAND,
            text: 'create folder [PATH]',
            arguments: {
              PATH: { type: Scratch.ArgumentType.STRING, defaultValue: './new_folder' }
            }
          },
          {
            opcode: 'deletePath',
            blockType: Scratch.BlockType.COMMAND,
            text: 'delete [PATH] recursive [RECURSIVE?]',
            arguments: {
              PATH: { type: Scratch.ArgumentType.STRING, defaultValue: './old_folder' },
              RECURSIVE: { type: Scratch.ArgumentType.BOOLEAN, defaultValue: false }
            }
          }
        ]
      };
    }

    async listDir({ PATH }) {
      const res = await request('GET', '/list', null, { Dir: PATH });
      if (!res.ok) return ['[ERROR]|List failed||0'];

      const decoded = decodeBase64Array(res.items);
      return decoded.length ? decoded : ['[ERROR]|Empty or invalid list||0'];
    }

    async readFile({ PATH }) {
      const res = await request('GET', '/read', null, { Path: PATH });
      if (!res.ok) return ['[ERROR]|Read failed||0'];

      const decoded = decodeBase64Array(res.content);
      return decoded.length ? decoded : ['[ERROR]|Empty or invalid file||0'];
    }

    async writeFile({ TEXT, PATH, BINARY }) {
      const payload = BINARY
        ? { path: PATH, content: TEXT, binary: true }
        : { path: PATH, content: TEXT };
      const res = await request('POST', '/write', payload);
      if (!res.ok) return ['[ERROR]|Write failed||0'];
      const decoded = decodeBase64Array(res.result);
      return decoded.length ? decoded : ['[INFO]|File written||0'];
    }

    async makeDir({ PATH }) {
      const res = await request('POST', '/mkdir', { path: PATH });
      if (!res.ok) return ['[ERROR]|Make dir failed||0'];
      const decoded = decodeBase64Array(res.result);
      return decoded.length ? decoded : ['[INFO]|Dir created||0'];
    }

    async deletePath({ PATH, RECURSIVE }) {
      const res = await request('POST', '/delete', { path: PATH, recursive: RECURSIVE });
      if (!res.ok) return ['[ERROR]|Delete failed||0'];
      const decoded = decodeBase64Array(res.result);
      return decoded.length ? decoded : ['[INFO]|Deleted||0'];
    }
  }

  Scratch.extensions.register(new FilesystemExtension());
})(Scratch);
