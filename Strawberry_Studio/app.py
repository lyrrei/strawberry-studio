# -*- coding: utf-8 -*-
"""ZEPETO Strawberry Studio - première version Windows."""
from __future__ import annotations
import json, threading, time, urllib.request, urllib.error, webbrowser, sys, os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from connector import ZepetoConnector

# Les ressources sont embarquées dans l'exécutable ; les réglages restent dans AppData.
BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
APP_DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "StrawberryStudio"
APP_DATA.mkdir(parents=True, exist_ok=True)
CONFIG = APP_DATA / "config.json"
DEFAULTS = {
    "theme": {"top": "#ffffff", "bottom": "#ff9fc4", "text": "#171717",
              "name": "#ffffff", "outline": "#ff8ab7", "opacity": 100,
              "font": "Arial", "font_size": 20, "bubble": "Arrondie"},
    "obs": {"host": "127.0.0.1", "port": 4455, "password": ""},
    "presets": {},
    "zepeto_url": "https://web.zepeto.me/fr/live"
}
def load_config():
    if CONFIG.exists():
        try:
            data = json.loads(CONFIG.read_text(encoding="utf-8"))
            for k, v in DEFAULTS.items():
                data.setdefault(k, v.copy() if isinstance(v, dict) else v)
            return data
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULTS))
def save_config(data):
    CONFIG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

STATE = {"messages": [], "fans": [], "points": {}, "donations": [], "events": []}
class LocalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/overlay":
            p = BASE / "overlay.html"
            body = p.read_bytes()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        elif self.path.startswith("/messages"):
            body = json.dumps({"messages": STATE["messages"][-30:]}, ensure_ascii=False).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body)
        else:
            self.send_error(404)
    def do_POST(self):
        if self.path in ("/chat", "/event"):
            try:
                n = int(self.headers.get("Content-Length", "0"))
                item = json.loads(self.rfile.read(n).decode("utf-8"))
                kind = "gift" if self.path == "/event" and item.get("type") == "gift" else "message"
                msg = {"type": kind, "name": str(item.get("name", "Spectateur"))[:80],
                       "text": str(item.get("text", ""))[:500], "avatar": item.get("avatar"),
                       "giftImage": item.get("giftImage"), "time": item.get("time", time.time())}
                if msg["text"]:
                    STATE["messages"].append(msg); STATE["messages"] = STATE["messages"][-100:]
                self.send_response(204); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers()
            except Exception:
                self.send_error(400)
        else: self.send_error(404)
    def log_message(self, *_): pass

def start_local_server():
    try:
        server = ThreadingHTTPServer(("127.0.0.1", 8765), LocalHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return server
    except OSError:
        return None

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🍓 ZEPETO Strawberry Studio")
        self.geometry("1180x780"); self.minsize(980, 650)
        self.configure(bg="#fff7fa")
        self.data = load_config()
        self.server = start_local_server()
        self.zepeto = ZepetoConnector(lambda msg: self.after(0, lambda: self.set_status(msg)))
        self.current = "Connexion ZEPETO"
        self._style()
        self._layout()
        self.show_page(self.current)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _style(self):
        s = ttk.Style(self); s.theme_use("clam")
        s.configure("TFrame", background="#fff7fa")
        s.configure("Card.TFrame", background="#ffffff")
        s.configure("TLabel", background="#fff7fa", foreground="#6f5360", font=("Segoe UI", 10))
        s.configure("Title.TLabel", background="#fff7fa", foreground="#e85b91", font=("Segoe UI", 19, "bold"))
        s.configure("CardTitle.TLabel", background="#ffffff", foreground="#e85b91", font=("Segoe UI", 11, "bold"))
        s.configure("TButton", font=("Segoe UI", 9, "bold"), padding=8, background="#ff9fc4", foreground="#ffffff")
        s.map("TButton", background=[("active", "#f27eac")])
        s.configure("TEntry", padding=7)
        s.configure("TNotebook", background="#fff7fa", borderwidth=0)
        s.configure("TNotebook.Tab", padding=(14, 8), background="#ffe8f0", foreground="#a56c82")
        s.map("TNotebook.Tab", background=[("selected", "#ff9fc4")], foreground=[("selected", "#ffffff")])
        s.configure("Horizontal.TScale", background="#ffffff")

    def _layout(self):
        header = tk.Frame(self, bg="#f7d2e2", height=62); header.pack(fill="x")
        tk.Label(header, text="🍓  STRAWBERRY STUDIO", bg="#f7d2e2", fg="#9b4568",
                 font=("Segoe UI", 17, "bold")).pack(side="left", padx=22, pady=14)
        tk.Label(header, text="Ton espace créateur ZEPETO", bg="#f7d2e2", fg="#9b4568",
                 font=("Segoe UI", 10)).pack(side="left", padx=8)
        self.status = tk.Label(header, text="● Serveur local prêt", bg="#f7d2e2", fg="#27845d",
                               font=("Segoe UI", 9, "bold")); self.status.pack(side="right", padx=20)
        body = tk.Frame(self, bg="#fff7fa"); body.pack(fill="both", expand=True)
        nav = tk.Frame(body, bg="#ffffff", width=205); nav.pack(side="left", fill="y")
        nav.pack_propagate(False)
        tk.Label(nav, text="ESPACE CRÉATEUR", bg="#ffffff", fg="#c18da2",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=18, pady=(22,10))
        self.nav_buttons = {}
        items = [("Connexion ZEPETO","🍓"),("Design du chat","💬"),("Cadeaux & dons","🎁"),("Mini-jeux","🎮"),
                 ("Spectateurs","👥"),("Gestion des fans","💗"),("Émojis personnalisés","☺"),
                 ("Points & TTS","🔊"),("Widgets OBS","🖥"),("Configuration","⚙")]
        for label, icon in items:
            b = tk.Button(nav, text=f"  {icon}   {label}", anchor="w", relief="flat",
                          bd=0, bg="#ffffff", fg="#987c88", activebackground="#ffe8f0",
                          activeforeground="#e85b91", font=("Segoe UI", 10, "bold"),
                          command=lambda x=label: self.show_page(x))
            b.pack(fill="x", padx=10, pady=3, ipady=9); self.nav_buttons[label] = b
        tk.Label(nav, text="STRAWBERRY • BETA 0.3", bg="#ffffff", fg="#d4a9b9",
                 font=("Segoe UI", 8)).pack(side="bottom", pady=18)
        self.content = tk.Frame(body, bg="#fff7fa"); self.content.pack(side="left", fill="both", expand=True, padx=22, pady=20)

    def show_page(self, name):
        self.current = name
        for label, b in self.nav_buttons.items():
            b.configure(bg="#ffe8f0" if label == name else "#ffffff",
                        fg="#e85b91" if label == name else "#987c88")
        for w in self.content.winfo_children(): w.destroy()
        pages = {"Connexion ZEPETO":self.page_zepeto, "Design du chat":self.page_chat, "Cadeaux & dons":self.page_donations,
                 "Mini-jeux":self.page_games, "Spectateurs":self.page_viewers,
                 "Gestion des fans":self.page_fans, "Émojis personnalisés":self.page_emojis,
                 "Points & TTS":self.page_tts, "Widgets OBS":self.page_obs,
                 "Configuration":self.page_config}
        pages[name]()

    def heading(self, title, desc):
        ttk.Label(self.content, text=title, style="Title.TLabel").pack(anchor="w")
        ttk.Label(self.content, text=desc).pack(anchor="w", pady=(4,16))
    def card(self, parent=None):
        f=tk.Frame(parent or self.content,bg="#ffffff",highlightbackground="#f7d6e3",highlightthickness=1)
        f.pack(fill="x", pady=7); return f

    def page_zepeto(self):
        self.heading("🍓 Connexion ZEPETO LIVE", "Ouvre ZEPETO LIVE dans une fenêtre dédiée. Strawberry Studio surveille les messages et cadeaux visibles dans le chat.")
        f=self.card()
        tk.Label(f,text="ADRESSE DU CATALOGUE ZEPETO LIVE",bg="white",fg="#e85b91",font=("Segoe UI",10,"bold")).pack(anchor="w",padx=18,pady=(14,6))
        self.zepeto_url=tk.StringVar(value=self.data.get("zepeto_url", "https://web.zepeto.me/fr/live"))
        ttk.Entry(f,textvariable=self.zepeto_url,width=76).pack(anchor="w",padx=18,pady=6)
        row=tk.Frame(f,bg="white"); row.pack(anchor="w",padx=18,pady=10)
        ttk.Button(row,text="🍓 Ouvrir ZEPETO LIVE",command=self.open_zepeto).pack(side="left",padx=(0,8))
        ttk.Button(row,text="Arrêter le connecteur",command=self.zepeto.stop).pack(side="left")
        self.zepeto_info=tk.Label(f,text="Le navigateur sera lancé avec un profil séparé réservé à Strawberry Studio.",bg="white",fg="#8d7180",wraplength=700,justify="left")
        self.zepeto_info.pack(anchor="w",padx=18,pady=(4,14))
        f2=self.card()
        tk.Label(f2,text="ÉVÉNEMENTS REÇUS",bg="white",fg="#e85b91",font=("Segoe UI",10,"bold")).pack(anchor="w",padx=18,pady=(14,6))
        self.zepeto_events=tk.Label(f2,text="En attente du premier message ou cadeau…",bg="white",fg="#8d7180",justify="left",wraplength=700)
        self.zepeto_events.pack(anchor="w",padx=18,pady=(0,14))
        ttk.Button(self.content,text="Enregistrer l'adresse",command=self.save_zepeto_url).pack(anchor="w",pady=8)

    def save_zepeto_url(self):
        self.data["zepeto_url"]=self.zepeto_url.get().strip(); save_config(self.data)
        self.set_status("Adresse ZEPETO enregistrée")

    def open_zepeto(self):
        url=self.zepeto_url.get().strip()
        if not url.startswith("https://") or "zepeto" not in url.lower():
            messagebox.showwarning("Adresse invalide", "Colle l’adresse HTTPS de la page ZEPETO LIVE que tu utilises déjà dans ton navigateur.")
            return
        self.save_zepeto_url()
        if not self.zepeto.open_browser(url):
            messagebox.showerror("Navigateur", "Impossible de lancer Chrome ou Edge. Vérifie qu'il est installé.")

    def page_chat(self):
        self.heading("💬 Design du chat", "Personnalise les bulles qui apparaîtront dans ton overlay OBS.")
        row=tk.Frame(self.content,bg="#fff7fa"); row.pack(fill="x")
        self.preset_name=tk.StringVar()
        ttk.Entry(row,textvariable=self.preset_name,width=22).pack(side="left",padx=(0,8))
        ttk.Button(row,text="Enregistrer le thème",command=self.save_preset).pack(side="left",padx=4)
        self.preset_var=tk.StringVar()
        self.preset_combo=ttk.Combobox(row,textvariable=self.preset_var,state="readonly",width=24,
                                       values=list(self.data["presets"].keys()))
        self.preset_combo.pack(side="left",padx=6)
        ttk.Button(row,text="Charger",command=self.load_preset).pack(side="left")
        panel=self.card()
        tk.Label(panel,text="APERÇU EN DIRECT",bg="white",fg="#e85b91",font=("Segoe UI",10,"bold")).pack(anchor="w",padx=18,pady=(14,4))
        self.preview=tk.Label(panel,text="Bonjour et bienvenue sur mon live ! 🍓",bg="#ff9fc4",fg="#171717",
                              font=("Segoe UI",15,"bold"),padx=24,pady=18,wraplength=560)
        self.preview.pack(anchor="w",padx=24,pady=(8,18))
        opts=self.card()
        tk.Label(opts,text="STYLE DE LA BULLE",bg="white",fg="#e85b91",font=("Segoe UI",10,"bold")).pack(anchor="w",padx=18,pady=(14,8))
        grid=tk.Frame(opts,bg="white"); grid.pack(fill="x",padx=18,pady=4)
        self.colors={}
        for i,(key,label) in enumerate([("top","Couleur haute"),("bottom","Couleur basse"),("text","Texte"),("name","Pseudo"),("outline","Contour")]):
            tk.Label(grid,text=label,bg="white",fg="#6f5360").grid(row=i,column=0,sticky="w",pady=5)
            val=tk.StringVar(value=self.data["theme"][key]); self.colors[key]=val
            ent=ttk.Entry(grid,textvariable=val,width=12); ent.grid(row=i,column=1,sticky="w",padx=12)
            ttk.Button(grid,text="Choisir…",command=lambda k=key:self.pick_color(k)).grid(row=i,column=2,sticky="w")
        tk.Label(grid,text="Forme",bg="white",fg="#6f5360").grid(row=0,column=3,padx=(28,8))
        self.shape=tk.StringVar(value=self.data["theme"]["bubble"])
        ttk.Combobox(grid,textvariable=self.shape,values=["Arrondie","Nuage","Chat","Carrée","Transparente"],state="readonly",width=16).grid(row=0,column=4)
        tk.Label(grid,text="Police",bg="white",fg="#6f5360").grid(row=1,column=3,padx=(28,8))
        self.font=tk.StringVar(value=self.data["theme"]["font"])
        ttk.Combobox(grid,textvariable=self.font,values=["Arial","Segoe UI","Comic Sans MS","Trebuchet MS","Georgia"],width=16).grid(row=1,column=4)
        tk.Label(grid,text="Taille",bg="white",fg="#6f5360").grid(row=2,column=3,padx=(28,8))
        self.font_size=tk.IntVar(value=self.data["theme"]["font_size"])
        ttk.Spinbox(grid,from_=10,to=40,textvariable=self.font_size,width=8).grid(row=2,column=4,sticky="w")
        tk.Label(grid,text="Opacité",bg="white",fg="#6f5360").grid(row=3,column=3,padx=(28,8))
        self.opacity=tk.IntVar(value=self.data["theme"]["opacity"])
        ttk.Scale(grid,from_=10,to=100,variable=self.opacity,orient="horizontal",length=140,command=lambda *_:self.update_preview()).grid(row=3,column=4)
        ttk.Button(opts,text="Appliquer les modifications",command=self.apply_theme).pack(anchor="e",padx=18,pady=14)
        ttk.Button(self.content,text="💾  Enregistrer le style et actualiser l'overlay",command=self.apply_theme).pack(anchor="e",pady=8)

    def pick_color(self,key):
        c=colorchooser.askcolor(self.colors[key].get(),title="Choisir une couleur")
        if c[1]: self.colors[key].set(c[1]); self.update_preview()
    def theme_values(self):
        t={k:v.get() for k,v in self.colors.items()}
        t.update({"bubble":self.shape.get(),"font":self.font.get(),"font_size":int(self.font_size.get()),"opacity":int(self.opacity.get())})
        return t
    def update_preview(self):
        if hasattr(self,"preview"):
            t=self.theme_values()
            self.preview.configure(bg=t["bottom"],fg=t["text"],font=(t["font"],t["font_size"],"bold"))
    def apply_theme(self):
        self.data["theme"]=self.theme_values(); save_config(self.data); self.update_preview()
        self.set_status("Style enregistré • overlay actualisé")
    def save_preset(self):
        name=self.preset_name.get().strip()
        if not name: messagebox.showinfo("Thème","Donne un nom à ton thème."); return
        self.data["presets"][name]=self.theme_values(); save_config(self.data)
        self.preset_combo.configure(values=list(self.data["presets"].keys())); self.preset_var.set(name)
        self.set_status(f"Thème « {name} » enregistré")
    def load_preset(self):
        name=self.preset_var.get()
        if name not in self.data["presets"]: return
        t=self.data["presets"][name]
        for k in self.colors: self.colors[k].set(t.get(k,self.colors[k].get()))
        self.shape.set(t.get("bubble","Arrondie")); self.font.set(t.get("font","Arial"))
        self.font_size.set(t.get("font_size",20)); self.opacity.set(t.get("opacity",100)); self.apply_theme()

    def page_obs(self):
        self.heading("🖥 Connexion OBS", "Connecte Strawberry Studio à OBS Studio via OBS WebSocket 5.")
        f=self.card()
        tk.Label(f,text="CONNEXION LOCALE",bg="white",fg="#e85b91",font=("Segoe UI",10,"bold")).pack(anchor="w",padx=18,pady=14)
        row=tk.Frame(f,bg="white"); row.pack(anchor="w",padx=18,pady=4)
        self.obs_host=tk.StringVar(value=self.data["obs"]["host"]); self.obs_port=tk.IntVar(value=self.data["obs"]["port"])
        self.obs_password=tk.StringVar(value=self.data["obs"]["password"])
        for label,var,width,show in [("Adresse",self.obs_host,18,""),("Port",self.obs_port,8,""),("Mot de passe OBS",self.obs_password,22,"•")]:
            tk.Label(row,text=label,bg="white",fg="#6f5360").pack(side="left",padx=(0,5))
            ttk.Entry(row,textvariable=var,width=width,show=show).pack(side="left",padx=(0,14))
        ttk.Button(f,text="Tester la connexion",command=self.test_obs).pack(anchor="w",padx=18,pady=12)
        self.obs_result=tk.Label(f,text="Non connecté",bg="white",fg="#a17c8b"); self.obs_result.pack(anchor="w",padx=18,pady=(0,14))
        f2=self.card()
        tk.Label(f2,text="OVERLAY POUR OBS",bg="white",fg="#e85b91",font=("Segoe UI",10,"bold")).pack(anchor="w",padx=18,pady=12)
        tk.Label(f2,text="Ajoute une source « Navigateur » dans OBS et utilise cette adresse :",bg="white",fg="#6f5360").pack(anchor="w",padx=18)
        self.url=tk.StringVar(value="http://127.0.0.1:8765/overlay")
        ttk.Entry(f2,textvariable=self.url,width=48).pack(anchor="w",padx=18,pady=8)
        ttk.Button(f2,text="Copier l'adresse",command=lambda:self.copy(self.url.get())).pack(anchor="w",padx=18,pady=(0,14))
        ttk.Button(self.content,text="Ouvrir l'aperçu de l'overlay",command=lambda:webbrowser.open(self.url.get())).pack(anchor="w",pady=6)
        ttk.Button(self.content,text="Enregistrer les paramètres OBS",command=self.save_obs).pack(anchor="w",pady=6)
    def save_obs(self):
        self.data["obs"]={"host":self.obs_host.get(),"port":int(self.obs_port.get()),"password":self.obs_password.get()}
        save_config(self.data); self.set_status("Paramètres OBS enregistrés")
    def test_obs(self):
        self.save_obs()
        try:
            import obsws_python as obs
            c=obs.ReqClient(host=self.obs_host.get(),port=int(self.obs_port.get()),password=self.obs_password.get(),timeout=3)
            v=c.get_version()
            self.obs_result.configure(text=f"Connecté à OBS {v.obs_version} • WebSocket {v.obs_web_socket_version}",fg="#27845d")
        except ImportError:
            self.obs_result.configure(text="Module OBS absent : installe les dépendances avec installer.bat",fg="#c17b22")
        except Exception as e:
            self.obs_result.configure(text=f"Connexion impossible : {e}",fg="#c15c76")

    def page_donations(self):
        self.heading("🎁 Cadeaux & dons", "Prépare les alertes de soutien et les actions associées.")
        self.simple_table(["Nom du cadeau","Message d'alerte","Action"],["Rose","Merci pour ton cadeau ! 🌹","Afficher une alerte"])
        ttk.Button(self.content,text="Ajouter une règle de cadeau",command=lambda:self.add_rule("cadeau")).pack(anchor="w",pady=10)
        tk.Label(self.content,text="La réception automatique des cadeaux ZEPETO sera branchée après validation de la source de données du live.",bg="#fff7fa",fg="#a17c8b",wraplength=650).pack(anchor="w")
    def simple_table(self,headers,rows):
        f=self.card(); inner=tk.Frame(f,bg="white"); inner.pack(fill="x",padx=15,pady=14)
        for i,h in enumerate(headers): tk.Label(inner,text=h,bg="white",fg="#e85b91",font=("Segoe UI",9,"bold")).grid(row=0,column=i,sticky="w",padx=12,pady=6)
        for j,row in enumerate(rows,1):
            for i,val in enumerate(row): tk.Label(inner,text=val,bg="white",fg="#6f5360").grid(row=j,column=i,sticky="w",padx=12,pady=6)
    def add_rule(self,kind):
        messagebox.showinfo("Bientôt disponible",f"L'éditeur de règles {kind} sera ajouté dans le prochain module.")
    def page_games(self):
        self.heading("🎮 Mini-jeux", "Des animations interactives pour faire participer ton chat.")
        for title,desc in [("Roue de la chance","Tirage aléatoire parmi les spectateurs participants."),("Quiz","Questions, réponses et classement des participants."),("Défi communautaire","Un objectif collectif avec une jauge de progression.")]:
            f=self.card(); tk.Label(f,text=title,bg="white",fg="#e85b91",font=("Segoe UI",11,"bold")).pack(anchor="w",padx=18,pady=(12,3))
            tk.Label(f,text=desc,bg="white",fg="#6f5360").pack(anchor="w",padx=18,pady=(0,12))
            ttk.Button(f,text="Configurer",command=lambda:self.add_rule(title)).pack(anchor="e",padx=16,pady=(0,12))
    def page_viewers(self):
        self.heading("👥 Spectateurs", "Liste des personnes détectées dans les événements reçus.")
        f=self.card(); tk.Label(f,text="Aucun spectateur reçu pour le moment.",bg="white",fg="#a17c8b").pack(anchor="w",padx=18,pady=22)
        ttk.Button(self.content,text="Envoyer un message de test à l'overlay",command=lambda:self.send_chat("Spectatrice","Coucou les fraises ! 🍓")).pack(anchor="w",pady=8)
    def page_fans(self):
        self.heading("💗 Gestion des fans", "Garde une trace des participants et de leurs points de fidélité.")
        row=tk.Frame(self.content,bg="#fff7fa"); row.pack(anchor="w")
        self.fan_name=tk.StringVar(); ttk.Entry(row,textvariable=self.fan_name,width=28).pack(side="left",padx=(0,8))
        ttk.Button(row,text="Ajouter un fan",command=self.add_fan).pack(side="left")
        self.fan_list=tk.Listbox(self.content,height=14,bg="white",fg="#6f5360",relief="flat",highlightthickness=1,highlightbackground="#f7d6e3")
        self.fan_list.pack(fill="both",expand=True,pady=12)
        for x in STATE["fans"]: self.fan_list.insert("end",x)
    def add_fan(self):
        n=self.fan_name.get().strip()
        if n: STATE["fans"].append(n); self.fan_list.insert("end",n); self.fan_name.set("")
    def page_emojis(self):
        self.heading("☺ Émojis personnalisés", "Associe des raccourcis à tes emojis favoris.")
        self.simple_table(["Raccourci","Emoji","Aperçu"],[(":fraisse:","🍓","🍓"),(":coeur:","💗","💗"),(":clover:","🍀","🍀")])
        ttk.Button(self.content,text="Ajouter un emoji",command=lambda:self.add_rule("emoji")).pack(anchor="w",pady=10)
    def page_tts(self):
        self.heading("🔊 Points & synthèse vocale", "Configure les points de participation et les messages lus à voix haute.")
        f=self.card()
        tk.Label(f,text="SYSTÈME DE POINTS",bg="white",fg="#e85b91",font=("Segoe UI",10,"bold")).pack(anchor="w",padx=18,pady=14)
        tk.Label(f,text="Points attribués par message",bg="white",fg="#6f5360").pack(anchor="w",padx=18)
        self.points_var=tk.IntVar(value=1); ttk.Spinbox(f,from_=0,to=100,textvariable=self.points_var,width=8).pack(anchor="w",padx=18,pady=8)
        ttk.Button(f,text="Enregistrer",command=lambda:self.set_status("Réglage des points enregistré")).pack(anchor="w",padx=18,pady=(0,14))
        f2=self.card(); tk.Label(f2,text="SYNTHÈSE VOCALE",bg="white",fg="#e85b91",font=("Segoe UI",10,"bold")).pack(anchor="w",padx=18,pady=14)
        tk.Label(f2,text="La lecture TTS sera activée lorsqu'une source de messages ZEPETO fiable sera connectée.",bg="white",fg="#6f5360",wraplength=650).pack(anchor="w",padx=18,pady=(0,14))
    def page_config(self):
        self.heading("⚙ Configuration", "Paramètres généraux de Strawberry Studio.")
        f=self.card()
        for line in ["Langue : Français","Thème : Fraise pastel","Serveur local : http://127.0.0.1:8765","Connexion ZEPETO : adaptateur en attente de source autorisée"]:
            tk.Label(f,text="•  "+line,bg="white",fg="#6f5360").pack(anchor="w",padx=18,pady=8)
        tk.Label(self.content,text="Sécurité : ne saisis jamais ton mot de passe ZEPETO dans un outil tiers non officiel. La connexion sera étudiée via une méthode autorisée, sans contourner l'authentification.",bg="#fff7fa",fg="#a17c8b",wraplength=700).pack(anchor="w",pady=12)
    def send_chat(self,name,msg):
        try:
            req=urllib.request.Request("http://127.0.0.1:8765/chat",data=json.dumps({"name":name,"text":msg}).encode(),headers={"Content-Type":"application/json"},method="POST")
            urllib.request.urlopen(req,timeout=2).close(); self.set_status("Message de démonstration envoyé à l'overlay")
        except Exception as e: messagebox.showerror("Overlay",str(e))
    def copy(self,text):
        self.clipboard_clear(); self.clipboard_append(text); self.set_status("Adresse copiée")
    def set_status(self,text):
        self.status.configure(text="● "+text,fg="#27845d")
    def on_close(self):
        try:
            self.zepeto.stop()
            self.data["theme"].update({}); save_config(self.data)
            if self.server: self.server.shutdown()
        except Exception: pass
        self.destroy()

if __name__ == "__main__":
    App().mainloop()
