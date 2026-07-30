import hashlib
import json
import os
import secrets
import uuid
from datetime import date, datetime, timedelta

import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# Config & constantes
# ----------------------------------------------------------------------------

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

# Paleta de Alto Contraste (Amigável para Daltonismo/Baixa Visão)
COLORS = [
    "#CC79A7",  # Rosa/Púrpura (Mantém o estilo Barbie)
    "#0072B2",  # Azul escuro
    "#E69F00",  # Laranja
    "#009E73",  # Verde esmeralda
    "#56B4E9",  # Azul claro
    "#D55E00",  # Vermelho/Laranja escuro
    "#F0E442",  # Amarelo brilhante
]

SUCCESS_CHART = "#009E73"  # Verde seguro
DANGER_CHART = "#D55E00"   # Laranja escuro (mais distinguível que o vermelho puro)

# Paleta UI Barbie Profissional
ACCENT = "#ff1493"        # Deep Barbie Pink (Principal)
ACCENT_2 = "#d500f9"      # Roxo/Lilás vibrante
DANGER = "#b71c1c"        # Vermelho bem escuro para textos
WARNING = "#e65100"       # Laranja/Âmbar escuro
SUCCESS = "#0a7040"       # Verde escuro para textos
MUTED = "#5c3a58"         # Cinza-arroxeado escuro (bem legível)
TEXT = "#1f0a1c"          # Quase preto com fundo magenta - ALTO CONTRASTE
PANEL = "#ffffff"         # Branco puro para os cards (fundo perfeito para leitura)
PANEL_2 = "#fff0f6"       # Rosa extremamente claro para fundos secundários
BG_1 = "#ffe4e1"          # Fundo geral rosa pastel
BG_2 = "#ffb6c1"          # Detalhes de gradiente em rosa claro

st.set_page_config(page_title="Nossas Finanças", page_icon="🎀", layout="wide")

# ----------------------------------------------------------------------------
# Login
# ----------------------------------------------------------------------------

def get_credentials():
    """Lê usuário/senha de st.secrets se existir; nunca quebra o app se não existir."""
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
            background: radial-gradient(circle at 15% 10%, {BG_2}, transparent 55%),
                        radial-gradient(circle at 85% 90%, #ffcbe0, transparent 55%),
                        {BG_1};
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
        .login-wrap h1 {{
            font-family: 'Playfair Display', serif;
            color: {ACCENT};
            font-size: 2.4rem;
            font-weight: 700;
            margin: 0.2rem 0 0.1rem 0;
        }}
        .login-wrap p {{ color: {TEXT}; margin-bottom: 0.4rem; font-size: 1rem; font-weight: 600; }}
        div[data-testid="stForm"] {{
            max-width: 440px;
            margin: 0 auto;
            border: none !important;
            background: transparent !important;
            padding: 0 !important;
        }}
        label, .stTextInput label p {{
            color: {TEXT} !important;
            font-weight: 700 !important;
            font-size: 1.05rem !important;
        }}
        input {{
            background-color: {PANEL_2} !important;
            color: {TEXT} !important;
            border-radius: 12px !important;
            border: 2px solid rgba(255, 20, 147, 0.4) !important;
            font-weight: 600 !important;
            font-size: 1.05rem !important;
        }}
        input::placeholder {{ color: {MUTED} !important; opacity: 0.9; }}
        .stButton>button, .stFormSubmitButton>button {{
            border: 0;
            border-radius: 12px;
            font-weight: 700;
            background: linear-gradient(135deg, {ACCENT}, {ACCENT_2});
            color: #ffffff !important;
            width: 100%;
            padding: 0.75rem 1.1rem;
            font-size: 1.1rem;
            box-shadow: 0 8px 20px rgba(255, 20, 147, 0.3);
        }}
        .stButton>button:hover, .stFormSubmitButton>button:hover {{
            opacity: 0.9;
            transform: translateY(-2px);
            transition: all 0.2s ease-in-out;
            color: #ffffff !important;
        }}
        div[data-testid="stTabs"] {{
            max-width: 440px;
            margin: 0 auto;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"] {{
            font-weight: 700;
            color: {MUTED};
            font-size: 1.1rem;
        }}
        div[data-testid="stTabs"] button[aria-selected="true"] {{
            color: {ACCENT} !important;
        }}
        div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] {{
            background-color: {ACCENT} !important;
            height: 4px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def login_screen():
    login_css()
    st.markdown(
        """
        <div class="login-wrap">
            <div class="icon">🌸</div>
            <h1>Nossas Finanças</h1>
            <p>Entre com sua conta ou crie uma nova para acessar seu espaço financeiro.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_signup = st.tabs(["Entrar", "Criar conta"])

    with tab_login:
        with st.form("login_form"):
            user = st.text_input("Usuário", placeholder="Digite seu usuário", key="login_user")
            pwd = st.text_input("Senha", type="password", placeholder="Digite sua senha", key="login_pwd")
            login_submitted = st.form_submit_button("Entrar 💖")

    with tab_signup:
        st.caption("Crie um usuário e senha para acessar as finanças. Todos que tiverem uma conta veem os mesmos dados.")
        with st.form("signup_form", clear_on_submit=True):
            new_user = st.text_input("Escolha um usuário", placeholder="Ex.: joao", key="signup_user")
            new_pwd = st.text_input("Escolha uma senha", type="password", placeholder="Mínimo 6 caracteres", key="signup_pwd")
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
            st.error("Usuário ou senha incorretos. Confira e tente novamente.")

    if signup_submitted:
        registered_users = load_users()
        user_clean = (new_user or "").strip()
        if not user_clean or not new_pwd:
            st.warning("Preencha usuário e senha para criar sua conta.")
        elif len(new_pwd) < 6:
            st.warning("A senha precisa ter pelo menos 6 caracteres.")
        elif new_pwd != new_pwd_confirm:
            st.warning("As senhas não coincidem. Tente novamente.")
        elif username_taken(user_clean, registered_users):
            st.warning("Esse usuário já existe. Escolha outro nome ou faça login na aba 'Entrar'.")
        else:
            registered_users[user_clean] = {
                "password_hash": hash_password(new_pwd),
                "created_at": datetime.now().isoformat(),
            }
            save_users(registered_users)
            st.session_state.authenticated = True
            st.session_state.username = user_clean
            st.success("Conta criada com sucesso! Entrando...")
            st.rerun()


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login_screen()
    st.stop()

# ----------------------------------------------------------------------------
# Persistência
# ----------------------------------------------------------------------------

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
                "location": inv.get("location", "Sem local informado"),
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
            inv.setdefault("location", "Sem local informado")
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

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def format_currency(value: float) -> str:
    value = value or 0
    s = f"{value:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def month_options(months_back=18, months_fwd=12):
    today = date.today()
    options = []
    y, m = today.year, today.month
    idx = -months_back
    while idx <= months_fwd:
        total = (y * 12 + (m - 1)) + idx
        yy, mm = divmod(total, 12)
        mm += 1
        options.append(f"{yy:04d}-{mm:02d}")
        idx += 1
    return options


MONTH_NAMES = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def format_month(value: str) -> str:
    try:
        y, m = value.split("-")
        return f"{MONTH_NAMES[int(m) - 1].capitalize()} de {y}"
    except Exception:
        return value


def account_name(account_id):
    if not account_id:
        return None
    acc = next((a for a in state["accounts"] if a["id"] == account_id), None)
    return acc["name"] if acc else None


def find_account(account_id):
    return next((a for a in state["accounts"] if a["id"] == account_id), None)

# ----------------------------------------------------------------------------
# Cálculo de juros
# ----------------------------------------------------------------------------

def monthly_rate(rate_pct: float, period: str) -> float:
    r = (rate_pct or 0) / 100
    if period == "Anual":
        return (1 + r) ** (1 / 12) - 1
    return r

def months_elapsed(start_iso: str, as_of: date) -> float:
    try:
        start = date.fromisoformat(start_iso)
    except Exception:
        start = as_of
    delta_days = (as_of - start).days
    if delta_days <= 0:
        return 0.0
    return delta_days / 30.4368

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
    period = inv.get("rate_period", "Mensal")
    suffix = "ao mês" if period == "Mensal" else "ao ano"
    return f"{rate:.2f}% {suffix}".replace(".", ",")

# ----------------------------------------------------------------------------
# CSS Principal - Alta legibilidade & Estilo
# ----------------------------------------------------------------------------

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700&family=Poppins:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Poppins', sans-serif;
    }}

    .stApp {{
        background: radial-gradient(circle at 10% 0%, {BG_2}, transparent 50%),
                    radial-gradient(circle at 90% 100%, #ffcbe0, transparent 50%),
                    {BG_1};
        color: {TEXT};
    }}

    .block-container {{
        max-width: 1200px;
        padding-top: 1.5rem;
    }}

    /* HERO SECTION */
    .hero {{
        padding: 2.5rem 2.2rem;
        border-radius: 26px;
        background: linear-gradient(120deg, #ffffff, {PANEL_2});
        border: 2px solid {ACCENT};
        margin-bottom: 2rem;
        box-shadow: 0 18px 45px rgba(255, 20, 147, 0.2);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        flex-wrap: wrap;
    }}
    .hero .eyebrow {{
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.25rem;
        color: {ACCENT};
        font-weight: 800;
        font-size: 0.85rem;
    }}
    .hero h1 {{
        font-family: 'Playfair Display', serif;
        margin: 0.15rem 0;
        font-size: 2.8rem;
        color: {TEXT};
        font-weight: 700;
    }}
    .hero p.subtitle {{
        color: {TEXT};
        max-width: 620px;
        margin: 0;
        font-weight: 500;
        font-size: 1.05rem;
    }}
    .hero .hero-icon {{
        font-size: 4rem;
        text-shadow: 2px 2px 15px rgba(255,20,147,0.3);
    }}

    .panel-title {{
        font-family: 'Playfair Display', serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: {TEXT};
        margin-bottom: 1rem;
        border-bottom: 2px solid rgba(255,20,147,0.2);
        padding-bottom: 0.5rem;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: {PANEL};
        border: 2px solid rgba(255, 20, 147, 0.3) !important;
        border-radius: 22px !important;
        box-shadow: 0 12px 30px rgba(255, 20, 147, 0.12);
        padding: 0.5rem;
    }}

    /* METRICS */
    div[data-testid="stMetric"] {{
        background: {PANEL_2};
        border-radius: 16px;
        padding: 1rem;
        border: 2px solid rgba(255, 20, 147, 0.25);
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }}
    div[data-testid="stMetricLabel"] {{
        color: {TEXT};
        font-weight: 700;
        font-size: 1rem;
    }}
    div[data-testid="stMetricValue"] {{
        color: {TEXT};
        font-weight: 800;
        font-size: 1.6rem;
    }}

    /* BUTTONS */
    .stButton>button, .stFormSubmitButton>button {{
        border: 0;
        border-radius: 12px;
        font-weight: 700;
        background: linear-gradient(135deg, {ACCENT}, {ACCENT_2});
        color: white;
        padding: 0.65rem 1.2rem;
        font-size: 1.05rem;
        box-shadow: 0 5px 15px rgba(255,20,147,0.3);
    }}
    .stButton>button:hover, .stFormSubmitButton>button:hover {{
        color: white;
        transform: translateY(-2px);
        transition: all 0.2s ease;
        opacity: 0.95;
    }}

    button[kind="secondary"] {{
        background: {PANEL_2} !important;
        border: 2px solid {ACCENT} !important;
        color: {TEXT} !important;
        box-shadow: none;
    }}

    /* INPUTS */
    label, .stSelectbox label p, .stTextInput label p, .stNumberInput label p {{
        font-weight: 700 !important;
        color: {TEXT} !important;
    }}
    input, textarea, select, .stSelectbox div[data-baseweb="select"] > div {{
        background-color: {PANEL_2} !important;
        color: {TEXT} !important;
        border-radius: 12px !important;
        border: 2px solid rgba(255,20,147,0.3) !important;
        font-weight: 600 !important;
    }}

    /* LIST ITEMS */
    .transaction-item, .account-item, .investment-item {{
        padding: 1rem 1.2rem;
        border-radius: 16px;
        background: {PANEL_2};
        margin-bottom: 0.8rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        border: 2px solid rgba(255,20,147,0.2);
    }}
    .t-meta strong {{ display:block; color: {TEXT}; font-size: 1.1rem; }}
    .t-meta span {{ color: {MUTED}; font-size: 0.95rem; font-weight: 600; }}
    .t-amount {{ font-weight: 800; font-size: 1.15rem; white-space: nowrap; }}
    .t-amount.income {{ color: {SUCCESS}; }}
    .t-amount.expense {{ color: {DANGER}; }}
    
    .acc-balance {{ font-weight: 800; font-size: 1.2rem; color: {SUCCESS}; }}
    .acc-balance.negative {{ color: {DANGER}; }}
    
    .empty-state {{
        padding: 1.5rem;
        border-radius: 16px;
        background: {PANEL_2};
        color: {TEXT};
        text-align: center;
        font-weight: 600;
        border: 2px dashed rgba(255,20,147,0.4);
    }}

    .legend-item {{
        display:flex; justify-content: space-between; color: {TEXT}; margin-bottom: 0.5rem; font-weight: 600; font-size: 1.05rem;
    }}
    .legend-badge {{
        width: 14px; height: 14px; border-radius: 4px; display:inline-block; margin-right: 0.6rem; border: 1px solid rgba(0,0,0,0.1);
    }}

    /* INVESTMENT CARDS */
    .inv-card {{
        padding: 1.2rem 1.4rem;
        border-radius: 20px;
        background: {PANEL_2};
        border: 2px solid rgba(255,20,147,0.25);
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(255,20,147,0.08);
    }}
    .inv-card .inv-top {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
    }}
    .inv-card .inv-name {{ font-weight: 800; color: {TEXT}; font-size: 1.2rem; }}
    .inv-card .inv-meta {{ color: {MUTED}; font-size: 0.95rem; font-weight: 600; margin-top: 0.2rem; }}
    .inv-badge {{
        display:inline-block;
        padding: 0.25rem 0.7rem;
        border-radius: 999px;
        background: {ACCENT};
        color: white;
        font-size: 0.85rem;
        font-weight: 700;
        white-space: nowrap;
        box-shadow: 0 2px 8px rgba(255,20,147,0.4);
    }}
    .inv-value {{ font-size: 1.4rem; font-weight: 800; color: {TEXT}; text-align: right; }}
    .inv-gain {{ font-size: 0.95rem; font-weight: 700; text-align: right; margin-top: 0.2rem; }}
    .inv-gain.positive {{ color: {SUCCESS}; }}
    .inv-gain.neutral {{ color: {MUTED}; }}

    section[data-testid="stSidebar"] {{
        background: {PANEL_2};
        border-right: 2px solid rgba(255,20,147,0.2);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Sidebar (usuário e logout)
# ----------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align:center; padding: 1rem 0 1.5rem 0;">
            <div style="font-size:3.5rem; text-shadow: 0 4px 10px rgba(255,20,147,0.3);">🎀</div>
            <div style="font-family:'Playfair Display', serif; font-weight:700; font-size:1.6rem; color:{ACCENT}; margin-top: 0.5rem;">Nossas Finanças</div>
            <div style="color:{TEXT}; font-size:1rem; font-weight: 600;">Olá, {st.session_state.get('username', '')}!</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Sair da Conta 👋", use_container_width=True, type="secondary"):
        st.session_state.authenticated = False
        st.rerun()

# ----------------------------------------------------------------------------
# Cabeçalho
# ----------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <div>
            <p class="eyebrow">Controle financeiro do casal</p>
            <h1>Nossas Finanças</h1>
            <p class="subtitle">Organize gastos, ganhos, investimentos, contas e acompanhe o patrimônio de vocês com clareza e estilo.</p>
        </div>
        <div class="hero-icon">🌸</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Nova movimentação
# ----------------------------------------------------------------------------

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
            "Mês", options, index=options.index(state["period"]),
            format_func=format_month, label_visibility="visible",
        )
        if new_period != state["period"]:
            state["period"] = new_period
            save_state()
            st.rerun()

    type_label = st.selectbox("Tipo", ["Gasto", "Ganho"], key="new_type")
    categories = EXPENSE_CATEGORIES if type_label == "Gasto" else INCOME_CATEGORIES

    with st.form("transaction_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            category = st.selectbox("Categoria", categories)
        with c2:
            account_names = ["Sem conta"] + [a["name"] for a in state["accounts"]]
            account_choice = st.selectbox("Conta", account_names)
        with c3:
            description = st.text_input("Descrição", placeholder="Ex.: Mercado da semana")

        c4, c5 = st.columns(2)
        with c4:
            amount = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        with c5:
            date_value = st.date_input("Data", value=date.today())

        submitted = st.form_submit_button("Adicionar Movimentação 💸")

        if submitted:
            if not description.strip() or amount <= 0:
                st.warning("Preencha a descrição e um valor maior que zero.")
            else:
                acc = None
                if account_choice != "Sem conta":
                    acc = next((a for a in state["accounts"] if a["name"] == account_choice), None)

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
                    if payload["type"] == "expense":
                        acc["balance"] -= payload["amount"]
                    else:
                        acc["balance"] += payload["amount"]

                state["transactions"].insert(0, payload)
                save_state()
                st.rerun()

# ----------------------------------------------------------------------------
# Cards de resumo
# ----------------------------------------------------------------------------

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

# ----------------------------------------------------------------------------
# Movimentações
# ----------------------------------------------------------------------------

with st.container(border=True):
    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown('<div class="panel-title">Histórico de Movimentações 📋</div>', unsafe_allow_html=True)
    with h2:
        if st.button("Limpar dados", type="secondary", use_container_width=True):
            st.session_state.confirm_clear = True

    if st.session_state.confirm_clear:
        st.warning("Tem certeza que deseja apagar todos os dados salvos? Esta ação não pode ser desfeita.")
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
        st.markdown('<div class="empty-state">Nenhuma movimentação para este período ainda. Comece a adicionar! 🌷</div>', unsafe_allow_html=True)
    else:
        for t in current_transactions:
            meta_line = f'{t["category"]} • {t["date"]}'
            if t.get("accountName"):
                meta_line += f' • {t["accountName"]}'
            sign = "+" if t["type"] == "income" else "-"
            cls = "income" if t["type"] == "income" else "expense"

            row = st.container()
            with row:
                rc1, rc2, rc3 = st.columns([5, 2, 1])
                with rc1:
                    st.markdown(
                        f'<div class="t-meta"><strong>{t["description"]}</strong><span>{meta_line}</span></div>',
                        unsafe_allow_html=True,
                    )
                with rc2:
                    st.markdown(
                        f'<div class="t-amount {cls}">{sign}{format_currency(t["amount"])}</div>',
                        unsafe_allow_html=True,
                    )
                with rc3:
                    if st.button("Remover", key=f"rm_t_{t['id']}"):
                        if t.get("accountId"):
                            acc = find_account(t["accountId"])
                            if acc:
                                if t["type"] == "expense":
                                    acc["balance"] += t["amount"]
                                else:
                                    acc["balance"] -= t["amount"]
                        state["transactions"] = [x for x in state["transactions"] if x["id"] != t["id"]]
                        save_state()
                        st.rerun()

# ----------------------------------------------------------------------------
# Contas
# ----------------------------------------------------------------------------

with st.container(border=True):
    st.markdown('<div class="panel-title">Minhas Contas 💳</div>', unsafe_allow_html=True)

    with st.form("account_form", clear_on_submit=True):
        ac1, ac2, ac3, ac4 = st.columns(4)
        with ac1:
            acc_choice = st.selectbox("Conta", [a["name"] for a in state["accounts"]])
        with ac2:
            operation = st.selectbox("Operação", ["Definir valor", "Adicionar", "Subtrair"])
        with ac3:
            acc_amount = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f", key="acc_amount")
        with ac4:
            acc_description = st.text_input("Descrição", placeholder="Ex.: Juros, ajuste manual", key="acc_desc")

        acc_submitted = st.form_submit_button("Atualizar Conta")

        if acc_submitted:
            acc = next((a for a in state["accounts"] if a["name"] == acc_choice), None)
            if acc:
                if operation == "Definir valor":
                    acc["balance"] = float(acc_amount)
                elif operation == "Adicionar":
                    acc["balance"] += float(acc_amount)
                else:
                    acc["balance"] -= float(acc_amount)

                if acc_description.strip():
                    state["transactions"].insert(0, {
                        "id": str(uuid.uuid4()),
                        "type": "expense" if operation == "Subtrair" else "income",
                        "category": "Ajuste",
                        "description": acc_description.strip(),
                        "amount": float(acc_amount),
                        "date": date.today().isoformat(),
                        "month": state["period"],
                        "accountId": acc["id"],
                        "accountName": acc["name"],
                    })
                save_state()
                st.rerun()

    if not state["accounts"]:
        st.markdown('<div class="empty-state">Nenhuma conta cadastrada.</div>', unsafe_allow_html=True)
    else:
        for a in state["accounts"]:
            neg = a["balance"] < 0
            st.markdown(
                f"""
                <div class="account-item">
                    <div>
                        <strong>{a['name']}</strong>
                        <div style="color:{MUTED}; font-size:0.9rem; font-weight: 600;">{'Saldo negativo' if neg else 'Saldo disponível'}</div>
                    </div>
                    <div class="acc-balance {'negative' if neg else ''}">{format_currency(a['balance'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ----------------------------------------------------------------------------
# Gráficos de Altíssimo Contraste e Acessibilidade
# ----------------------------------------------------------------------------

with st.container(border=True):
    st.markdown('<div class="panel-title">Análise Financeira 📊</div>', unsafe_allow_html=True)

    g1, g2 = st.columns([1.2, 0.8])

    with g1:
        st.markdown(f"**<span style='color:{TEXT}; font-size:1.1rem;'>Receitas x Despesas</span>**", unsafe_allow_html=True)
        bar_fig = go.Figure(
            data=[
                go.Bar(
                    x=["Ganhos", "Gastos"],
                    y=[income, expenses],
                    marker_color=[SUCCESS_CHART, DANGER_CHART], 
                    marker_line=dict(color=TEXT, width=1.5),    
                    text=[format_currency(income), format_currency(expenses)],
                    textposition="auto",
                    textfont=dict(color="white", size=16, weight="900"),
                    width=0.4,
                )
            ]
        )
        bar_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT, family="Poppins", size=14),
            yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)", visible=True),
            xaxis=dict(showgrid=False, color=TEXT, tickfont=dict(weight="bold", size=14)),
            margin=dict(l=10, r=10, t=30, b=10),
            height=320,
            showlegend=False,
        )
        st.plotly_chart(bar_fig, use_container_width=True)

    with g2:
        st.markdown(f"**<span style='color:{TEXT}; font-size:1.1rem;'>Despesas por categoria</span>**", unsafe_allow_html=True)
        expense_items = [t for t in current_transactions if t["type"] == "expense"]
        totals_by_cat = {}
        for t in expense_items:
            totals_by_cat[t["category"]] = totals_by_cat.get(t["category"], 0) + t["amount"]

        if not totals_by_cat:
            donut_fig = go.Figure(data=[go.Pie(labels=["Sem dados"], values=[1], hole=0.65,
                                                marker=dict(colors=[PANEL_2]), textinfo="none")])
        else:
            labels = list(totals_by_cat.keys())
            values = list(totals_by_cat.values())
            donut_fig = go.Figure(
                data=[
                    go.Pie(
                        labels=labels,
                        values=values,
                        hole=0.65,
                        marker=dict(
                            colors=COLORS * 3, 
                            line=dict(color=PANEL, width=3)
                        ),
                        textinfo="none",
                    )
                ]
            )
        donut_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT, family="Poppins"),
            margin=dict(l=10, r=10, t=30, b=10),
            height=320,
            showlegend=False,
            annotations=[dict(
                text=f"<b>Total:</b><br>{format_currency(sum(totals_by_cat.values()))}" if totals_by_cat else "Sem dados",
                x=0.5, y=0.5, font_size=16, showarrow=False, font_color=TEXT
            )],
        )
        st.plotly_chart(donut_fig, use_container_width=True)

        if totals_by_cat:
            for idx, (name, value) in enumerate(totals_by_cat.items()):
                color = COLORS[idx % len(COLORS)]
                st.markdown(
                    f"""
                    <div class="legend-item">
                        <span style="display:flex; align-items:center;">
                            <span class="legend-badge" style="background:{color}; border: 2px solid {TEXT};"></span>{name}
                        </span>
                        <strong>{format_currency(value)}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ----------------------------------------------------------------------------
# Investimentos
# ----------------------------------------------------------------------------

with st.container(border=True):
    st.markdown('<div class="panel-title">Meus Investimentos 📈</div>', unsafe_allow_html=True)
    st.caption("O valor de cada investimento é recalculado automaticamente com base na taxa de juros e no tempo desde o aporte.")

    iv1, iv2, iv3 = st.columns(3)
    iv1.metric("Total aportado", format_currency(invested_principal_total))
    iv2.metric("Valor atual (com juros)", format_currency(invested_current_total))
    iv3.metric("Rendimento acumulado", format_currency(investment_gain_total))

    st.write("")

    with st.form("investment_form", clear_on_submit=True):
        st.markdown(f"**<span style='color:{TEXT}; font-size:1.1rem;'>Novo investimento</span>**", unsafe_allow_html=True)
        ic1, ic2, ic3 = st.columns(3)
        with ic1:
            inv_name = st.text_input("Nome do investimento", placeholder="Ex.: Poupança")
        with ic2:
            inv_amount = st.number_input("Valor inicial aplicado", min_value=0.0, step=0.01, format="%.2f", key="inv_amount")
        with ic3:
            inv_location = st.text_input("Onde está aplicado", placeholder="Ex.: Banco, Tesouro, CDB")

        ic4, ic5, ic6 = st.columns(3)
        with ic4:
            inv_rate = st.number_input("Taxa de juros (%)", min_value=0.0, step=0.01, format="%.2f", key="inv_rate")
        with ic5:
            inv_rate_period = st.selectbox("Período da taxa", RATE_PERIODS, key="inv_rate_period")
        with ic6:
            inv_start = st.date_input("Data de início", value=date.today(), key="inv_start")

        inv_submitted = st.form_submit_button("Salvar investimento 💰")

        if inv_submitted:
            if not inv_name.strip():
                st.warning("Informe um nome para o investimento.")
            else:
                state["investments"].append({
                    "id": str(uuid.uuid4()),
                    "name": inv_name.strip(),
                    "location": inv_location.strip() or "Sem local informado",
                    "initial_amount": float(inv_amount),
                    "rate": float(inv_rate),
                    "rate_period": inv_rate_period,
                    "start_date": inv_start.isoformat(),
                    "contributions": [],
                })
                save_state()
                st.rerun()

    st.write("")

    if not state["investments"]:
        st.markdown('<div class="empty-state">Nenhum investimento cadastrado.</div>', unsafe_allow_html=True)
    else:
        for inv in state["investments"]:
            current_value = investment_current_value(inv)
            principal = investment_principal(inv)
            gain = current_value - principal
            gain_cls = "positive" if gain > 0.005 else "neutral"
            gain_sign = "+" if gain >= 0 else ""

            st.markdown(
                f"""
                <div class="inv-card">
                    <div class="inv-top">
                        <div>
                            <div class="inv-name">{inv['name']}</div>
                            <div class="inv-meta">{inv['location']} • desde {inv['start_date']}</div>
                            <div style="margin-top:0.6rem;"><span class="inv-badge">{rate_label(inv)}</span></div>
                        </div>
                        <div>
                            <div class="inv-value">{format_currency(current_value)}</div>
                            <div class="inv-gain {gain_cls}">{gain_sign}{format_currency(gain)} de rendimento</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            rm_col = st.columns([5, 1])[1]
            with rm_col:
                if st.button("Remover", key=f"rm_i_{inv['id']}"):
                    state["investments"] = [x for x in state["investments"] if x["id"] != inv["id"]]
                    save_state()
                    st.rerun()

    st.write("")
    with st.form("invest_more_form", clear_on_submit=True):
        st.markdown(f"**<span style='color:{TEXT}; font-size:1.1rem;'>Adicionar aporte a um investimento existente</span>**", unsafe_allow_html=True)
        if state["investments"]:
            im1, im2, im3 = st.columns([2, 1, 1])
            with im1:
                inv_choice = st.selectbox(
                    "Investimento",
                    [f'{i["name"]} — {format_currency(investment_current_value(i))}' for i in state["investments"]],
                )
            with im2:
                extra_amount = st.number_input("Valor do aporte", min_value=0.0, step=0.01, format="%.2f", key="extra_amount")
            with im3:
                extra_date = st.date_input("Data do aporte", value=date.today(), key="extra_date")
            extra_submitted = st.form_submit_button("Adicionar aporte 💎")

            if extra_submitted:
                if extra_amount <= 0:
                    st.warning("Informe um valor maior que zero.")
                else:
                    labels = [f'{i["name"]} — {format_currency(investment_current_value(i))}' for i in state["investments"]]
                    idx = labels.index(inv_choice)
                    state["investments"][idx].setdefault("contributions", []).append({
                        "id": str(uuid.uuid4()),
                        "amount": float(extra_amount),
                        "date": extra_date.isoformat(),
                    })
                    save_state()
                    st.rerun()
        else:
            st.caption("Cadastre um investimento primeiro.")
            st.form_submit_button("Adicionar aporte", disabled=True)
