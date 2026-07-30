import hashlib
import json
import os
import secrets
import uuid
from datetime import date, datetime, timedelta

import plotly.graph_objects as go
import streamlit as st

# ============================================================================
# 1. CONFIGURAÇÕES E CONSTANTES
# ============================================================================

DATA_FILE = os.path.join(os.path.dirname(__file__), "finances_data.json")

EXPENSE_CATEGORIES = [
    "Compras", "Roupa", "Casa", "Carro", "Imprevistos", "Condomínio",
    "Luz", "Internet", "Celular", "Gasolina", "Mercado", "Ifood", "Saídas",
]
INCOME_CATEGORIES = ["Salário João", "Salário Emily", "Extra", "Rendimento", "Outro"]

DEFAULT_ACCOUNTS = [
    {"id": "bb-joao", "name": "Banco do Brasil - João", "balance": 0.0},
    {"id": "bb-emily", "name": "Banco do Brasil Emily", "balance": 0.0},
    {"id": "itau", "name": "Itaú", "balance": 0.0},
    {"id": "viacredi", "name": "Viacredi", "balance": 0.0},
    {"id": "caju", "name": "Caju", "balance": 0.0},
]

RATE_PERIODS = ["Mensal", "Anual"]

COLORS = ["#CC79A7", "#0072B2", "#E69F00", "#009E73", "#56B4E9", "#D55E00", "#F0E442"]

SUCCESS_CHART = "#009E73"  
DANGER_CHART = "#D55E00"   

ACCENT = "#ff1493"        
ACCENT_2 = "#d500f9"      
DANGER = "#b71c1c"        
WARNING = "#e65100"       
SUCCESS = "#0a7040"       
MUTED = "#5c3a58"         
TEXT = "#1f0a1c"          
PANEL = "#ffffff"         
PANEL_2 = "#fff0f6"       
BG_1 = "#ffe4e1"          
BG_2 = "#ffb6c1"          

BG_PATTERN = "url(\"data:image/svg+xml,%3Csvg width='160' height='160' viewBox='0 0 160 160' xmlns='http://www.w3.org/2000/svg'%3E%3Ctext x='20' y='40' font-size='24' opacity='0.35'%3E🌸%3C/text%3E%3Ctext x='100' y='40' font-size='24' opacity='0.35'%3E👑%3C/text%3E%3Ctext x='20' y='120' font-size='24' opacity='0.35'%3E⭐%3C/text%3E%3Ctext x='100' y='120' font-size='24' opacity='0.35'%3E🎀%3C/text%3E%3C/svg%3E\")"

st.set_page_config(page_title="Nossas Finanças", page_icon="🎀", layout="wide")

if "princess_reaction" not in st.session_state:
    st.session_state.princess_reaction = None

# ============================================================================
# 2. SISTEMA DE LOGIN E USUÁRIOS
# ============================================================================

def get_credentials():
    try:
        if hasattr(st, "secrets") and "credentials" in st.secrets:
            creds = dict(st.secrets["credentials"])
            if creds: return creds
    except Exception: pass
    return {"casal": "financas2026"}

CREDENTIALS = get_credentials()
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def hash_password(password: str, salt: str = None) -> str:
    if salt is None: salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${derived.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    try: salt, _ = stored_hash.split("$", 1)
    except (ValueError, AttributeError): return False
    return hash_password(password, salt) == stored_hash

def username_taken(username: str, registered_users: dict) -> bool:
    return username in CREDENTIALS or username in registered_users

def login_screen():
    st.markdown(f"""<style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700&family=Poppins:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
        .stApp {{ background-color: {BG_1}; background-image: {BG_PATTERN}; }}
        .login-wrap {{ max-width: 440px; margin: 6vh auto; padding: 2.4rem; background: {PANEL}; border-radius: 28px; box-shadow: 0 25px 60px rgba(255, 20, 147, 0.25); border: 2px solid {ACCENT}; text-align: center; }}
        .login-wrap h1 {{ font-family: 'Playfair Display', serif; color: {ACCENT}; margin: 0; }}
        .stButton>button {{ border: 0; border-radius: 12px; font-weight: 700; background: linear-gradient(135deg, {ACCENT}, {ACCENT_2}); color: #ffffff !important; width: 100%; }}
        </style>""", unsafe_allow_html=True)
    
    st.markdown('<div class="login-wrap"><h1>Nossas Finanças</h1><p>Entre com sua conta.</p></div>', unsafe_allow_html=True)
    tab_login, tab_signup = st.tabs(["Entrar", "Criar conta"])

    with tab_login:
        with st.form("login_form"):
            user = st.text_input("Usuário", key="login_user")
            pwd = st.text_input("Senha", type="password", key="login_pwd")
            if st.form_submit_button("Entrar 💖"):
                reg_users = load_users()
                u_clean = (user or "").strip()
                if (u_clean in CREDENTIALS and pwd == CREDENTIALS[u_clean]) or (u_clean in reg_users and verify_password(pwd, reg_users[u_clean].get("password_hash", ""))):
                    st.session_state.authenticated = True
                    st.session_state.username = u_clean
                    st.rerun()
                else: st.error("Usuário ou senha incorretos.")

    with tab_signup:
        with st.form("signup_form", clear_on_submit=True):
            n_user = st.text_input("Novo usuário", key="signup_user")
            n_pwd = st.text_input("Nova senha", type="password", key="signup_pwd")
            if st.form_submit_button("Criar conta ✨"):
                reg_users = load_users()
                u_clean = (n_user or "").strip()
                if not u_clean or len(n_pwd) < 6: st.warning("Mínimo 6 caracteres.")
                elif username_taken(u_clean, reg_users): st.warning("Usuário já existe.")
                else:
                    reg_users[u_clean] = {"password_hash": hash_password(n_pwd), "created_at": datetime.now().isoformat()}
                    save_users(reg_users)
                    st.session_state.authenticated = True
                    st.session_state.username = u_clean
                    st.success("Conta criada!")
                    st.rerun()

if "authenticated" not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated: login_screen(); st.stop()


# ============================================================================
# 3. SALVAMENTO E CARREGAMENTO
# ============================================================================

def default_state():
    return {"transactions": [], "investments": [], "accounts": [dict(a) for a in DEFAULT_ACCOUNTS], "period": date.today().strftime("%Y-%m")}

def load_state():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                d.setdefault("transactions", []); d.setdefault("investments", []); d.setdefault("accounts", [dict(a) for a in DEFAULT_ACCOUNTS]); d.setdefault("period", date.today().strftime("%Y-%m"))
                return d
        except: return default_state()
    return default_state()

def save_state():
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(st.session_state.state, f, ensure_ascii=False, indent=2)

if "state" not in st.session_state: st.session_state.state = load_state()
state = st.session_state.state
if "confirm_clear" not in st.session_state: st.session_state.confirm_clear = False

def format_currency(value: float) -> str: return f"R$ {f'{value or 0:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')}"
def month_options(): return [(date.today().replace(day=1) + timedelta(days=30*i)).strftime("%Y-%m") for i in range(-18, 13)]
def format_month(value: str) -> str: return f"{['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][int(value.split('-')[1])-1]} de {value.split('-')[0]}"
def find_account(acc_id): return next((a for a in state["accounts"] if a["id"] == acc_id), None)


# ============================================================================
# 5. ESTILOS GERAIS
# ============================================================================

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700&family=Poppins:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
    .stApp {{ background-color: {BG_1}; background-image: {BG_PATTERN}; color: {TEXT}; }}
    .panel-title {{ font-family: 'Playfair Display', serif; font-size: 1.6rem; font-weight: 700; border-bottom: 2px solid rgba(255,20,147,0.2); padding-bottom: 0.5rem; }}
    div[data-testid="stMetric"] {{ background: {PANEL_2}; border-radius: 16px; padding: 1rem; border: 2px solid rgba(255, 20, 147, 0.25); }}
    .stButton>button, .stFormSubmitButton>button {{ background: linear-gradient(135deg, {ACCENT}, {ACCENT_2}); color: white; border-radius: 12px; font-weight: 700; border: none; }}
    .transaction-item {{ padding: 1rem; border-radius: 16px; background: {PANEL_2}; border: 2px solid rgba(255,20,147,0.2); margin-bottom: 0.8rem; display: flex; justify-content: space-between; }}
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"<div style='text-align:center; padding: 1rem 0;'><div style='font-size:3rem;'>👑</div><div style='font-weight:700; color:{ACCENT};'>Olá, {st.session_state.get('username', '')}!</div></div>", unsafe_allow_html=True)
    if st.button("Sair 👋", use_container_width=True): st.session_state.authenticated = False; st.rerun()


# ============================================================================
# 7. A PRINCESA PROGRAMADA (TRADUZIDA DO SEU PYGAME!)
# ============================================================================

def gerar_princesa_svg(feliz=True):
    # Cores inspiradas no seu Pygame
    cor_vestido = "#ff69b4" if feliz else "#6495ed"  # ROSA vs AZUL_VESTIDO
    
    # Boca baseada no arco: Feliz sorri para cima, triste para baixo
    boca = 'd="M 63 75 Q 75 90 87 75"' if feliz else 'd="M 63 80 Q 75 70 87 80"'
    
    # Braço animado apenas se estiver feliz
    animacao_braco = 'class="wave"' if feliz else ""

    # SVG que funciona com as mesmas formas primitivas (Círculos, Polígonos, Linhas)
    return f"""
    <svg width="200" height="300" viewBox="0 0 150 300" xmlns="http://www.w3.org/2000/svg">
      <style>
        /* Equivalente ao math.sin(tempo) para o deslocamento (pulo) */
        .bounce {{ animation: bounce 0.6s infinite alternate ease-in-out; transform-origin: center; }}
        @keyframes bounce {{ from {{ transform: translateY(-8px); }} to {{ transform: translateY(8px); }} }}
        
        /* Equivalente ao angulo do braço */
        .wave {{ animation: wave 0.4s infinite alternate ease-in-out; transform-origin: 95px 130px; }}
        @keyframes wave {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(-30deg); }} }}
      </style>
      
      <!-- O grupo inteiro pula -->
      <g class="bounce">
        <!-- Cabelo (AMARELO) -->
        <circle cx="75" cy="60" r="42" fill="#ffd700" />
        <!-- Rosto (PELE) -->
        <circle cx="75" cy="70" r="35" fill="#ffe0bd" />
        <!-- Coroa (AMARELO) -->
        <polygon points="50,30 60,5 75,30 90,5 100,30" fill="#ffd700" />
        <!-- Olhos (PRETO) -->
        <circle cx="65" cy="65" r="3" fill="#000" />
        <circle cx="85" cy="65" r="3" fill="#000" />
        <!-- Boca (PRETO) -->
        <path {boca} stroke="#000" stroke-width="2.5" fill="none" stroke-linecap="round"/>
        <!-- Pescoço (PELE) -->
        <rect x="70" y="102" width="10" height="15" fill="#ffe0bd" />
        <!-- Pernas (PRETO) -->
        <line x1="60" y1="240" x2="60" y2="290" stroke="#000" stroke-width="4" />
        <line x1="90" y1="240" x2="90" y2="290" stroke="#000" stroke-width="4" />
        <!-- Vestido (ROSA / AZUL_VESTIDO) -->
        <polygon points="75,110 15,240 135,240" fill="{cor_vestido}" />
        <!-- Braço esquerdo estático -->
        <line x1="55" y1="130" x2="15" y2="180" stroke="#ffe0bd" stroke-width="5" stroke-linecap="round"/>
        <!-- Braço direito animado/estático -->
        <line x1="95" y1="130" x2="135" y2="180" stroke="#ffe0bd" stroke-width="5" stroke-linecap="round" {animacao_braco}/>
      </g>
    </svg>
    """

if st.session_state.princess_reaction == "happy":
    st.markdown(f"""
        <style>
        .princess-container {{ position: fixed; bottom: 20px; left: -300px; z-index: 999999 !important; animation: runAcross 4.5s linear forwards; pointer-events: none; }}
        @keyframes runAcross {{ 0% {{ left: -300px; }} 100% {{ left: 120%; visibility: hidden; }} }}
        </style>
        <div class="princess-container">{gerar_princesa_svg(feliz=True)}</div>
        """, unsafe_allow_html=True)
    st.session_state.princess_reaction = None 

elif st.session_state.princess_reaction == "sad":
    st.markdown(f"""
        <style>
        .princess-container {{ position: fixed; bottom: -350px; right: 10%; z-index: 999999 !important; animation: riseAndCry 5.5s ease-in-out forwards; pointer-events: none; }}
        @keyframes riseAndCry {{ 0% {{ bottom: -350px; opacity: 0; }} 20% {{ bottom: 0px; opacity: 1; }} 80% {{ bottom: 0px; opacity: 1; }} 100% {{ bottom: -350px; opacity: 0; visibility: hidden; }} }}
        </style>
        <div class="princess-container">{gerar_princesa_svg(feliz=False)}</div>
        """, unsafe_allow_html=True)
    st.session_state.princess_reaction = None 


# ============================================================================
# 8. FILTRO DE MÊS E FORMULÁRIO
# ============================================================================

with st.container(border=True):
    col1, col2 = st.columns([3, 1])
    with col1: st.markdown('<div class="panel-title">Nova movimentação ✨</div>', unsafe_allow_html=True)
    with col2:
        opts = list(set(month_options() + [state["period"]]))
        opts.sort()
        new_period = st.selectbox("Mês", opts, index=opts.index(state["period"]), format_func=format_month)
        if new_period != state["period"]: state["period"] = new_period; save_state(); st.rerun()

    type_label = st.selectbox("Tipo", ["Gasto", "Ganho"])
    cats = EXPENSE_CATEGORIES if type_label == "Gasto" else INCOME_CATEGORIES

    with st.form("tx_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1: cat = st.selectbox("Categoria", cats)
        with c2: acc_c = st.selectbox("Conta", ["Sem conta"] + [a["name"] for a in state["accounts"]])
        with c3: desc = st.text_input("Descrição")
        c4, c5 = st.columns(2)
        with c4: amt = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        with c5: dt = st.date_input("Data", value=date.today())

        if st.form_submit_button("Adicionar Movimentação"):
            if not desc.strip() or amt <= 0: st.warning("Preencha corretamente.")
            else:
                acc = next((a for a in state["accounts"] if a["name"] == acc_c), None)
                payload = {"id": str(uuid.uuid4()), "type": "expense" if type_label == "Gasto" else "income", "category": cat, "description": desc.strip(), "amount": float(amt), "date": dt.isoformat(), "month": state["period"], "accountId": acc["id"] if acc else None}
                if acc:
                    if payload["type"] == "expense": acc["balance"] -= payload["amount"]
                    else: acc["balance"] += payload["amount"]
                state["transactions"].insert(0, payload)
                save_state()
                
                # Ativa a nossa princesa desenhada!
                st.session_state.princess_reaction = "happy" if payload["type"] == "income" else "sad"
                st.rerun()

# ============================================================================
# 9. HISTÓRICO
# ============================================================================

current_txs = [t for t in state["transactions"] if t["month"] == state["period"]]
st.write("")
m1, m2 = st.columns(2)
m1.metric("Ganhos do Mês", format_currency(sum(t["amount"] for t in current_txs if t["type"] == "income")))
m2.metric("Gastos do Mês", format_currency(sum(t["amount"] for t in current_txs if t["type"] == "expense")))
st.write("")

with st.container(border=True):
    st.markdown('<div class="panel-title">Histórico 📋</div>', unsafe_allow_html=True)
    if not current_txs: st.write("Nenhuma movimentação neste mês.")
    for t in current_txs:
        sign, color = ("+", SUCCESS) if t["type"] == "income" else ("-", DANGER)
        st.markdown(f"""
        <div class="transaction-item">
            <div><strong>{t['description']}</strong><br><span style="font-size:0.9em; color:#666;">{t['category']} • {t['date']}</span></div>
            <div style="color:{color}; font-weight:bold; font-size:1.1em;">{sign}{format_currency(t['amount'])}</div>
        </div>
        """, unsafe_allow_html=True)
