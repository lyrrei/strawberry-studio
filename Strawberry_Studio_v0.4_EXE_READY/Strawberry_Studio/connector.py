# -*- coding: utf-8 -*-
"""Connecteur expérimental Chromium DevTools pour Strawberry Studio.
Il observe uniquement le DOM visible de l'onglet ZEPETO ouvert par l'application.
"""
from __future__ import annotations
import json, threading, time, urllib.request, urllib.error
from pathlib import Path

DEBUG_PORT = 9222
LOCAL_EVENT_URL = "http://127.0.0.1:8765/event"

INJECT_SCRIPT = r'''(() => {
  if (window.__strawberryChatObserver) window.__strawberryChatObserver.disconnect();
  const seen = new WeakSet();
  const post = (event) => fetch('http://127.0.0.1:8765/event', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify(event), mode: 'cors'
  }).catch(() => {});
  function scan(node) {
    if (!(node instanceof Element)) return;
    const rows = [];
    if (node.matches('.w-full.flex.items-start')) rows.push(node);
    if (node.matches('.flex.items-center.w-full.min-h-\\[44px\\]')) rows.push(node);
    rows.push(...node.querySelectorAll('.w-full.flex.items-start'));
    rows.push(...node.querySelectorAll('.flex.items-center.w-full.min-h-\\[44px\\]'));
    for (const row of rows) {
      if (seen.has(row)) continue;
      const body = row.querySelector('.Typography__Body--13--M');
      if (!body) continue;
      const text = (body.innerText || '').trim();
      if (!text) continue;
      const imgs = [...row.querySelectorAll('img')];
      const avatar = imgs[0]?.src || null;
      const giftImg = imgs.length > 1 ? imgs[imgs.length - 1].src : null;
      const username = row.querySelector('.Typography__Caption--12--SB span')?.innerText?.trim() || null;
      const isGift = /a envoyé/i.test(text);
      let giftName = null, giftUser = username;
      if (isGift) {
        const m = text.match(/^(.*?)\s+a envoyé\s+(.+?)\s*$/is);
        if (m) { giftUser = m[1].trim() || username; giftName = m[2].trim().replace(/[.!]+$/, ''); }
      }
      if (!isGift && !username) continue;
      seen.add(row);
      post({type: isGift ? 'gift' : 'message', name: giftUser || username || 'Spectateur',
        text: isGift ? (giftName || text) : text, rawText: text, avatar,
        giftImage: isGift ? giftImg : null, time: Date.now() / 1000});
    }
  }
  window.__strawberryChatObserver = new MutationObserver(records => {
    for (const record of records) for (const node of record.addedNodes) scan(node);
  });
  window.__strawberryChatObserver.observe(document.body, {childList:true, subtree:true});
  console.log('🍓 Strawberry Studio : connecteur chat actif');
})();'''

class ZepetoConnector:
    def __init__(self, status_callback=None):
        self.status_callback = status_callback or (lambda _s: None)
        self.stop_event = threading.Event()
        self.thread = None
        self.chrome_process = None
        self.last_target = None
        self.last_url = None
        self.ws = None
        self.msg_id = 0

    def _status(self, text):
        try: self.status_callback(text)
        except Exception: pass

    @staticmethod
    def find_chrome():
        import os
        candidates = [
            os.path.expandvars(r'%PROGRAMFILES%\\Google\\Chrome\\Application\\chrome.exe'),
            os.path.expandvars(r'%PROGRAMFILES(X86)%\\Google\\Chrome\\Application\\chrome.exe'),
            os.path.expandvars(r'%LOCALAPPDATA%\\Google\\Chrome\\Application\\chrome.exe'),
            os.path.expandvars(r'%PROGRAMFILES%\\Microsoft\\Edge\\Application\\msedge.exe'),
            os.path.expandvars(r'%PROGRAMFILES(X86)%\\Microsoft\\Edge\\Application\\msedge.exe'),
        ]
        for p in candidates:
            if p and Path(p).exists(): return p
        return None

    def open_browser(self, url):
        import subprocess, tempfile
        exe = self.find_chrome()
        if not exe:
            self._status('Chrome / Edge introuvable')
            return False
        profile = Path.home() / 'AppData' / 'Local' / 'StrawberryStudio' / 'ChromiumProfile'
        profile.mkdir(parents=True, exist_ok=True)
        args = [exe, f'--remote-debugging-port={DEBUG_PORT}', '--remote-allow-origins=*',
                f'--user-data-dir={profile}', '--no-first-run', '--no-default-browser-check',
                '--new-window', url]
        try:
            self.chrome_process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._status('Fenêtre ZEPETO LIVE ouverte • connexion en attente')
            self.start()
            return True
        except Exception as e:
            self._status(f'Ouverture impossible : {e}')
            return False

    def start(self):
        if self.thread and self.thread.is_alive(): return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        try:
            if self.ws: self.ws.close()
        except Exception: pass
        self._status('Connecteur arrêté')

    def _targets(self):
        with urllib.request.urlopen(f'http://127.0.0.1:{DEBUG_PORT}/json', timeout=1.5) as r:
            return json.loads(r.read().decode('utf-8'))

    def _run(self):
        try:
            import websocket
        except ImportError:
            self._status('Dépendance websocket-client manquante')
            return
        self._status('Recherche de la fenêtre ZEPETO…')
        while not self.stop_event.is_set():
            try:
                pages = [p for p in self._targets() if p.get('type') == 'page' and p.get('webSocketDebuggerUrl')]
                target = next((p for p in pages if 'zepeto' in p.get('url','').lower()), None)
                if target and (target.get('id') != self.last_target or target.get('url') != self.last_url):
                    try:
                        if self.ws: self.ws.close()
                    except Exception: pass
                    self.ws = websocket.create_connection(target['webSocketDebuggerUrl'], timeout=2,
                                                          origin='http://localhost')
                    self.ws.settimeout(1)
                    self.last_target = target.get('id')
                    self.last_url = target.get('url')
                    self.msg_id = 0
                    self._send_cdp('Runtime.enable')
                    self._send_cdp('Page.enable')
                    self._send_cdp('Runtime.evaluate', {'expression': INJECT_SCRIPT, 'awaitPromise': True})
                    self._status('Connecté à la page ZEPETO • écoute du chat active')
                elif not target:
                    self._status('Ouvre le catalogue ZEPETO LIVE dans la fenêtre Strawberry')
                if self.ws:
                    try:
                        self.ws.recv()
                    except Exception as e:
                        if 'timed out' not in str(e).lower():
                            try: self.ws.close()
                            except Exception: pass
                            self.ws = None; self.last_target = None; self.last_url = None
            except Exception:
                pass
            self.stop_event.wait(1.0)

    def _send_cdp(self, method, params=None):
        self.msg_id += 1
        self.ws.send(json.dumps({'id':self.msg_id, 'method':method, 'params':params or {}}))
