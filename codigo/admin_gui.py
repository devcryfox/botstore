import os
import json
import uuid
import threading
import customtkinter as ctk
import mysql.connector
import telebot
from tkinter import messagebox, filedialog

# ==========================================
# 🎨 TEMA
# ==========================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "railway_config.json")

def cargar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def guardar_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"No se pudo guardar config: {e}")


# ==========================================
# 🔐 PANTALLA DE CONEXIÓN
# ==========================================
class PantallaConexion(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Conectar a Railway MySQL")
        self.geometry("540x680")
        self.resizable(False, False)
        self.resultado = None

        config = cargar_config()

        # --- Título ---
        ctk.CTkLabel(self, text="🚂 CONEXIÓN A RAILWAY",
                     font=("Roboto", 22, "bold")).pack(pady=(20, 2))
        ctk.CTkLabel(self, text="Usa el host PÚBLICO de Railway, no el interno.",
                     font=("Arial", 11), text_color="#FFD700").pack()

        # --- Ayuda desplegable ---
        self.frame_ayuda_visible = False
        self.btn_ayuda = ctk.CTkButton(
            self, text="❓ ¿Cómo obtengo el host público?",
            command=self._toggle_ayuda,
            fg_color="#2a2a2a", hover_color="#3a3a3a",
            font=("Arial", 11), height=28
        )
        self.btn_ayuda.pack(pady=(4, 0), padx=30, fill="x")

        self.frame_ayuda = ctk.CTkFrame(self, fg_color="#1a1a2e", corner_radius=8)
        self.lbl_ayuda = ctk.CTkLabel(
            self.frame_ayuda,
            text=(
                "1️⃣  Ve a railway.app → tu proyecto → MySQL\n"
                "2️⃣  Clic en la pestaña  'Settings'\n"
                "3️⃣  Activa  'Public Networking'  si está apagado\n"
                "4️⃣  Copia el valor de  'Public URL' ➜ pégalo en Host\n"
                "     (formato: roundhouse.proxy.rlwy.net)\n"
                "5️⃣  El PUERTO público es diferente al 3306 interno\n"
                "     (p.ej. 32785) — cópialo también en Puerto."
            ),
            font=("Consolas", 11),
            text_color="#aaaaff",
            justify="left"
        )
        self.lbl_ayuda.pack(padx=12, pady=8)

        # --- Campos ---
        frame = ctk.CTkFrame(self)
        frame.pack(padx=30, pady=(10, 0), fill="x")

        campos = [
            ("Host público (MYSQLHOST)",       "host",     config.get("host", "")),
            ("Puerto público (MYSQLPORT)",      "port",     config.get("port", "3306")),
            ("Usuario (MYSQLUSER)",             "user",     config.get("user", "root")),
            ("Contraseña (MYSQLPASSWORD)",      "password", config.get("password", "")),
            ("Base de datos (MYSQLDATABASE)",   "database", config.get("database", "railway")),
            ("Token del Bot de Telegram",       "token",    config.get("token", "")),
        ]

        self.entradas = {}
        for label_txt, key, valor in campos:
            ctk.CTkLabel(frame, text=label_txt, anchor="w",
                         font=("Arial", 11)).pack(fill="x", padx=15, pady=(8, 0))
            show = "*" if key == "password" else None
            e = ctk.CTkEntry(frame, show=show)
            e.insert(0, valor)
            e.pack(fill="x", padx=15, pady=(0, 2))
            self.entradas[key] = e

        # --- LED de estado ---
        self.frame_led = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_led.pack(pady=(10, 0))
        self.canvas_led = ctk.CTkCanvas(self.frame_led, width=18, height=18,
                                         bg="#2b2b2b", highlightthickness=0)
        self.canvas_led.pack(side="left", padx=(0, 6))
        self.led = self.canvas_led.create_oval(2, 2, 16, 16, fill="#444444", outline="")
        self.lbl_estado = ctk.CTkLabel(self.frame_led, text="Sin probar",
                                        font=("Arial", 11), text_color="gray")
        self.lbl_estado.pack(side="left")

        # --- Botones ---
        fila = ctk.CTkFrame(self, fg_color="transparent")
        fila.pack(padx=30, fill="x", pady=(8, 4))
        ctk.CTkButton(fila, text="🔍 Probar Conexión",
                      command=self._probar, height=42,
                      fg_color="#2e6b2e", hover_color="#1a4a1a",
                      font=("Arial", 13, "bold")
                      ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.btn_entrar = ctk.CTkButton(fila, text="🔌 Entrar al Panel",
                                         command=self._conectar, height=42,
                                         fg_color="#555", hover_color="#555",
                                         font=("Arial", 13, "bold"), state="disabled")
        self.btn_entrar.pack(side="left", expand=True, fill="x")

        ctk.CTkButton(self, text="Cargar variables de entorno del sistema",
                      command=self._desde_env,
                      height=32, fg_color="#333", hover_color="#1a1a1a",
                      font=("Arial", 11)).pack(padx=30, fill="x", pady=(0, 10))

    def _toggle_ayuda(self):
        if self.frame_ayuda_visible:
            self.frame_ayuda.pack_forget()
            self.frame_ayuda_visible = False
        else:
            self.frame_ayuda.pack(padx=30, pady=(0, 4), fill="x",
                                  before=self.entradas["host"].master)
            self.frame_ayuda_visible = True

    def _desde_env(self):
        mapa = {"host": "MYSQLHOST", "port": "MYSQLPORT", "user": "MYSQLUSER",
                "password": "MYSQLPASSWORD", "database": "MYSQLDATABASE", "token": "TOKEN"}
        for key, env in mapa.items():
            val = os.getenv(env, "")
            self.entradas[key].delete(0, "end")
            self.entradas[key].insert(0, val)
        self.lbl_estado.configure(text="Variables de entorno cargadas.", text_color="cyan")

    def _leer(self):
        return {k: e.get().strip() for k, e in self.entradas.items()}

    def _set_led(self, estado):
        colores = {"ok": "#00FF00", "error": "#FF3333", "probando": "#FFD700", "neutro": "#444444"}
        self.canvas_led.itemconfig(self.led, fill=colores.get(estado, "#444444"))

    def _probar(self):
        d = self._leer()
        if not all([d["host"], d["port"], d["user"], d["password"], d["database"]]):
            self._set_led("error")
            self.lbl_estado.configure(text="⚠️ Completa todos los campos de DB.", text_color="orange")
            return
        self._set_led("probando")
        self.lbl_estado.configure(text="🔄 Probando...", text_color="#FFD700")
        self.btn_entrar.configure(state="disabled", fg_color="#555", hover_color="#555")
        self.update()

        def _test():
            try:
                conn = mysql.connector.connect(
                    host=d["host"], user=d["user"], password=d["password"],
                    database=d["database"], port=int(d["port"]), connection_timeout=8)
                ver = conn.get_server_info()
                conn.close()
                self.after(0, lambda: self._resultado(True, f"✅ Conectado — MySQL {ver}"))
            except Exception as e:
                msg = str(e)
                if "11001" in msg or "Unknown MySQL server host" in msg:
                    msg = "❌ Host no alcanzable — usa el host PÚBLICO de Railway"
                elif "Access denied" in msg:
                    msg = "❌ Usuario o contraseña incorrectos"
                elif "Unknown database" in msg:
                    msg = "❌ La base de datos no existe"
                elif "timed out" in msg or "Can't connect" in msg:
                    msg = "❌ Tiempo agotado — revisa host y puerto"
                else:
                    msg = f"❌ {msg[:100]}"
                self.after(0, lambda m=msg: self._resultado(False, m))

        threading.Thread(target=_test, daemon=True).start()

    def _resultado(self, ok, msg):
        self._set_led("ok" if ok else "error")
        self.lbl_estado.configure(text=msg, text_color="#00FF00" if ok else "#FF4444")
        if ok:
            self.btn_entrar.configure(state="normal", fg_color="#1f538d", hover_color="#14375e")
        else:
            self.btn_entrar.configure(state="disabled", fg_color="#555", hover_color="#555")

    def _conectar(self):
        d = self._leer()
        if not d.get("token"):
            self.lbl_estado.configure(text="⚠️ Falta el Token del Bot.", text_color="orange")
            return
        guardar_config(d)
        self.resultado = d
        self.lbl_estado.configure(text="✅ Entrando al panel...", text_color="#00FF00")
        self.after(300, self.destroy)


# ==========================================
# 🛡️ PANEL PRINCIPAL
# ==========================================
class AdminDashboard(ctk.CTk):

    def __init__(self, config):
        super().__init__()
        self.title("Panel Admin — Bot de Ventas")
        self.geometry("900x680")
        self.minsize(800, 600)

        self.TOKEN = config["token"]
        self.bot = telebot.TeleBot(self.TOKEN)
        self.DB_CONFIG = {
            'host':     config["host"],
            'user':     config["user"],
            'password': config["password"],
            'database': config["database"],
            'port':     int(config["port"])
        }

        self._build_ui()
        self._uid_seleccionado = ""
        self.after(200, self.actualizar_todo)

    # ─── DB ───────────────────────────────
    def conectar_db(self):
        return mysql.connector.connect(**self.DB_CONFIG)

    def _status(self, msg, color="#aaaaaa"):
        self.lbl_statusbar.configure(text=f"  {msg}", text_color=color)

    # ─── UI PRINCIPAL ─────────────────────
    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="🛡️ PANEL DE CONTROL",
                     font=("Roboto", 20, "bold")).pack(side="left", padx=16, pady=10)
        self.lbl_db = ctk.CTkLabel(
            header,
            text=f"🟢 {self.DB_CONFIG['host']}:{self.DB_CONFIG['port']}",
            font=("Consolas", 10), text_color="#00FF00")
        self.lbl_db.pack(side="right", padx=16)

        # Tabs
        self.tabs = ctk.CTkTabview(self, height=520)
        self.tabs.pack(padx=16, pady=(10, 6), fill="both", expand=True)
        for t in ["📦 Inventario", "🔑 Keys", "👥 Clientes", "💰 Créditos", "📢 Broadcast"]:
            self.tabs.add(t)

        self._tab_inventario()
        self._tab_keys()
        self._tab_clientes()
        self._tab_creditos()
        self._tab_broadcast()

        # Barra inferior
        barra = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0, height=36)
        barra.pack(fill="x", side="bottom")
        barra.pack_propagate(False)
        self.lbl_statusbar = ctk.CTkLabel(barra, text="  Listo.", font=("Consolas", 11),
                                           text_color="#888888")
        self.lbl_statusbar.pack(side="left", pady=6)
        ctk.CTkButton(barra, text="🔄 Sincronizar", command=self.actualizar_todo,
                      height=26, width=120, font=("Arial", 11),
                      fg_color="#2a2a2a", hover_color="#3a3a3a"
                      ).pack(side="right", padx=10, pady=5)

    # ─── TAB INVENTARIO ───────────────────
    def _tab_inventario(self):
        tab = self.tabs.tab("📦 Inventario")

        ctk.CTkLabel(tab, text="Stock por Servicio",
                     font=("Arial", 15, "bold")).pack(pady=(10, 4))

        self.txt_stock = ctk.CTkTextbox(
            tab, state="disabled", fg_color="#0a0a0a",
            text_color="#00FF00", font=("Consolas", 13))
        self.txt_stock.pack(padx=16, pady=4, fill="both", expand=True)

        # ── Subir cuentas ──────────────────────────────────────────
        frame_subir = ctk.CTkFrame(tab, fg_color="#1a1a1a", corner_radius=8)
        frame_subir.pack(pady=(4, 2), fill="x", padx=16)

        ctk.CTkLabel(frame_subir, text="📂 Subir cuentas a un servicio",
                     font=("Arial", 12, "bold"), text_color="#FFD700").pack(anchor="w", padx=10, pady=(6, 2))

        caja = ctk.CTkFrame(frame_subir, fg_color="transparent")
        caja.pack(pady=(0, 8), fill="x", padx=10)

        # Dropdown de servicios existentes
        self._servicios_lista = ["(nuevo servicio…)"]
        self.combo_servicio = ctk.CTkComboBox(
            caja,
            values=self._servicios_lista,
            command=self._on_servicio_seleccionado,
            font=("Arial", 12), width=220,
            button_color="#8B4513", button_hover_color="#5C2D0E",
            dropdown_hover_color="#3a2a1a"
        )
        self.combo_servicio.set("Selecciona o escribe servicio")
        self.combo_servicio.pack(side="left", padx=(0, 6))

        self.inp_servicio_nuevo = ctk.CTkEntry(
            caja, placeholder_text="Nombre del nuevo servicio",
            font=("Arial", 12), width=180)
        self.inp_servicio_nuevo.pack(side="left", padx=(0, 8))
        self.inp_servicio_nuevo.pack_forget()  # oculto por defecto

        ctk.CTkButton(caja, text="📂 Subir .txt",
                      command=self._cargar_combos,
                      fg_color="#8B4513", hover_color="#5C2D0E",
                      font=("Arial", 12)).pack(side="right")

        # ── Limpiar entregados ─────────────────────────────────────
        frame_limpiar = ctk.CTkFrame(tab, fg_color="#1a1a1a", corner_radius=8)
        frame_limpiar.pack(pady=(2, 8), fill="x", padx=16)

        ctk.CTkLabel(frame_limpiar, text="🗑️ Limpiar cuentas ya entregadas",
                     font=("Arial", 12, "bold"), text_color="#FF8888").pack(anchor="w", padx=10, pady=(6, 2))

        caja2 = ctk.CTkFrame(frame_limpiar, fg_color="transparent")
        caja2.pack(pady=(0, 8), fill="x", padx=10)

        self.combo_servicio_limpiar = ctk.CTkComboBox(
            caja2,
            values=["(todos los servicios)"],
            font=("Arial", 12), width=240,
            button_color="#5a0000", button_hover_color="#3a0000",
            dropdown_hover_color="#3a0a0a"
        )
        self.combo_servicio_limpiar.set("(todos los servicios)")
        self.combo_servicio_limpiar.pack(side="left", padx=(0, 8))

        ctk.CTkButton(caja2, text="🗑️ Limpiar Entregados",
                      command=self._limpiar_entregados,
                      fg_color="#5a0000", hover_color="#3a0000",
                      font=("Arial", 12)).pack(side="right")

    def _on_servicio_seleccionado(self, valor):
        if valor == "(nuevo servicio…)":
            self.inp_servicio_nuevo.pack(side="left", padx=(0, 8),
                                         before=self.combo_servicio.master.winfo_children()[-1])
        else:
            self.inp_servicio_nuevo.pack_forget()
            self.inp_servicio_nuevo.delete(0, "end")

    def _actualizar_stock(self):
        self.txt_stock.configure(state="normal")
        self.txt_stock.delete("0.0", "end")
        try:
            conn = self.conectar_db()
            cur = conn.cursor()
            cur.execute("""
                SELECT servicio,
                  COUNT(CASE WHEN estado='disponible' THEN 1 END) AS disp,
                  COUNT(CASE WHEN estado='entregado'  THEN 1 END) AS entregado
                FROM combos GROUP BY servicio ORDER BY servicio
            """)
            rows = cur.fetchall()
            if rows:
                self.txt_stock.insert("end", f"{'SERVICIO':<20} {'DISPONIBLE':>10} {'ENTREGADO':>10}\n")
                self.txt_stock.insert("end", "─" * 44 + "\n")
                for serv, disp, ent in rows:
                    self.txt_stock.insert("end", f"/{serv:<19} {disp:>10} {ent:>10}\n")
                # Actualizar dropdowns
                nombres = [r[0] for r in rows]
                self.combo_servicio.configure(values=nombres + ["(nuevo servicio…)"])
                self.combo_servicio_limpiar.configure(values=["(todos los servicios)"] + nombres)
            else:
                self.txt_stock.insert("end", "Sin servicios registrados.\n")
            self._status(f"Stock actualizado — {len(rows)} servicio(s)", "#00FF00")
        except Exception as e:
            self.txt_stock.insert("end", f"❌ Error: {e}\n")
            self._status(f"Error al leer stock: {e}", "#FF4444")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cur.close(); conn.close()
        self.txt_stock.configure(state="disabled")

    def _cargar_combos(self):
        val = self.combo_servicio.get().strip()
        if val == "(nuevo servicio…)" or val == "Selecciona o escribe servicio":
            servicio = self.inp_servicio_nuevo.get().strip().lower()
        else:
            servicio = val.lower()
        if not servicio:
            messagebox.showwarning("Error", "Selecciona un servicio o escribe el nombre del nuevo.")
            return
        ruta = filedialog.askopenfilename(filetypes=[("Archivos TXT", "*.txt")])
        if not ruta:
            return
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                lineas = [l.strip() for l in f if l.strip()]
            conn = self.conectar_db()
            cur = conn.cursor()
            cur.executemany(
                "INSERT INTO combos (servicio, cuenta) VALUES (%s, %s)",
                [(servicio, l) for l in lineas])
            conn.commit()
            messagebox.showinfo("Éxito", f"{len(lineas)} cuentas cargadas para '{servicio}'.")
            self._actualizar_stock()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if 'conn' in locals() and conn.is_connected():
                cur.close(); conn.close()

    def _limpiar_entregados(self):
        val = self.combo_servicio_limpiar.get().strip()
        serv = "" if val == "(todos los servicios)" else val.lower()
        target = f"servicio '{serv}'" if serv else "TODOS los servicios"
        if not messagebox.askyesno("Confirmar", f"¿Eliminar cuentas ya entregadas de {target}?"):
            return
        try:
            conn = self.conectar_db()
            cur = conn.cursor()
            if serv:
                cur.execute("DELETE FROM combos WHERE estado='entregado' AND servicio=%s", (serv,))
            else:
                cur.execute("DELETE FROM combos WHERE estado='entregado'")
            conn.commit()
            n = cur.rowcount
            messagebox.showinfo("Listo", f"{n} registro(s) eliminado(s).")
            self._actualizar_stock()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if 'conn' in locals() and conn.is_connected():
                cur.close(); conn.close()

    # ─── TAB KEYS ─────────────────────────
    def _tab_keys(self):
        tab = self.tabs.tab("🔑 Keys")
        ctk.CTkLabel(tab, text="Llaves de Acceso",
                     font=("Arial", 15, "bold")).pack(pady=(10, 4))

        caja = ctk.CTkFrame(tab, fg_color="transparent")
        caja.pack(pady=4, fill="x", padx=16)
        self.inp_key = ctk.CTkEntry(caja, placeholder_text="Escribe una key o genera aleatoria",
                                     font=("Arial", 12))
        self.inp_key.pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(caja, text="🎲 Generar",
                      command=self._generar_key_aleatoria,
                      fg_color="#4a4a4a", hover_color="#333",
                      width=90, font=("Arial", 12)).pack(side="left", padx=(0, 6))
        ctk.CTkButton(caja, text="➕ Agregar",
                      command=self._agregar_key,
                      fg_color="#228B22", hover_color="#006400",
                      width=90, font=("Arial", 12)).pack(side="right")

        # Generador en lote
        caja2 = ctk.CTkFrame(tab, fg_color="transparent")
        caja2.pack(pady=(0, 4), fill="x", padx=16)
        ctk.CTkLabel(caja2, text="Generar en lote:", font=("Arial", 11)).pack(side="left", padx=(0, 6))
        self.inp_cantidad_keys = ctk.CTkEntry(caja2, placeholder_text="Cantidad", width=80,
                                               font=("Arial", 12))
        self.inp_cantidad_keys.pack(side="left", padx=(0, 6))
        ctk.CTkButton(caja2, text="🎲 Generar Lote",
                      command=self._generar_lote_keys,
                      fg_color="#4a4a4a", hover_color="#333",
                      font=("Arial", 12)).pack(side="left")

        self.panel_keys = ctk.CTkScrollableFrame(tab, fg_color="#0a0a0a")
        self.panel_keys.pack(pady=6, padx=16, fill="both", expand=True)

    def _generar_key_aleatoria(self):
        key = f"KEY-{uuid.uuid4().hex[:12].upper()}"
        self.inp_key.delete(0, "end")
        self.inp_key.insert(0, key)

    def _generar_lote_keys(self):
        try:
            n = int(self.inp_cantidad_keys.get().strip())
            if n < 1 or n > 500:
                messagebox.showwarning("Error", "Ingresa un número entre 1 y 500.")
                return
        except:
            messagebox.showwarning("Error", "Número inválido.")
            return

        keys = [f"KEY-{uuid.uuid4().hex[:12].upper()}" for _ in range(n)]
        try:
            conn = self.conectar_db()
            cur = conn.cursor()
            cur.executemany("INSERT IGNORE INTO claves_acceso (clave) VALUES (%s)",
                            [(k,) for k in keys])
            conn.commit()
            messagebox.showinfo("Éxito", f"{cur.rowcount} keys generadas.")
            self._actualizar_keys()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if 'conn' in locals() and conn.is_connected():
                cur.close(); conn.close()

    def _agregar_key(self):
        key = self.inp_key.get().strip()
        if not key:
            return
        try:
            conn = self.conectar_db()
            cur = conn.cursor()
            cur.execute("INSERT INTO claves_acceso (clave) VALUES (%s)", (key,))
            conn.commit()
            self.inp_key.delete(0, "end")
            self._actualizar_keys()
            self._status(f"Key '{key}' agregada.", "#00FF00")
        except mysql.connector.errors.IntegrityError:
            messagebox.showwarning("Aviso", "Esa key ya existe.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if 'conn' in locals() and conn.is_connected():
                cur.close(); conn.close()

    def _actualizar_keys(self):
        for w in self.panel_keys.winfo_children():
            w.destroy()
        try:
            conn = self.conectar_db()
            cur = conn.cursor()
            cur.execute("SELECT clave FROM claves_acceso ORDER BY id DESC")
            filas = cur.fetchall()
            if not filas:
                ctk.CTkLabel(self.panel_keys, text="No hay keys activas.",
                             text_color="gray").pack()
                return
            ctk.CTkLabel(self.panel_keys,
                         text=f"  {len(filas)} key(s) activa(s) — clic en una para copiarla",
                         font=("Arial", 11), text_color="gray").pack(anchor="w", pady=(0, 4))
            for (clave,) in filas:
                fila = ctk.CTkFrame(self.panel_keys, fg_color="transparent")
                fila.pack(fill="x", pady=2)
                ctk.CTkButton(
                    fila, text=clave, anchor="w",
                    command=lambda c=clave: [self.clipboard_clear(), self.clipboard_append(c),
                                             self._status(f"Copiado: {c}", "#00FF00")],
                    fg_color="#1a1a2e", hover_color="#2a2a4e",
                    font=("Consolas", 12)
                ).pack(side="left", expand=True, fill="x", padx=(0, 6))
                ctk.CTkButton(
                    fila, text="🗑️", width=36,
                    command=lambda c=clave: self._eliminar_key(c),
                    fg_color="#5a0000", hover_color="#3a0000"
                ).pack(side="right")
        except Exception as e:
            self._status(f"Error keys: {e}", "#FF4444")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cur.close(); conn.close()

    def _eliminar_key(self, clave):
        if not messagebox.askyesno("Confirmar", f"¿Eliminar key '{clave}'?"):
            return
        try:
            conn = self.conectar_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM claves_acceso WHERE clave=%s", (clave,))
            conn.commit()
            self._actualizar_keys()
            self._status(f"Key '{clave}' eliminada.", "#FF8800")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if 'conn' in locals() and conn.is_connected():
                cur.close(); conn.close()

    # ─── TAB CLIENTES ─────────────────────
    def _tab_clientes(self):
        tab = self.tabs.tab("👥 Clientes")

        # Header con contador
        hdr = ctk.CTkFrame(tab, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(10, 2))
        ctk.CTkLabel(hdr, text="Usuarios Registrados",
                     font=("Arial", 15, "bold")).pack(side="left")
        self.lbl_total_usuarios = ctk.CTkLabel(hdr, text="",
                     font=("Arial", 12), text_color="#888888")
        self.lbl_total_usuarios.pack(side="right")

        # Buscador
        self.inp_buscar_usuario = ctk.CTkEntry(
            tab, placeholder_text="🔍 Buscar por @usuario o ID…",
            font=("Arial", 12))
        self.inp_buscar_usuario.pack(fill="x", padx=16, pady=(0, 4))
        self.inp_buscar_usuario.bind("<KeyRelease>", lambda e: self._filtrar_usuarios())

        # Lista clickeable
        self.panel_usuarios = ctk.CTkScrollableFrame(tab, fg_color="#0a0a0a")
        self.panel_usuarios.pack(padx=16, pady=4, fill="both", expand=True)

        # Barra de acciones — se auto-rellena al hacer clic en un usuario
        frame_acciones = ctk.CTkFrame(tab, fg_color="#1a1a1a", corner_radius=8)
        frame_acciones.pack(pady=(4, 8), fill="x", padx=16)

        ctk.CTkLabel(frame_acciones, text="Usuario seleccionado:",
                     font=("Arial", 11), text_color="gray").pack(side="left", padx=(10, 4), pady=8)
        self.lbl_usuario_sel = ctk.CTkLabel(frame_acciones, text="—",
                     font=("Arial", 12, "bold"), text_color="#00FF00")
        self.lbl_usuario_sel.pack(side="left", padx=(0, 16), pady=8)

        # ID oculto para operaciones
        self.inp_uid_accion = ctk.CTkEntry(frame_acciones, width=0)  # invisible, solo para guardar el valor
        self._uid_seleccionado = ""

        ctk.CTkButton(frame_acciones, text="🗑️ Eliminar",
                      command=self._eliminar_usuario,
                      fg_color="#5a0000", hover_color="#3a0000",
                      font=("Arial", 12)).pack(side="right", padx=(0, 8), pady=6)
        ctk.CTkButton(frame_acciones, text="📋 Copiar ID",
                      command=self._copiar_uid_seleccionado,
                      fg_color="#2a2a2a", hover_color="#3a3a3a",
                      font=("Arial", 12)).pack(side="right", padx=(0, 4), pady=6)

        self._todos_usuarios = []  # cache para el filtro

    def _copiar_uid_seleccionado(self):
        if self._uid_seleccionado:
            self.clipboard_clear()
            self.clipboard_append(self._uid_seleccionado)
            self._status(f"ID {self._uid_seleccionado} copiado.", "#00FF00")

    def _seleccionar_usuario(self, uid, username, creditos):
        self._uid_seleccionado = str(uid)
        nombre = f"@{username}" if username else f"ID {uid}"
        self.lbl_usuario_sel.configure(
            text=f"{nombre}  —  ${creditos} MXN  (ID: {uid})")
        self._status(f"Seleccionado: {nombre}", "#00FF00")
        # También rellena el campo de créditos
        self.inp_uid_credito.delete(0, "end")
        self.inp_uid_credito.insert(0, str(uid))

    def _filtrar_usuarios(self):
        q = self.inp_buscar_usuario.get().strip().lower().lstrip("@")
        self._dibujar_usuarios([
            u for u in self._todos_usuarios
            if q in str(u[0]).lower() or q in (u[1] or "").lower()
        ] if q else self._todos_usuarios)

    def _dibujar_usuarios(self, filas):
        for w in self.panel_usuarios.winfo_children():
            w.destroy()
        if not filas:
            ctk.CTkLabel(self.panel_usuarios, text="Sin resultados.",
                         text_color="gray").pack()
            return
        for row in filas:
            uid = row[0]
            username = row[1] if len(row) > 1 else None
            creditos = row[2] if len(row) > 2 else row[1]
            nombre = f"@{username}" if username else f"ID {uid}"
            texto = f"  {nombre:<25}  💰 ${creditos} MXN"
            btn = ctk.CTkButton(
                self.panel_usuarios,
                text=texto, anchor="w",
                command=lambda u=uid, n=username, c=creditos: self._seleccionar_usuario(u, n, c),
                fg_color="#0d1a0d", hover_color="#1a2e1a",
                text_color="#00FF00", font=("Consolas", 12),
                corner_radius=4, height=34
            )
            btn.pack(fill="x", pady=2, padx=2)

    def _actualizar_usuarios(self):
        try:
            conn = self.conectar_db()
            cur = conn.cursor()
            # Intentar obtener username; si la columna no existe, usar solo id y créditos
            try:
                cur.execute("""
                    SELECT user_id, username, creditos
                    FROM usuarios_autorizados
                    ORDER BY creditos DESC
                """)
                filas = cur.fetchall()
            except Exception:
                cur.execute("SELECT user_id, creditos FROM usuarios_autorizados ORDER BY creditos DESC")
                raw = cur.fetchall()
                filas = [(r[0], None, r[1]) for r in raw]

            self._todos_usuarios = filas
            self.lbl_total_usuarios.configure(text=f"{len(filas)} usuario(s)")
            self._dibujar_usuarios(filas)
        except Exception as e:
            self._status(f"Error clientes: {e}", "#FF4444")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cur.close(); conn.close()

    def _eliminar_usuario(self):
        uid = self._uid_seleccionado
        if not uid:
            messagebox.showwarning("Error", "Haz clic en un usuario de la lista primero.")
            return
        if not messagebox.askyesno("Confirmar", f"¿Eliminar al usuario {uid}? Perderá su saldo."):
            return
        try:
            conn = self.conectar_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM usuarios_autorizados WHERE user_id=%s", (uid,))
            conn.commit()
            if cur.rowcount == 0:
                messagebox.showwarning("Aviso", f"No se encontró el usuario {uid}.")
            else:
                messagebox.showinfo("Listo", f"Usuario {uid} eliminado.")
                self._uid_seleccionado = ""
                self.lbl_usuario_sel.configure(text="—")
                self._actualizar_usuarios()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if 'conn' in locals() and conn.is_connected():
                cur.close(); conn.close()

    # ─── TAB CRÉDITOS ─────────────────────
    def _tab_creditos(self):
        tab = self.tabs.tab("💰 Créditos")

        # Precio global
        frame_precio = ctk.CTkFrame(tab, corner_radius=8)
        frame_precio.pack(pady=(12, 6), padx=16, fill="x")
        ctk.CTkLabel(frame_precio, text="💲 Precio por Cuenta",
                     font=("Arial", 14, "bold")).pack(pady=(8, 2))
        self.lbl_precio = ctk.CTkLabel(frame_precio, text="Cargando...",
                                        font=("Consolas", 16), text_color="#FFD700")
        self.lbl_precio.pack()
        caja_p = ctk.CTkFrame(frame_precio, fg_color="transparent")
        caja_p.pack(pady=(4, 10))
        self.inp_precio = ctk.CTkEntry(caja_p, placeholder_text="Nuevo precio MXN",
                                        width=160, font=("Arial", 13))
        self.inp_precio.pack(side="left", padx=(0, 8))
        ctk.CTkButton(caja_p, text="💾 Guardar Precio",
                      command=self._guardar_precio,
                      fg_color="#1f538d", hover_color="#14375e",
                      font=("Arial", 13)).pack(side="left")

        ctk.CTkLabel(tab, text="─" * 80, text_color="#333").pack()

        # Cargar / Quitar saldo
        frame_saldo = ctk.CTkFrame(tab, corner_radius=8)
        frame_saldo.pack(pady=6, padx=16, fill="x")
        ctk.CTkLabel(frame_saldo, text="💳 Ajustar Saldo de Usuario",
                     font=("Arial", 14, "bold")).pack(pady=(8, 2))
        ctk.CTkLabel(frame_saldo, text="💡 Haz clic en un usuario en la pestaña Clientes para auto-rellenar",
                     font=("Arial", 10), text_color="#888888").pack(pady=(0, 4))

        caja_s = ctk.CTkFrame(frame_saldo, fg_color="transparent")
        caja_s.pack(pady=(0, 10))
        self.inp_uid_credito = ctk.CTkEntry(caja_s, placeholder_text="ID de usuario",
                                             width=200, font=("Arial", 13))
        self.inp_uid_credito.pack(side="left", padx=(0, 8))
        self.inp_monto = ctk.CTkEntry(caja_s, placeholder_text="Monto MXN",
                                       width=120, font=("Arial", 13))
        self.inp_monto.pack(side="left", padx=(0, 8))
        ctk.CTkButton(caja_s, text="➕ Agregar",
                      command=lambda: self._ajustar_creditos(sumar=True),
                      fg_color="#228B22", hover_color="#006400",
                      font=("Arial", 13)).pack(side="left", padx=(0, 6))
        ctk.CTkButton(caja_s, text="➖ Quitar",
                      command=lambda: self._ajustar_creditos(sumar=False),
                      fg_color="#8B0000", hover_color="#5c0000",
                      font=("Arial", 13)).pack(side="left")

    def _actualizar_precio_label(self):
        try:
            conn = self.conectar_db()
            cur = conn.cursor()
            cur.execute("SELECT valor FROM configuracion_sistema WHERE parametro='precio_cuenta'")
            res = cur.fetchone()
            precio = int(res[0]) if res else "?"
            self.lbl_precio.configure(text=f"${precio} MXN por cuenta")
        except:
            self.lbl_precio.configure(text="Error al leer")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cur.close(); conn.close()

    def _guardar_precio(self):
        val = self.inp_precio.get().strip()
        if not val:
            return
        try:
            nuevo = int(val)
            conn = self.conectar_db()
            cur = conn.cursor()
            cur.execute("""
                UPDATE configuracion_sistema SET valor=%s
                WHERE parametro='precio_cuenta'
            """, (nuevo,))
            conn.commit()
            messagebox.showinfo("Éxito", f"Precio actualizado a ${nuevo} MXN.")
            self.inp_precio.delete(0, "end")
            self._actualizar_precio_label()
            self._status(f"Precio cambiado a ${nuevo} MXN", "#00FF00")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if 'conn' in locals() and conn.is_connected():
                cur.close(); conn.close()

    def _ajustar_creditos(self, sumar=True):
        uid = self.inp_uid_credito.get().strip()
        monto_str = self.inp_monto.get().strip()
        if not uid or not monto_str:
            messagebox.showwarning("Error", "Completa ID y Monto.")
            return
        try:
            monto = int(monto_str)
            conn = self.conectar_db()
            cur = conn.cursor()
            cur.execute("SELECT creditos FROM usuarios_autorizados WHERE user_id=%s", (uid,))
            row = cur.fetchone()
            if not row:
                messagebox.showwarning("Aviso", f"Usuario {uid} no registrado.")
                return
            nuevo = row[0] + monto if sumar else max(0, row[0] - monto)
            cur.execute("UPDATE usuarios_autorizados SET creditos=%s WHERE user_id=%s", (nuevo, uid))
            conn.commit()
            accion = "agregado" if sumar else "quitado"
            messagebox.showinfo("Éxito", f"${monto} {accion}.\nNuevo saldo: ${nuevo} MXN")
            self.inp_monto.delete(0, "end")
            self._actualizar_usuarios()
            self._status(f"Saldo de {uid} → ${nuevo} MXN", "#00FF00")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            if 'conn' in locals() and conn.is_connected():
                cur.close(); conn.close()

    # ─── TAB BROADCAST ────────────────────
    def _tab_broadcast(self):
        tab = self.tabs.tab("📢 Broadcast")
        ctk.CTkLabel(tab, text="Mensaje Masivo a Todos los Usuarios",
                     font=("Arial", 15, "bold")).pack(pady=(10, 4))
        ctk.CTkLabel(tab, text="El mensaje se enviará a todos los usuarios registrados.",
                     font=("Arial", 11), text_color="gray").pack()
        self.txt_broadcast = ctk.CTkTextbox(tab, height=200, font=("Arial", 14))
        self.txt_broadcast.pack(pady=8, padx=16, fill="both", expand=True)
        self.txt_broadcast.bind("<KeyRelease>", self._on_broadcast_key)

        # Contador de caracteres
        pie = ctk.CTkFrame(tab, fg_color="transparent")
        pie.pack(fill="x", padx=16, pady=(0, 4))
        self.lbl_chars = ctk.CTkLabel(pie, text="0 caracteres",
                     font=("Arial", 10), text_color="#666666")
        self.lbl_chars.pack(side="left")
        ctk.CTkLabel(pie, text="Telegram admite hasta 4096 caracteres",
                     font=("Arial", 10), text_color="#444444").pack(side="right")

        ctk.CTkButton(tab, text="🚀 TRANSMITIR AHORA",
                      command=self._iniciar_broadcast,
                      fg_color="#1f538d", hover_color="#14375e",
                      height=48, font=("Arial", 15, "bold")
                      ).pack(pady=(4, 12), padx=16, fill="x")

    def _on_broadcast_key(self, event=None):
        txt = self.txt_broadcast.get("0.0", "end").strip()
        n = len(txt)
        color = "#FF4444" if n > 4096 else "#FFD700" if n > 3000 else "#00FF00" if n > 0 else "#666666"
        self.lbl_chars.configure(text=f"{n} caracteres", text_color=color)

    def _iniciar_broadcast(self):
        msg = self.txt_broadcast.get("0.0", "end").strip()
        if len(msg) < 2:
            messagebox.showwarning("Error", "Escribe un mensaje.")
            return
        threading.Thread(target=self._proceso_broadcast, args=(msg,), daemon=True).start()

    def _proceso_broadcast(self, mensaje):
        try:
            conn = self.conectar_db()
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM usuarios_autorizados")
            uids = cur.fetchall()
            ok = err = 0
            for (uid,) in uids:
                try:
                    self.bot.send_message(uid, f"📢 {mensaje}")
                    ok += 1
                except:
                    err += 1
            self.after(0, lambda: messagebox.showinfo(
                "Broadcast completo", f"✅ Enviado: {ok}\n❌ Fallidos: {err}"))
            self.after(0, lambda: self._status(f"Broadcast: {ok} enviados, {err} fallidos",
                                                "#00FF00" if err == 0 else "#FF8800"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            if 'conn' in locals() and conn.is_connected():
                cur.close(); conn.close()

    # ─── ACTUALIZAR TODO ──────────────────
    def actualizar_todo(self):
        self._status("Sincronizando...", "#FFD700")
        threading.Thread(target=self._sync_thread, daemon=True).start()

    def _sync_thread(self):
        self.after(0, self._actualizar_stock)
        self.after(0, self._actualizar_keys)
        self.after(0, self._actualizar_usuarios)
        self.after(0, self._actualizar_precio_label)
        self.after(200, lambda: self._status("Sincronizado ✓", "#00FF00"))


# ==========================================
# 🚀 INICIO
# ==========================================
if __name__ == "__main__":
    login = PantallaConexion()
    login.mainloop()
    config = login.resultado
    if not config:
        print("❌ Sin configuración. Saliendo.")
        exit(0)
    app = AdminDashboard(config)
    app.mainloop()
