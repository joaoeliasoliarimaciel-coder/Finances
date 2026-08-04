import base64
import hashlib
import json
import os
import secrets
import textwrap
import uuid
import requests
import yfinance as yf
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

# Fundos automatizados
BB_INVESTMENT_OPTIONS = [
    "Eletrobras",
    "LP High",
    "LP Prefixado",
    "MM Ouro",
    "MM Carteira Investimento",
    "Outro (Manual - Configurar Juros)"
]

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
        except Exception: return {}
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

def login_css():
    css = textwrap.dedent(f"""\
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700&family=Poppins:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
    .stApp {{ background-color: {BG_1}; background-image: {BG_PATTERN}, radial-gradient(circle at 15% 10%, {BG_2}, transparent 55%), radial-gradient(circle at 85% 90%, #ffcbe0, transparent 55%); }}
    .login-wrap {{ max-width: 440px; margin: 6vh auto 1.2rem auto; padding: 2.4rem 2.2rem 1.4rem 2.2rem; background: {PANEL}; border-radius: 28px; box-shadow: 0 25px 60px rgba(255, 20, 147, 0.25); border: 2px solid {ACCENT}; text-align: center; }}
    .login-wrap .icon {{ font-size: 3rem; margin-bottom: 0.2rem; }}
    .login-wrap h1 {{ font-family: 'Playfair Display', serif; color: {ACCENT}; font-size: 2.4rem; font-weight: 700; margin: 0; }}
    .login-wrap p {{ color: {TEXT}; font-size: 1rem; font-weight: 600; }}
    div[data-testid="stForm"] {{ max-width: 440px; margin: 0 auto; border: none !important; background: transparent !important; padding: 0 !important; }}
    label, .stTextInput label p {{ color: {TEXT} !important; font-weight: 700 !important; }}
    input {{ background-color: {PANEL_2} !important; color: {TEXT} !important; border-radius: 12px !important; border: 2px solid rgba(255, 20, 147, 0.4) !important; }}
    .stButton>button, .stFormSubmitButton>button {{ border: 0; border-radius: 12px; font-weight: 700; background: linear-gradient(135deg, {ACCENT}, {ACCENT_2}); color: #ffffff !important; width: 100%; padding: 0.75rem 1.1rem; }}
    div[data-testid="stTabs"] {{ max-width: 440px; margin: 0 auto; }}
    div[data-testid="stTabs"] button[aria-selected="true"] {{ color: {ACCENT} !important; }}
    div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] {{ background-color: {ACCENT} !important; height: 4px; }}
    </style>
    """)
    st.markdown(css, unsafe_allow_html=True)

def login_screen():
    login_css()
    st.markdown('<div class="login-wrap"><div class="icon">🌸</div><h1>Nossas Finanças</h1><p>Entre com sua conta.</p></div>', unsafe_allow_html=True)
    tab_login, tab_signup = st.tabs(["Entrar", "Criar conta"])

    with tab_login:
        with st.form("login_form"):
            user = st.text_input("Usuário", key="login_user")
            pwd = st.text_input("Senha", type="password", key="login_pwd")
            if st.form_submit_button("Entrar 💖"):
                registered_users = load_users()
                user_clean = (user or "").strip()
                if (user_clean in CREDENTIALS and pwd == CREDENTIALS[user_clean]) or (user_clean in registered_users and verify_password(pwd, registered_users[user_clean].get("password_hash", ""))):
                    st.session_state.authenticated = True
                    st.session_state.username = user_clean
                    st.rerun()
                else: st.error("Usuário ou senha incorretos.")

    with tab_signup:
        with st.form("signup_form", clear_on_submit=True):
            new_user = st.text_input("Escolha um usuário", key="signup_user")
            new_pwd = st.text_input("Escolha uma senha", type="password", key="signup_pwd")
            new_pwd_confirm = st.text_input("Confirme a senha", type="password", key="signup_pwd_confirm")
            if st.form_submit_button("Criar conta ✨"):
                registered_users = load_users()
                user_clean = (new_user or "").strip()
                if not user_clean or len(new_pwd) < 6: st.warning("Preencha usuário e senha (mínimo 6 caracteres).")
                elif new_pwd != new_pwd_confirm: st.warning("As senhas não coincidem.")
                elif username_taken(user_clean, registered_users): st.warning("Usuário já existe.")
                else:
                    registered_users[user_clean] = {"password_hash": hash_password(new_pwd), "created_at": datetime.now().isoformat()}
                    save_users(registered_users)
                    st.session_state.authenticated = True
                    st.session_state.username = user_clean
                    st.success("Conta criada! Entrando...")
                    st.rerun()

if "authenticated" not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated: login_screen(); st.stop()


# ============================================================================
# 3. INTEGRAÇÃO DE MERCADO EM TEMPO REAL (MÁGICA DOS FUNDOS)
# ============================================================================

@st.cache_data(ttl=43200) # Atualiza a cada 12 horas para não sobrecarregar
def get_auto_multiplier(inv_name: str, start_date_str: str) -> float:
    """Busca dados da bolsa e do Banco Central para multiplicar a cota de forma automática."""
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        if start_date >= date.today(): 
            return 1.0

        # Eletrobras -> Busca a ação real (ELET3.SA) no Yahoo Finance
        if "Eletrobras" in inv_name:
            hist = yf.download("ELET3.SA", start=start_date_str, progress=False)
            if not hist.empty: 
                primeiro = float(hist['Close'].dropna().values[0])
                ultimo = float(hist['Close'].dropna().values[-1])
                return ultimo / primeiro
            
        # MM Ouro -> Busca contrato futuro de ouro Global
        elif "Ouro" in inv_name:
            hist = yf.download("GC=F", start=start_date_str, progress=False) 
            if not hist.empty: 
                primeiro = float(hist['Close'].dropna().values[0])
                ultimo = float(hist['Close'].dropna().values[-1])
                return ultimo / primeiro
            
        # Fundos de Renda Fixa e Multimercado -> Puxa o CDI diário real direto do Banco Central
        elif "LP High" in inv_name or "Carteira Investimento" in inv_name or "LP Prefixado" in inv_name:
            d_str = start_date.strftime("%d/%m/%Y")
            url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json&dataInicial={d_str}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                multiplier = 1.0
                for row in data:
                    multiplier *= (1 + (float(row['valor']) / 100.0))
                
                # Ajustes finos do perfil de cada fundo:
                if "LP Prefixado" in inv_name:
                    # Fundos prefixados não seguem CDI perfeitamente, assumindo média de 10.5% ao ano.
                    days = (date.today() - start_date).days
                    return (1.105) ** (days / 365.25)
                elif "LP High" in inv_name:
                    return multiplier * 1.02 # Geralmente tenta render 102~105% do CDI
                return multiplier # MM Carteira Investimento (rendimento base ~100% CDI)
                
    except Exception as e: 
        pass
    
    return 1.0 # Se der falha de conexão, mantém o valor original sem erro.

# ============================================================================
# 4. SALVAMENTO E CARREGAMENTO DE DADOS
# ============================================================================

def default_state():
    return {"transactions": [], "investments": [], "accounts": [dict(a) for a in DEFAULT_ACCOUNTS], "period": date.today().strftime("%Y-%m")}

def load_state():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f: data = json.load(f)
            data.setdefault("transactions", []); data.setdefault("investments", []); data.setdefault("accounts", [dict(a) for a in DEFAULT_ACCOUNTS]); data.setdefault("period", date.today().strftime("%Y-%m"))
            return data
        except Exception: return default_state()
    return default_state()

def save_state():
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(st.session_state.state, f, ensure_ascii=False, indent=2)

if "state" not in st.session_state: st.session_state.state = load_state()
state = st.session_state.state
if "confirm_clear" not in st.session_state: st.session_state.confirm_clear = False


# ============================================================================
# 5. FUNÇÕES DE APOIO E CÁLCULOS
# ============================================================================

def format_currency(value: float) -> str: return f"R$ {f'{value or 0:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')}"
def month_options(months_back=18, months_fwd=12):
    today = date.today()
    return [f"{(today.year * 12 + today.month - 1 + i) // 12:04d}-{(today.year * 12 + today.month - 1 + i) % 12 + 1:02d}" for i in range(-months_back, months_fwd + 1)]

MONTH_NAMES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
def format_month(value: str) -> str:
    try: y, m = value.split("-"); return f"{MONTH_NAMES[int(m) - 1].capitalize()} de {y}"
    except: return value

def find_account(account_id): return next((a for a in state["accounts"] if a["id"] == account_id), None)
def monthly_rate(rate_pct: float, period: str) -> float: r = (rate_pct or 0) / 100; return (1 + r) ** (1 / 12) - 1 if period == "Anual" else r
def months_elapsed(start_iso: str, as_of: date) -> float:
    try: start = date.fromisoformat(start_iso)
    except: start = as_of
    return max(0.0, (as_of - start).days / 30.4368)

def investment_principal(inv) -> float: return inv.get("initial_amount", 0.0) + sum(c["amount"] for c in inv.get("contributions", []))

# --- CÁLCULO ATUALIZADO DOS INVESTIMENTOS (MANUAL VS AUTOMÁTICO) ---
def investment_current_value(inv, as_of: date = None) -> float:
    as_of = as_of or date.today()
    name = inv.get("name", "")
    
    # Se for um fundo da nossa lista automatizada, puxamos via API real
    is_auto = any(af in name for af in ["Eletrobras", "LP High", "LP Prefixado", "Ouro", "Carteira Investimento"])
    
    if is_auto:
        mult = get_auto_multiplier(name, inv.get("start_date"))
        val = inv.get("initial_amount", 0.0) * mult
        for c in inv.get("contributions", []):
            m_c = get_auto_multiplier(name, c["date"])
            val += c["amount"] * m_c
        return val
    else:
        # Se for manual (poupança, etc), usa o cálculo antigo de juros simples/compostos
        r_m = monthly_rate(inv.get("rate", 0.0), inv.get("rate_period", "Mensal"))
        val = inv.get("initial_amount", 0.0) * (1 + r_m) ** months_elapsed(inv.get("start_date"), as_of)
        for c in inv.get("contributions", []): val += c["amount"] * (1 + r_m) ** months_elapsed(c["date"], as_of)
        return val

def rate_label(inv) -> str: 
    if any(af in inv.get("name","") for af in ["Eletrobras", "LP High", "LP Prefixado", "Ouro", "Carteira Investimento"]):
        return "Rendimento Automático"
    return f"{inv.get('rate', 0.0):.2f}% {'ao mês' if inv.get('rate_period', 'Mensal') == 'Mensal' else 'ao ano'}".replace(".", ",")


# ============================================================================
# 6. ESTILOS (CSS DO APP PRINCIPAL)
# ============================================================================

main_css = textwrap.dedent(f"""\
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700&family=Poppins:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
.stApp {{ background-color: {BG_1}; background-image: {BG_PATTERN}, radial-gradient(circle at 10% 0%, {BG_2}, transparent 50%), radial-gradient(circle at 90% 100%, #ffcbe0, transparent 50%); color: {TEXT}; }}
.block-container {{ max-width: 1200px; padding-top: 1.5rem; }}
.hero {{ padding: 2.5rem 2.2rem; border-radius: 26px; background: linear-gradient(120deg, rgba(255,255,255,0.95), rgba(255,240,246,0.95)); border: 2px solid {ACCENT}; margin-bottom: 2rem; box-shadow: 0 18px 45px rgba(255, 20, 147, 0.2); display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; backdrop-filter: blur(5px); }}
.hero .eyebrow {{ margin: 0; text-transform: uppercase; letter-spacing: 0.25rem; color: {ACCENT}; font-weight: 800; font-size: 0.85rem; }}
.hero h1 {{ font-family: 'Playfair Display', serif; margin: 0.15rem 0; font-size: 2.8rem; color: {TEXT}; font-weight: 700; }}
.hero p.subtitle {{ color: {TEXT}; max-width: 620px; margin: 0; font-weight: 500; font-size: 1.05rem; }}
.hero .hero-icon {{ font-size: 4rem; text-shadow: 2px 2px 15px rgba(255,20,147,0.3); }}
.panel-title {{ font-family: 'Playfair Display', serif; font-size: 1.6rem; font-weight: 700; color: {TEXT}; margin-bottom: 1rem; border-bottom: 2px solid rgba(255,20,147,0.2); padding-bottom: 0.5rem; }}
div[data-testid="stVerticalBlockBorderWrapper"] {{ background: rgba(255,255,255,0.9); border: 2px solid rgba(255, 20, 147, 0.3) !important; border-radius: 22px !important; box-shadow: 0 12px 30px rgba(255, 20, 147, 0.12); padding: 0.5rem; backdrop-filter: blur(5px); }}
div[data-testid="stMetric"] {{ background: {PANEL_2}; border-radius: 16px; padding: 1rem; border: 2px solid rgba(255, 20, 147, 0.25); box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
div[data-testid="stMetricLabel"] {{ color: {TEXT}; font-weight: 700; font-size: 1rem; }}
div[data-testid="stMetricValue"] {{ color: {TEXT}; font-weight: 800; font-size: 1.6rem; }}
.stButton>button, .stFormSubmitButton>button {{ border: 0; border-radius: 12px; font-weight: 700; background: linear-gradient(135deg, {ACCENT}, {ACCENT_2}); color: white; padding: 0.65rem 1.2rem; font-size: 1.05rem; }}
.stButton>button:hover, .stFormSubmitButton>button:hover {{ color: white; transform: translateY(-2px); transition: all 0.2s ease; }}
button[kind="secondary"] {{ background: {PANEL_2} !important; border: 2px solid {ACCENT} !important; color: {TEXT} !important; }}
label, .stSelectbox label p, .stTextInput label p, .stNumberInput label p {{ font-weight: 700 !important; color: {TEXT} !important; }}
input, textarea, select, .stSelectbox div[data-baseweb="select"] > div {{ background-color: {PANEL_2} !important; color: {TEXT} !important; border-radius: 12px !important; border: 2px solid rgba(255,20,147,0.3) !important; font-weight: 600 !important; }}
.transaction-item, .account-item, .investment-item {{ padding: 1rem 1.2rem; border-radius: 16px; background: {PANEL_2}; margin-bottom: 0.8rem; display: flex; justify-content: space-between; align-items: center; gap: 1rem; border: 2px solid rgba(255,20,147,0.2); }}
.t-meta strong {{ display:block; color: {TEXT}; font-size: 1.1rem; }}
.t-meta span {{ color: {MUTED}; font-size: 0.95rem; font-weight: 600; }}
.t-amount {{ font-weight: 800; font-size: 1.15rem; white-space: nowrap; }}
.t-amount.income {{ color: {SUCCESS}; }}
.t-amount.expense {{ color: {DANGER}; }}
.acc-balance {{ font-weight: 800; font-size: 1.2rem; color: {SUCCESS}; }}
.acc-balance.negative {{ color: {DANGER}; }}
.empty-state {{ padding: 1.5rem; border-radius: 16px; background: {PANEL_2}; color: {TEXT}; text-align: center; font-weight: 600; border: 2px dashed rgba(255,20,147,0.4); }}
.legend-item {{ display:flex; justify-content: space-between; color: {TEXT}; margin-bottom: 0.5rem; font-weight: 600; font-size: 1.05rem; }}
.legend-badge {{ width: 14px; height: 14px; border-radius: 4px; display:inline-block; margin-right: 0.6rem; border: 1px solid rgba(0,0,0,0.1); }}
.inv-card {{ padding: 1.2rem 1.4rem; border-radius: 20px; background: {PANEL_2}; border: 2px solid rgba(255,20,147,0.25); margin-bottom: 1rem; }}
.inv-card .inv-top {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; }}
.inv-card .inv-name {{ font-weight: 800; color: {TEXT}; font-size: 1.2rem; }}
.inv-card .inv-meta {{ color: {MUTED}; font-size: 0.95rem; font-weight: 600; margin-top: 0.2rem; }}
.inv-badge {{ display:inline-block; padding: 0.25rem 0.7rem; border-radius: 999px; background: {ACCENT}; color: white; font-size: 0.85rem; font-weight: 700; }}
.inv-value {{ font-size: 1.4rem; font-weight: 800; color: {TEXT}; text-align: right; }}
.inv-gain {{ font-size: 0.95rem; font-weight: 700; text-align: right; margin-top: 0.2rem; }}
.inv-gain.positive {{ color: {SUCCESS}; }}
.inv-gain.neutral {{ color: {MUTED}; }}
section[data-testid="stSidebar"] {{ background: rgba(255, 240, 246, 0.95); border-right: 2px solid rgba(255,20,147,0.2); backdrop-filter: blur(5px); }}
.happy-princess, .sad-princess {{ position: fixed; z-index: 999999 !important; pointer-events: none; }}
.happy-princess img, .sad-princess img {{ display: block; width: 160px; height: auto; filter: drop-shadow(0 8px 18px rgba(0,0,0,0.25)); }}
.happy-princess {{ bottom: 20px; left: -300px; animation: runAcross 4.5s linear forwards; }}
.sad-princess {{ bottom: -350px; right: 8%; animation: riseAndCry 5.5s ease-in-out forwards; }}
@keyframes runAcross {{ 0% {{ left: -300px; }} 100% {{ left: 120%; visibility: hidden; }} }}
@keyframes riseAndCry {{ 0% {{ bottom: -350px; opacity: 0; }} 20% {{ bottom: 0px; opacity: 1; }} 80% {{ bottom: 0px; opacity: 1; }} 100% {{ bottom: -350px; opacity: 0; visibility: hidden; }} }}
.princess-bounce {{ animation: princessBounce 0.6s infinite alternate ease-in-out; }}
@keyframes princessBounce {{ from {{ transform: translateY(-8px); }} to {{ transform: translateY(8px); }} }}
</style>
""")
st.markdown(main_css, unsafe_allow_html=True)


# ============================================================================
# 7. SIDEBAR E CABEÇALHO
# ============================================================================

with st.sidebar:
    sidebar_html = textwrap.dedent(f"""\
    <div style="text-align:center; padding: 1rem 0 1.5rem 0;">
        <div style="font-size:3.5rem;">👑</div>
        <div style="font-family:'Playfair Display', serif; font-weight:700; font-size:1.6rem; color:{ACCENT};">Nossas Finanças</div>
        <div style="color:{TEXT}; font-size:1rem; font-weight: 600;">Olá, {st.session_state.get('username', '')}!</div>
    </div>
    """)
    st.markdown(sidebar_html, unsafe_allow_html=True)
    if st.button("Sair da Conta 👋", use_container_width=True, type="secondary"):
        st.session_state.authenticated = False; st.rerun()

hero_html = textwrap.dedent("""\
<div class="hero">
    <div>
        <p class="eyebrow">Controle financeiro do casal</p>
        <h1>Nossas Finanças</h1>
        <p class="subtitle">Organize gastos, ganhos, investimentos e acompanhe o patrimônio com clareza.</p>
    </div>
    <div class="hero-icon">👑</div>
</div>
""")
st.markdown(hero_html, unsafe_allow_html=True)


# ============================================================================
# 8. ANIMAÇÕES DA PRINCESA
# ============================================================================

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


@st.cache_data
def carregar_imagem_base64(nome_arquivo: str) -> str:
    """Lê uma imagem da pasta assets/ e retorna como base64 (cacheado)."""
    caminho = os.path.join(ASSETS_DIR, nome_arquivo)
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


if st.session_state.princess_reaction == "happy":
    img_b64 = carregar_imagem_base64("princesa_feliz.png")
    happy_html = textwrap.dedent(f"""\
    <div class="happy-princess">
        <img class="princess-bounce" src="data:image/png;base64,{img_b64}" alt="Princesa feliz" />
    </div>
    """)
    st.markdown(happy_html, unsafe_allow_html=True)
    st.session_state.princess_reaction = None

elif st.session_state.princess_reaction == "sad":
    img_b64 = carregar_imagem_base64("princesa_triste.png")
    sad_html = textwrap.dedent(f"""\
    <div class="sad-princess">
        <img class="princess-bounce" src="data:image/png;base64,{img_b64}" alt="Princesa triste" />
    </div>
    """)
    st.markdown(sad_html, unsafe_allow_html=True)
    st.session_state.princess_reaction = None


# ============================================================================
# 9. FILTRO DE MÊS E FORMULÁRIO DE NOVA MOVIMENTAÇÃO
# ============================================================================

with st.container(border=True):
    top_col1, top_col2 = st.columns([3, 1])
    with top_col1: st.markdown('<div class="panel-title">Nova movimentação ✨</div>', unsafe_allow_html=True)
    with top_col2:
        options = month_options()
        if state["period"] not in options:
            options.append(state["period"])
            options.sort()
        new_period = st.selectbox("Mês de referência", options, index=options.index(state["period"]), format_func=format_month)
        if new_period != state["period"]:
            state["period"] = new_period
            save_state()
            st.rerun()

    type_label = st.selectbox("Tipo de Movimentação", ["Gasto", "Ganho"], key="new_type")
    categories = EXPENSE_CATEGORIES if type_label == "Gasto" else INCOME_CATEGORIES

    with st.form("transaction_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1: category = st.selectbox("Categoria", categories)
        with c2: account_choice = st.selectbox("Conta", ["Sem conta"] + [a["name"] for a in state["accounts"]])
        with c3: description = st.text_input("Descrição", placeholder="Ex.: Mercado")

        c4, c5 = st.columns(2)
        with c4: amount = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        with c5: date_value = st.date_input("Data", value=date.today())

        if st.form_submit_button("Adicionar Movimentação 💸"):
            if not description.strip() or amount <= 0:
                st.warning("Preencha a descrição e um valor maior que zero.")
            else:
                acc = next((a for a in state["accounts"] if a["name"] == account_choice), None) if account_choice != "Sem conta" else None
                payload = {
                    "id": str(uuid.uuid4()), "type": "expense" if type_label == "Gasto" else "income",
                    "category": category, "description": description.strip(), "amount": float(amount),
                    "date": date_value.isoformat(), "month": state["period"],
                    "accountId": acc["id"] if acc else None, "accountName": acc["name"] if acc else None,
                }
                if acc:
                    if payload["type"] == "expense": acc["balance"] -= payload["amount"]
                    else: acc["balance"] += payload["amount"]

                state["transactions"].insert(0, payload)
                save_state()
                
                if payload["type"] == "income": st.session_state.princess_reaction = "happy"
                else: st.session_state.princess_reaction = "sad"
                st.rerun()


# ============================================================================
# 10. CÁLCULOS TOTAIS E MÉTRICAS PRINCIPAIS
# ============================================================================

current_transactions = [t for t in state["transactions"] if t["month"] == state["period"]]
income = sum(t["amount"] for t in current_transactions if t["type"] == "income")
expenses = sum(t["amount"] for t in current_transactions if t["type"] == "expense")
balance = income - expenses
accounts_total = sum(a["balance"] for a in state["accounts"])
invested_principal_total = sum(investment_principal(i) for i in state["investments"])
invested_current_total = sum(investment_current_value(i) for i in state["investments"])
investment_gain_total = invested_current_total - invested_principal_total
net_worth = accounts_total + invested_current_total

st.write("")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Ganhos", format_currency(income))
m2.metric("Gastos", format_currency(expenses))
m3.metric("Saldo do mês", format_currency(balance))
m4.metric("Nas contas", format_currency(accounts_total))
m5.metric("Patrimônio total", format_currency(net_worth))
st.write("")


# ============================================================================
# 11. HISTÓRICO DE MOVIMENTAÇÕES
# ============================================================================

with st.container(border=True):
    h1, h2 = st.columns([4, 1])
    with h1: st.markdown('<div class="panel-title">Histórico de Movimentações 📋</div>', unsafe_allow_html=True)
    with h2:
        if st.button("Limpar dados", type="secondary", use_container_width=True): st.session_state.confirm_clear = True

    if st.session_state.confirm_clear:
        st.warning("Tem certeza que deseja apagar TODOS os dados?")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("Confirmar exclusão", type="secondary"):
                st.session_state.state = default_state()
                state = st.session_state.state; save_state()
                st.session_state.confirm_clear = False; st.rerun()
        with cc2:
            if st.button("Cancelar"): st.session_state.confirm_clear = False; st.rerun()

    if not current_transactions: st.markdown('<div class="empty-state">Nenhuma movimentação neste mês! 🌷</div>', unsafe_allow_html=True)
    else:
        for t in current_transactions:
            meta_line = f'{t["category"]} • {t["date"]}'
            if t.get("accountName"): meta_line += f' • {t["accountName"]}'
            sign, cls = ("+", "income") if t["type"] == "income" else ("-", "expense")

            row = st.container()
            with row:
                rc1, rc2, rc3 = st.columns([5, 2, 1])
                with rc1: st.markdown(f'<div class="t-meta"><strong>{t["description"]}</strong><span>{meta_line}</span></div>', unsafe_allow_html=True)
                with rc2: st.markdown(f'<div class="t-amount {cls}">{sign}{format_currency(t["amount"])}</div>', unsafe_allow_html=True)
                with rc3:
                    if st.button("Remover", key=f"rm_{t['id']}"):
                        if t.get("accountId"):
                            acc = find_account(t["accountId"])
                            if acc:
                                if t["type"] == "expense": acc["balance"] += t["amount"]
                                else: acc["balance"] -= t["amount"]
                        state["transactions"] = [x for x in state["transactions"] if x["id"] != t["id"]]
                        save_state()
                        st.rerun()


# ============================================================================
# 12. GRÁFICOS VISUAIS E ANÁLISE DE DADOS
# ============================================================================

with st.container(border=True):
    st.markdown('<div class="panel-title">Análise Financeira 📊</div>', unsafe_allow_html=True)
    g1, g2 = st.columns([1.2, 0.8])

    with g1:
        st.markdown(f"**<span style='color:{TEXT}; font-size:1.1rem;'>Receitas x Despesas</span>**", unsafe_allow_html=True)
        bar_fig = go.Figure(data=[go.Bar(x=["Ganhos", "Gastos"], y=[income, expenses], marker_color=[SUCCESS_CHART, DANGER_CHART], marker_line=dict(color=TEXT, width=1.5), text=[format_currency(income), format_currency(expenses)], textposition="auto", textfont=dict(color="white", size=16), width=0.4)])
        bar_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT, family="Poppins", size=14), yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.35)", zeroline=True, zerolinecolor=TEXT, zerolinewidth=2, visible=True, color=TEXT), xaxis=dict(showgrid=False, showline=True, linewidth=2, linecolor=TEXT, color=TEXT, tickfont=dict(size=15, color=TEXT)), margin=dict(l=10, r=10, t=30, b=10), height=320, showlegend=False)
        st.plotly_chart(bar_fig, use_container_width=True, theme=None)
       
    with g2:
        st.markdown(f"**<span style='color:{TEXT}; font-size:1.1rem;'>Despesas por categoria</span>**", unsafe_allow_html=True)
        expense_items = [t for t in current_transactions if t["type"] == "expense"]
        totals_by_cat = {}
        for t in expense_items: totals_by_cat[t["category"]] = totals_by_cat.get(t["category"], 0) + t["amount"]

        if not totals_by_cat: donut_fig = go.Figure(data=[go.Pie(labels=["Sem dados"], values=[1], hole=0.65, marker=dict(colors=[PANEL_2]), textinfo="none")])
        else: donut_fig = go.Figure(data=[go.Pie(labels=list(totals_by_cat.keys()), values=list(totals_by_cat.values()), hole=0.65, marker=dict(colors=COLORS * 3, line=dict(color=PANEL, width=3)), textinfo="none")])

        donut_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT, family="Poppins"), margin=dict(l=10, r=10, t=30, b=10), height=320, showlegend=False, annotations=[dict(text=f"Total:<br>{format_currency(sum(totals_by_cat.values()))}" if totals_by_cat else "Sem dados", x=0.5, y=0.5, font_size=16, showarrow=False, font_color=TEXT)])
        st.plotly_chart(donut_fig, use_container_width=True)

        if totals_by_cat:
            for idx, (name, value) in enumerate(totals_by_cat.items()):
                color = COLORS[idx % len(COLORS)]
                st.markdown(f'<div class="legend-item"><span style="display:flex; align-items:center;"><span class="legend-badge" style="background:{color}; border: 2px solid {TEXT};"></span>{name}</span><strong>{format_currency(value)}</strong></div>', unsafe_allow_html=True)


# ============================================================================
# 13. GESTÃO DE CONTAS BANCÁRIAS
# ============================================================================

with st.container(border=True):
    st.markdown('<div class="panel-title">Minhas Contas 💳</div>', unsafe_allow_html=True)
    with st.form("account_form", clear_on_submit=True):
        ac1, ac2, ac3, ac4 = st.columns(4)
        with ac1: acc_choice = st.selectbox("Conta", [a["name"] for a in state["accounts"]])
        with ac2: operation = st.selectbox("Operação", ["Definir valor", "Adicionar", "Subtrair"])
        with ac3: acc_amount = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f", key="acc_amount")
        with ac4: acc_description = st.text_input("Descrição", placeholder="Ex.: Ajuste manual", key="acc_desc")

        if st.form_submit_button("Atualizar Conta"):
            acc = next((a for a in state["accounts"] if a["name"] == acc_choice), None)
            if acc:
                if operation == "Definir valor": acc["balance"] = float(acc_amount)
                elif operation == "Adicionar": acc["balance"] += float(acc_amount)
                else: acc["balance"] -= float(acc_amount)

                if acc_description.strip():
                    state["transactions"].insert(0, {"id": str(uuid.uuid4()), "type": "expense" if operation == "Subtrair" else "income", "category": "Ajuste", "description": acc_description.strip(), "amount": float(acc_amount), "date": date.today().isoformat(), "month": state["period"], "accountId": acc["id"], "accountName": acc["name"]})
                save_state(); st.rerun()

    if not state["accounts"]: st.markdown('<div class="empty-state">Nenhuma conta.</div>', unsafe_allow_html=True)
    else:
        for a in state["accounts"]:
            neg = a["balance"] < 0
            st.markdown(f'<div class="account-item"><div><strong>{a["name"]}</strong><div style="color:{MUTED}; font-size:0.9rem; font-weight: 600;">{"Saldo negativo" if neg else "Saldo disponível"}</div></div><div class="acc-balance {"negative" if neg else ""}">{format_currency(a["balance"])}</div></div>', unsafe_allow_html=True)


# ============================================================================
# 14. GESTÃO DE INVESTIMENTOS AUTOMATIZADA
# ============================================================================

with st.container(border=True):
    st.markdown('<div class="panel-title">Meus Investimentos 📈</div>', unsafe_allow_html=True)
    st.caption("O valor dos fundos é extraído em tempo real de acordo com as cotações oficiais e o Banco Central.")

    iv1, iv2, iv3 = st.columns(3)
    iv1.metric("Total investido (Seu bolso)", format_currency(invested_principal_total))
    iv2.metric("Valor atualizado do Patrimônio", format_currency(invested_current_total))
    iv3.metric("Rendimento acumulado no mercado", format_currency(investment_gain_total))

    st.write("")
    
    st.markdown(f"**<span style='color:{TEXT}; font-size:1.1rem;'>Novo investimento</span>**", unsafe_allow_html=True)

    bb_select = st.selectbox("Selecione o Fundo", BB_INVESTMENT_OPTIONS, key="bb_select")

    with st.form("investment_form", clear_on_submit=True):
        ic1, ic2, ic3 = st.columns(3)
        with ic1:
            if "Outro" in bb_select:
                inv_name = st.text_input("Nome do investimento", placeholder="Ex.: Ações PETR4")
            else:
                inv_name = st.text_input("Nome do investimento", value=bb_select, disabled=True)

        with ic2:
            inv_amount = st.number_input("Valor investido (R$)", min_value=0.0, step=0.01, format="%.2f", key="inv_amount")
        
        with ic3:
            inv_start = st.date_input("Data do Aporte (Importante para calcular rendimento)", value=date.today(), key="inv_start")

        # Mostra o painel de juros APENAS se a pessoa escolher "Outro"
        if "Outro" in bb_select:
            with st.expander("Configurar juros (Apenas para investimentos manuais)"):
                ix1, ix2 = st.columns(2)
                with ix1: inv_rate = st.number_input("Taxa de juros (%)", min_value=0.0, step=0.01, value=0.0, format="%.2f", key="inv_rate")
                with ix2: inv_rate_period = st.selectbox("Período", RATE_PERIODS, key="inv_rate_period")
        else:
            inv_rate = 0.0
            inv_rate_period = "Mensal"
            st.info("💡 Este fundo será atualizado **automaticamente** pelas cotações reais do mercado e CDI do Banco Central.")

        if st.form_submit_button("Salvar investimento 💰"):
            nome_final = inv_name.strip() if "Outro" in bb_select else bb_select
            if not nome_final: 
                st.warning("Informe um nome para o investimento.")
            else:
                state["investments"].append({
                    "id": str(uuid.uuid4()),
                    "name": nome_final,
                    "location": "Banco do Brasil" if "Outro" not in bb_select else "Corretora",
                    "initial_amount": float(inv_amount),
                    "rate": float(inv_rate),
                    "rate_period": inv_rate_period,
                    "start_date": inv_start.isoformat(),
                    "contributions": []
                })
                save_state(); st.rerun()

    st.write("")

    if not state["investments"]: st.markdown('<div class="empty-state">Nenhum investimento cadastrado.</div>', unsafe_allow_html=True)
    else:
        for inv in state["investments"]:
            current_value = investment_current_value(inv)
            gain = current_value - investment_principal(inv)
            gain_cls, gain_sign = ("positive", "+") if gain > 0.005 else ("neutral", "")
            
            st.markdown(f'<div class="inv-card"><div class="inv-top"><div><div class="inv-name">{inv["name"]}</div><div class="inv-meta">{inv["location"]} • comprado em {inv["start_date"]}</div><div style="margin-top:0.6rem;"><span class="inv-badge">{rate_label(inv)}</span></div></div><div><div class="inv-value">{format_currency(current_value)}</div><div class="inv-gain {gain_cls}">{gain_sign}{format_currency(gain)} de variação</div></div></div></div>', unsafe_allow_html=True)
            if st.columns([5, 1])[1].button("Remover", key=f"rm_i_{inv['id']}"):
                state["investments"] = [x for x in state["investments"] if x["id"] != inv["id"]]; save_state(); st.rerun()

    st.write("")
    
    with st.form("invest_more_form", clear_on_submit=True):
        st.markdown(f"**<span style='color:{TEXT}; font-size:1.1rem;'>Adicionar novo aporte em fundo existente</span>**", unsafe_allow_html=True)
        if state["investments"]:
            im1, im2, im3 = st.columns([2, 1, 1])
            with im1: inv_choice = st.selectbox("Investimento", [f'{i["name"]} — {format_currency(investment_current_value(i))}' for i in state["investments"]])
            with im2: extra_amount = st.number_input("Valor do aporte", min_value=0.0, step=0.01, format="%.2f", key="extra_amount")
            with im3: extra_date = st.date_input("Data do aporte", value=date.today(), key="extra_date")
            
            if st.form_submit_button("Adicionar aporte 💎"):
                if extra_amount <= 0: st.warning("Informe um valor maior que zero.")
                else:
                    idx = [f'{i["name"]} — {format_currency(investment_current_value(i))}' for i in state["investments"]].index(inv_choice)
                    state["investments"][idx].setdefault("contributions", []).append({"id": str(uuid.uuid4()), "amount": float(extra_amount), "date": extra_date.isoformat()})
                    save_state(); st.rerun()
        else:
            st.caption("Cadastre um investimento primeiro.")
            st.form_submit_button("Adicionar aporte", disabled=True)
