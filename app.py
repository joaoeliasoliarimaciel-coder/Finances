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

# Fundo atualizado: Flores, Coroas, Estrelas e Laços
BG_PATTERN = "url(\"data:image/svg+xml,%3Csvg width='160' height='160' viewBox='0 0 160 160' xmlns='http://www.w3.org/2000/svg'%3E%3Ctext x='20' y='40' font-size='24' opacity='0.35'%3E🌸%3C/text%3E%3Ctext x='100' y='40' font-size='24' opacity='0.35'%3E👑%3C/text%3E%3Ctext x='20' y='120' font-size='24' opacity='0.35'%3E⭐%3C/text%3E%3Ctext x='100' y='120' font-size='24' opacity='0.35'%3E🎀%3C/text%3E%3C/svg%3E\")"

st.set_page_config(page_title="Nossas Finanças", page_icon="👑", layout="wide")

if "princess_reaction" not in st.session_state:
    st.session_state.princess_reaction = None

# ============================================================================
# 2. SISTEMA DE LOGIN
# ============================================================================

def get_credentials():
    try:
        if hasattr(st, "secrets") and "credentials" in st.secrets:
            creds = dict(st.secrets["credentials"])
            if creds:
                return creds
    except Exception:
        pass
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
    if salt is None:
        salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${derived.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, _ = stored_hash.split("$", 1)
    except (ValueError, AttributeError):
        return False
    return hash_password(password, salt) == stored_hash

def username_taken(username: str, registered_users: dict) -> bool:
    return username in CREDENTIALS or username in registered_users

def login_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700&family=Poppins:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
        .stApp {{
            background-color: {BG_1};
            background-image: {BG_PATTERN},
                              radial-gradient(circle at 15% 10%, {BG_2}, transparent 55%),
                              radial-gradient(circle at 85% 90%, #ffcbe0, transparent 55%);
        }}
        .login-wrap {{
            max-width: 440px;
            margin: 6vh auto 1.2rem auto;
            padding: 2.4rem 2.2rem 1.4rem 2.2rem;
            background: {PANEL};
            border-radius: 28px;
            box-shadow: 0 25px 60px rgba(255, 20, 147, 0.25);
            border: 2px solid {ACCENT};
            text-align: center;
        }}
        .login-wrap .icon {{ font-size: 3rem; margin-bottom: 0.2rem; }}
        .login-wrap h1 {{ font-family: 'Playfair Display', serif; color: {ACCENT}; font-size: 2.4rem; font-weight: 700; margin: 0; }}
        .login-wrap p {{ color: {TEXT}; font-size: 1rem; font-weight: 600; }}
        div[data-testid="stForm"] {{ max-width: 440px; margin: 0 auto; border: none !important; background: transparent !important; padding: 0 !important; }}
        label, .stTextInput label p {{ color: {TEXT} !important; font-weight: 700 !important; }}
        input {{ background-color: {PANEL_2} !important; color: {TEXT} !important; border-radius: 12px !important; border: 2px solid rgba(255, 20, 147, 0.4) !important; }}
        .stButton>button, .stFormSubmitButton>button {{
            border: 0; border-radius: 12px; font-weight: 700; background: linear-gradient(135deg, {ACCENT}, {ACCENT_2});
            color: #ffffff !important; width: 100%; padding: 0.75rem 1.1rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def login_screen():
    login_css()
    st.markdown('<div class="login-wrap"><div class="icon">👑</div><h1>Nossas Finanças</h1><p>Entre com sua conta.</p></div>', unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs(["Entrar", "Criar conta"])

    with tab_login:
        with st.form("login_form"):
            user = st.text_input("Usuário", key="login_user")
            pwd = st.text_input("Senha", type="password", key="login_pwd")
            login_submitted = st.form_submit_button("Entrar 💖")

    with tab_signup:
        with st.form("signup_form", clear_on_submit=True):
            new_user = st.text_input("Escolha um usuário", key="signup_user")
            new_pwd = st.text_input("Escolha uma senha", type="password", key="signup_pwd")
            new_pwd_confirm = st.text_input("Confirme a senha", type="password", key="signup_pwd_confirm")
            signup_submitted = st.form_submit_button("Criar conta ✨")

    if login_submitted:
        registered_users = load_users()
        user_clean = (user or "").strip()
        if user_clean in CREDENTIALS and pwd == CREDENTIALS[user_clean]:
            st.session_state.authenticated = True
            st.session_state.username = user_clean
            st.rerun()
        elif user_clean in registered_users and verify_password(pwd, registered_users[user_clean].get("password_hash", "")):
            st.session_state.authenticated = True
            st.session_state.username = user_clean
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

    if signup_submitted:
        registered_users = load_users()
        user_clean = (new_user or "").strip()
        if not user_clean or len(new_pwd) < 6:
            st.warning("Preencha usuário e senha (mínimo 6 caracteres).")
        elif new_pwd != new_pwd_confirm:
            st.warning("As senhas não coincidem.")
        elif username_taken(user_clean, registered_users):
            st.warning("Usuário já existe.")
        else:
            registered_users[user_clean] = {"password_hash": hash_password(new_pwd), "created_at": datetime.now().isoformat()}
            save_users(registered_users)
            st.session_state.authenticated = True
            st.session_state.username = user_clean
            st.success("Conta criada! Entrando...")
            st.rerun()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login_screen()
    st.stop()


# ============================================================================
# 3. SALVAMENTO E CARREGAMENTO
# ============================================================================

def default_state():
    return {
        "transactions": [],
        "investments": [],
        "accounts": [dict(a) for a in DEFAULT_ACCOUNTS],
        "period": date.today().strftime("%Y-%m"),
    }

def migrate_investments(investments):
    migrated = []
    for inv in investments:
        if "initial_amount" not in inv:
            inv = {
                "id": inv.get("id", str(uuid.uuid4())),
                "name": inv.get("name", "Investimento"),
                "location": inv.get("location", "Sem local"),
                "initial_amount": float(inv.get("amount", 0.0)),
                "rate": 0.0,
                "rate_period": "Mensal",
                "start_date": date.today().isoformat(),
                "contributions": [],
            }
        else:
            inv.setdefault("contributions", [])
            inv.setdefault("rate", 0.0)
            inv.setdefault("rate_period", "Mensal")
            inv.setdefault("start_date", date.today().isoformat())
            inv.setdefault("location", "Sem local")
        migrated.append(inv)
    return migrated

def load_state():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.setdefault("transactions", [])
            data.setdefault("investments", [])
            data.setdefault("accounts", [dict(a) for a in DEFAULT_ACCOUNTS])
            data.setdefault("period", date.today().strftime("%Y-%m"))
            data["investments"] = migrate_investments(data["investments"])
            return data
        except Exception:
            return default_state()
    return default_state()

def save_state():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.state, f, ensure_ascii=False, indent=2)

if "state" not in st.session_state:
    st.session_state.state = load_state()

state = st.session_state.state

if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = False


# ============================================================================
# 4. FUNÇÕES DE APOIO E CÁLCULOS
# ============================================================================

def format_currency(value: float) -> str:
    value = value or 0
    s = f"{value:,.2f}"
    return f"R$ {s.replace(',', 'X').replace('.', ',').replace('X', '.')}"

def month_options(months_back=18, months_fwd=12):
    today = date.today()
    options = []
    y, m = today.year, today.month
    for idx in range(-months_back, months_fwd + 1):
        total = (y * 12 + (m - 1)) + idx
        yy, mm = divmod(total, 12)
        options.append(f"{yy:04d}-{mm + 1:02d}")
    return options

MONTH_NAMES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

def format_month(value: str) -> str:
    try:
        y, m = value.split("-")
        return f"{MONTH_NAMES[int(m) - 1].capitalize()} de {y}"
    except:
        return value

def find_account(account_id):
    return next((a for a in state["accounts"] if a["id"] == account_id), None)

def monthly_rate(rate_pct: float, period: str) -> float:
    r = (rate_pct or 0) / 100
    return (1 + r) ** (1 / 12) - 1 if period == "Anual" else r

def months_elapsed(start_iso: str, as_of: date) -> float:
    try:
        start = date.fromisoformat(start_iso)
    except:
        start = as_of
    delta_days = (as_of - start).days
    return 0.0 if delta_days <= 0 else delta_days / 30.4368

def investment_principal(inv) -> float:
    total = inv.get("initial_amount", 0.0)
    total += sum(c["amount"] for c in inv.get("contributions", []))
    return total

def investment_current_value(inv, as_of: date = None) -> float:
    as_of = as_of or date.today()
    r_m = monthly_rate(inv.get("rate", 0.0), inv.get("rate_period", "Mensal"))
    value = inv.get("initial_amount", 0.0) * (1 + r_m) ** months_elapsed(inv.get("start_date"), as_of)
    for c in inv.get("contributions", []):
        value += c["amount"] * (1 + r_m) ** months_elapsed(c["date"], as_of)
    return value

def rate_label(inv) -> str:
    rate = inv.get("rate", 0.0)
    period = "ao mês" if inv.get("rate_period", "Mensal") == "Mensal" else "ao ano"
    return f"{rate:.2f}% {period}".replace(".", ",")


# ============================================================================
# 5. ESTILOS (CSS DO APP PRINCIPAL)
# ============================================================================

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700&family=Poppins:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
    
    .stApp {{ 
        background-color: {BG_1};
        background-image: {BG_PATTERN}, 
                          radial-gradient(circle at 10% 0%, {BG_2}, transparent 50%), 
                          radial-gradient(circle at 90% 100%, #ffcbe0, transparent 50%); 
        color: {TEXT}; 
    }}
    
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
    
    .inv-card {{ padding: 1.2rem 1.4rem; border-radius: 20px; background: {PANEL_2}; border: 2px solid rgba(255,20,147,0.25); margin-bottom: 1rem; }}
    .inv-card .inv-name {{ font-weight: 800; color: {TEXT}; font-size: 1.2rem; }}
    
    section[data-testid="stSidebar"] {{ background: rgba(255, 240, 246, 0.95); border-right: 2px solid rgba(255,20,147,0.2); backdrop-filter: blur(5px); }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================================
# 6. SIDEBAR E CABEÇALHO
# ============================================================================

with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align:center; padding: 1rem 0 1.5rem 0;">
            <div style="font-size:3.5rem;">👑</div>
            <div style="font-family:'Playfair Display', serif; font-weight:700; font-size:1.6rem; color:{ACCENT};">Nossas Finanças</div>
            <div style="color:{TEXT}; font-size:1rem; font-weight: 600;">Olá, {st.session_state.get('username', '')}!</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Sair da Conta 👋", use_container_width=True, type="secondary"):
        st.session_state.authenticated = False
        st.rerun()

st.markdown(
    """
    <div class="hero">
        <div>
            <p class="eyebrow">Controle financeiro do casal</p>
            <h1>Nossas Finanças</h1>
            <p class="subtitle">Organize gastos, ganhos e acompanhe o patrimônio.</p>
        </div>
        <div class="hero-icon">👑</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================================
# 7. ANIMAÇÕES DA PRINCESA (APENAS A PRINCESA)
# ============================================================================
# Mudança: O z-index agora é super alto (999999) para não ficar escondida atrás de nada.
# As funções de balões e neve foram 100% removidas.

if st.session_state.princess_reaction == "happy":
    st.markdown(
        """
        <style>
        .happy-princess {
            position: fixed;
            bottom: 30px;
            left: -300px;
            z-index: 999999 !important;
            animation: runAcross 4.5s linear forwards;
            pointer-events: none;
        }
        @keyframes runAcross {
            0% { left: -300px; }
            100% { left: 110vw; visibility: hidden; }
        }
        </style>
        <img src="https://media.tenor.com/7wMvD2hT4l4AAAAi/cinderella-disney.gif" class="happy-princess" width="280">
        """, unsafe_allow_html=True
    )
    st.session_state.princess_reaction = None 

elif st.session_state.princess_reaction == "sad":
    st.markdown(
        """
        <style>
        .sad-princess {
            position: fixed;
            bottom: -350px;
            right: 5%;
            z-index: 999999 !important;
            animation: riseAndCry 5.5s ease-in-out forwards;
            pointer-events: none;
        }
        @keyframes riseAndCry {
            0% { bottom: -350px; opacity: 0; }
            20% { bottom: 0px; opacity: 1; }
            80% { bottom: 0px; opacity: 1; }
            100% { bottom: -350px; opacity: 0; visibility: hidden; }
        }
        </style>
        <img src="https://media.tenor.com/L4u2zEEDN20AAAAi/crying-cinderella.gif" class="sad-princess" width="280">
        """, unsafe_allow_html=True
    )
    st.session_state.princess_reaction = None 


# ============================================================================
# 8. FILTRO DE MÊS E FORMULÁRIO DE NOVA MOVIMENTAÇÃO
# ============================================================================

with st.container(border=True):
    top_col1, top_col2 = st.columns([3, 1])
    
    with top_col1:
        st.markdown('<div class="panel-title">Nova movimentação ✨</div>', unsafe_allow_html=True)
    
    with top_col2:
        options = month_options()
        if state["period"] not in options:
            options.append(state["period"])
            options.sort()
        new_period = st.selectbox(
            "Mês de referência", options, index=options.index(state["period"]),
            format_func=format_month
        )
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

        submitted = st.form_submit_button("Adicionar Movimentação 💸")

        if submitted:
            if not description.strip() or amount <= 0:
                st.warning("Preencha a descrição e um valor maior que zero.")
            else:
                acc = next((a for a in state["accounts"] if a["name"] == account_choice), None) if account_choice != "Sem conta" else None
                payload = {
                    "id": str(uuid.uuid4()),
                    "type": "expense" if type_label == "Gasto" else "income",
                    "category": category,
                    "description": description.strip(),
                    "amount": float(amount),
                    "date": date_value.isoformat(),
                    "month": state["period"],
                    "accountId": acc["id"] if acc else None,
                    "accountName": acc["name"] if acc else None,
                }
                if acc:
                    if payload["type"] == "expense": acc["balance"] -= payload["amount"]
                    else: acc["balance"] += payload["amount"]

                state["transactions"].insert(0, payload)
                save_state()
                
                # Seta o estado da animação 
                if payload["type"] == "income":
                    st.session_state.princess_reaction = "happy"
                else:
                    st.session_state.princess_reaction = "sad"
                    
                st.rerun()


# ============================================================================
# 9. CÁLCULOS TOTAIS E MÉTRICAS
# ============================================================================

current_transactions = [t for t in state["transactions"] if t["month"] == state["period"]]
income = sum(t["amount"] for t in current_transactions if t["type"] == "income")
expenses = sum(t["amount"] for t in current_transactions if t["type"] == "expense")
balance = income - expenses
accounts_total = sum(a["balance"] for a in state["accounts"])
invested_current_total = sum(investment_current_value(i) for i in state["investments"])
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
# 10. HISTÓRICO DE MOVIMENTAÇÕES
# ============================================================================

with st.container(border=True):
    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown('<div class="panel-title">Histórico de Movimentações 📋</div>', unsafe_allow_html=True)
    with h2:
        if st.button("Limpar dados", type="secondary", use_container_width=True):
            st.session_state.confirm_clear = True

    if st.session_state.confirm_clear:
        st.warning("Tem certeza que deseja apagar TODOS os dados?")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("Confirmar exclusão", type="secondary"):
                st.session_state.state = default_state()
                state = st.session_state.state
                save_state()
                st.session_state.confirm_clear = False
                st.rerun()
        with cc2:
            if st.button("Cancelar"):
                st.session_state.confirm_clear = False
                st.rerun()

    if not current_transactions:
        st.markdown('<div style="text-align:center; padding:1.5rem; color:#5c3a58;">Nenhuma movimentação neste mês! 🌷</div>', unsafe_allow_html=True)
    else:
        for t in current_transactions:
            meta_line = f'{t["category"]} • {t["date"]}'
            if t.get("accountName"): meta_line += f' • {t["accountName"]}'
            sign, cls = ("+", "income") if t["type"] == "income" else ("-", "expense")

            row = st.container()
            with row:
                rc1, rc2, rc3 = st.columns([5, 2, 1])
                with rc1:
                    st.markdown(f'<div class="t-meta"><strong>{t["description"]}</strong><span>{meta_line}</span></div>', unsafe_allow_html=True)
                with rc2:
                    st.markdown(f'<div class="t-amount {cls}">{sign}{format_currency(t["amount"])}</div>', unsafe_allow_html=True)
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
