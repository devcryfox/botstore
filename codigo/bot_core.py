import os
import telebot
import mysql.connector

# ==========================================
# ⚙️ CONFIGURACIÓN Y CONEXIÓN
# ==========================================

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise Exception("❌ TOKEN no encontrado en Railway")

DB_CONFIG = {
    'host':     os.getenv("MYSQLHOST") or os.getenv("DB_HOST"),
    'user':     os.getenv("MYSQLUSER") or os.getenv("DB_USER"),
    'password': os.getenv("MYSQLPASSWORD") or os.getenv("DB_PASSWORD"),
    'database': os.getenv("MYSQLDATABASE") or os.getenv("DB_NAME") or "railway",
    'port':     int(os.getenv("MYSQLPORT") or os.getenv("DB_PORT") or 3306)
}

# DEPURACIÓN: Imprimimos qué variables encontró el sistema
print("--- VARIABLES DETECTADAS POR EL BOT ---")
for key, value in DB_CONFIG.items():
    status = "✅ OK" if value else "❌ VACÍA/NO ENCONTRADA"
    print(f"{key}: {status}")
print("---------------------------------------")

# Validación final
missing = [k for k, v in DB_CONFIG.items() if not v]
if missing:
    raise Exception(f"❌ Variables de DB faltantes en Railway: {missing}")

bot = telebot.TeleBot(TOKEN)

CONTACTO_ADMIN = "@useragb"

# ==========================================
# 🔌 CONEXIÓN MYSQL
# ==========================================

def conectar_db():
    print("✅ Intentando conectar a MySQL...")
    return mysql.connector.connect(**DB_CONFIG)

# ==========================================
# 💰 OBTENER PRECIO
# ==========================================

def obtener_precio_actual():
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT valor
            FROM configuracion_sistema
            WHERE parametro = 'precio_cuenta'
        """)
        res = cursor.fetchone()
        return int(res[0]) if res else 20
    except Exception as e:
        print(f"❌ ERROR obtener_precio_actual: {e}")
        return 20
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# ==========================================
# 👋 START / HELP
# ==========================================

@bot.message_handler(commands=['start', 'help'])
def bienvenida(message):
    uid = message.from_user.id
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT creditos
            FROM usuarios_autorizados
            WHERE user_id = %s
        """, (uid,))
        user = cursor.fetchone()

        if user:
            bot.reply_to(
                message,
                f"✅ <b>Sistema Activo.</b>\n\n"
                f"💰 Tu saldo: <b>${user[0]} MXN</b>\n"
                f"🛒 Usa /productos para ver stock.",
                parse_mode="HTML"
            )
        else:
            bot.reply_to(
                message,
                "🔒 <b>Acceso restringido.</b>\n\n"
                "Envíame tu key de acceso para registrarte.",
                parse_mode="HTML"
            )
    except Exception as e:
        print(f"❌ ERROR start: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# ==========================================
# 🛒 PRODUCTOS
# ==========================================

@bot.message_handler(commands=['productos', 'stock'])
def mostrar_productos(message):
    uid = message.from_user.id
    precio = obtener_precio_actual()
    try:
        conn = conectar_db()
        cursor = conn.cursor(buffered=True)
        cursor.execute("""
            SELECT creditos
            FROM usuarios_autorizados
            WHERE user_id = %s
        """, (uid,))
        user = cursor.fetchone()

        if not user:
            return

        cursor.execute("""
            SELECT servicio, COUNT(id)
            FROM combos
            WHERE estado = 'disponible'
            GROUP BY servicio
        """)
        resultados = cursor.fetchall()

        resp = (
            f"💰 <b>Saldo:</b> ${user[0]} MXN\n"
            f"🏷️ <b>Precio:</b> ${precio} MXN c/u\n\n"
        )
        resp += "🛒 <b>PRODUCTOS DISPONIBLES</b>\n"
        resp += "━━━━━━━━━━━━━━━━━━\n"

        if resultados:
            for serv, cant in resultados:
                resp += (
                    f"🔹 <b>{serv.capitalize()}</b> "
                    f"({cant}) ➜ /{serv}\n"
                )
        else:
            resp += "⚠️ No hay stock actualmente."

        bot.reply_to(message, resp, parse_mode="HTML")

    except Exception as e:
        print(f"❌ ERROR productos: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# ==========================================
# 📦 ENTREGA DE CUENTAS
# ==========================================

@bot.message_handler(func=lambda message: message.text.startswith('/'))
def entregar_cuenta(message):
    uid = message.from_user.id
    servicio = message.text[1:].strip().lower()

    if servicio in ['start', 'help', 'productos', 'stock']:
        return

    precio = obtener_precio_actual()
    try:
        conn = conectar_db()
        cursor = conn.cursor(buffered=True)
        cursor.execute("""
            SELECT creditos
            FROM usuarios_autorizados
            WHERE user_id = %s
        """, (uid,))
        res_user = cursor.fetchone()

        if not res_user:
            return

        saldo_actual = res_user[0]

        if saldo_actual < precio:
            bot.reply_to(
                message,
                f"❌ <b>Saldo insuficiente</b>\n\n"
                f"💰 Saldo: ${saldo_actual}\n"
                f"🏷️ Precio: ${precio}\n\n"
                f"📩 Contacto: {CONTACTO_ADMIN}",
                parse_mode="HTML"
            )
            return

        cursor.execute("""
            SELECT id, cuenta
            FROM combos
            WHERE servicio = %s
            AND estado = 'disponible'
            LIMIT 1
        """, (servicio,))
        res_combo = cursor.fetchone()

        if not res_combo:
            bot.reply_to(
                message,
                "⚠️ No hay stock disponible de ese servicio."
            )
            return

        combo_id, cuenta_txt = res_combo

        cursor.execute("""
            UPDATE usuarios_autorizados
            SET creditos = creditos - %s
            WHERE user_id = %s
        """, (precio, uid))

        cursor.execute("""
            UPDATE combos
            SET estado = 'entregado'
            WHERE id = %s
        """, (combo_id,))

        conn.commit()
        nuevo_saldo = saldo_actual - precio

        bot.reply_to(
            message,
            f"✅ <b>COMPRA EXITOSA</b>\n\n"
            f"💸 Costo: ${precio}\n"
            f"💰 Nuevo saldo: ${nuevo_saldo}\n\n"
            f"<code>{cuenta_txt}</code>",
            parse_mode="HTML"
        )

    except Exception as e:
        print(f"❌ ERROR compra: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# ==========================================
# 🔑 REGISTRO POR KEY
# ==========================================

@bot.message_handler(func=lambda message: True)
def procesar_keys(message):
    uid = message.from_user.id
    texto = message.text.strip()
    try:
        conn = conectar_db()
        cursor = conn.cursor(buffered=True)
        cursor.execute("""
            SELECT clave
            FROM claves_acceso
            WHERE clave = %s
        """, (texto,))
        existe = cursor.fetchone()

        if existe:
            cursor.execute("""
                SELECT user_id
                FROM usuarios_autorizados
                WHERE user_id = %s
            """, (uid,))
            ya_registrado = cursor.fetchone()

            if ya_registrado:
                bot.reply_to(message, "⚠️ Ya estás registrado.")
                return

            cursor.execute("""
                INSERT INTO usuarios_autorizados (user_id, creditos)
                VALUES (%s, 0)
            """, (uid,))

            cursor.execute("""
                DELETE FROM claves_acceso
                WHERE clave = %s
            """, (texto,))

            conn.commit()

            bot.reply_to(
                message,
                f"🔓 <b>Acceso concedido</b>\n\n"
                f"💰 Saldo actual: $0 MXN\n"
                f"📩 Contacta a {CONTACTO_ADMIN} para recargar.",
                parse_mode="HTML"
            )

    except Exception as e:
        print(f"❌ ERROR keys: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# ==========================================
# 🚀 INICIAR BOT
# ==========================================

if __name__ == "__main__":
    import time
    print("🚀 [BOT] Corriendo con Precios Dinámicos...")
    print(f"🔗 Conectando a: {DB_CONFIG['host']}:{DB_CONFIG['port']} / {DB_CONFIG['database']}")
    try:
        bot.remove_webhook()
        time.sleep(2)
        print("🔄 Iniciando polling...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"❌ ERROR EN POLLING: {e}")
