import json
import os
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

# Paleta clara e elegante (rosé/ameixa) em vez do tema escuro anterior
COLORS = ["#c08497", "#7c6a8e", "#e8b86d", "#8aa694", "#b0879a", "#6f8faa", "#d2a679"]

ACCENT = "#b76e79"        # rosé principal
ACCENT_2 = "#7c6a8e"      # ameixa
DANGER = "#c0564a"        # terracota suave
WARNING = "#e0a458"       # dourado suave
SUCCESS = "#6f9c76"       # verde salva
MUTED = "#8a7d87"
TEXT = "#3d2c3a"
PANEL = "#ffffff"
PANEL_2 = "#faf1ec"
BG_1 = "#fdf6f2"
BG_2 = "#f6e9ec"

st.set_page_config(page_title="Nossas Finanças", page_icon="💗", layout="wide")

# ----------------------------------------------------------------------------
# Login
# ----------------------------------------------------------------------------

try:
    CREDENTIALS = dict(st.secrets["credentials"])
except Exception:
    # Login padrão de fábrica — troque isso em "Settings > Secrets" no Streamlit
    # Cloud adicionando:
    # [credentials]
    # casal = "sua_senha_aqui"
    CREDENTIALS = {"casal": "financas2026"}


def login_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Poppins:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
        .stApp {{
            background: radial-gradient(circle at 15% 10%, {BG_2}, transparent 55%),
                        radial-gradient(circle at 85% 90%, #eee0dd, transparent 55%),
                        {BG_1};
        }}
        .login-wrap {{
            max-width: 420px;
            margin: 6vh auto 0 auto;
            padding: 2.4rem 2.2rem 2rem 2.2rem;
            background: {PANEL};
            border-radius: 26px;
            box-shadow: 0 25px 60px rgba(120, 80, 90, 0.18);
            border: 1px solid rgba(183, 110, 121, 0.15);
            text-align: center;
        }}
        .login-wrap .icon {{ font-size: 2.4rem; margin-bottom: 0.2rem; }}
        .login-wrap h1 {{
            font-family: 'Playfair Display', serif;
            color: {TEXT};
            font-size: 1.9rem;
            margin: 0.2rem 0 0.1rem 0;
        }}
        .login-wrap p {{ color: {MUTED}; margin-bottom: 1.2rem; font-size: 0.92rem; }}
        div[data-testid="stForm"] {{
            border: none !important;
            background: transparent !important;
            padding: 0 !important;
        }}
        input {{
            background-color: {PANEL_2} !important;
            color: {TEXT} !important;
            border-radius: 12px !important;
            border: 1px solid rgba(183,110,121,0.25) !important;
        }}
        .stButton>button, .stFormSubmitButton>button {{
            border: 0;
            border-radius: 12px;
            font-weight: 600;
            background: linear-gradient(135deg, {ACCENT}, {ACCENT_2});
            color: white;
            width: 100%;
            padding: 0.6rem 1.1rem;
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
            <div class="icon">💗</div>
            <h1>Nossas Finanças</h1>
            <p>Entre com seu usuário e senha para acessar</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([1, 1.05, 1])
    with mid:
        with st.container():
            st.markdown('<div style="max-width:420px; margin: -1.4rem auto 0 auto;">', unsafe_allow_html=True)
            with st.form("login_form"):
                user = st.text_input("Usuário")
                pwd = st.text_input("Senha", type="password")
                submitted = st.form_submit_button("Entrar")
            st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        if user in CREDENTIALS and pwd == CREDENTIALS[user]:
            st.session_state.authenticated = True
            st.session_state.username = user
            st.rerun()
        else:
            _, mid2, _ = st.columns([1, 1.05, 1])
            with mid2:
                st.error("Usuário ou senha incorretos.")


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
    """Garante que investimentos antigos (sem taxa/juros) ganhem os novos campos."""
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
# Cálculo de juros dos investimentos (juros compostos, atualiza sozinho)
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
    """Total efetivamente aportado (sem os juros)."""
    total = inv.get("initial_amount", 0.0)
    total += sum(c["amount"] for c in inv.get("contributions", []))
    return total


def investment_current_value(inv, as_of: date = None) -> float:
    """Valor atual do investimento já com os juros aplicados desde cada aporte."""
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
# CSS - visual claro e elegante
# ----------------------------------------------------------------------------

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Poppins:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Poppins', sans-serif;
    }}

    .stApp {{
        background: radial-gradient(circle at 10% 0%, {BG_2}, transparent 50%),
                    radial-gradient(circle at 90% 100%, #eee0dd, transparent 50%),
                    {BG_1};
        color: {TEXT};
    }}

    .block-container {{
        max-width: 1180px;
        padding-top: 1.5rem;
    }}

    .hero {{
        padding: 2rem 2.2rem;
        border-radius: 26px;
        background: linear-gradient(120deg, rgba(183, 110, 121, 0.12), rgba(124, 106, 142, 0.08)), {PANEL};
        border: 1px solid rgba(183, 110, 121, 0.18);
        margin-bottom: 1.5rem;
        box-shadow: 0 18px 45px rgba(150, 100, 110, 0.12);
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
        font-weight: 600;
        font-size: 0.78rem;
    }}
    .hero h1 {{
        font-family: 'Playfair Display', serif;
        margin: 0.15rem 0;
        font-size: 2.3rem;
        color: {TEXT};
    }}
    .hero p.subtitle {{
        color: {MUTED};
        max-width: 620px;
        margin: 0;
    }}
    .hero .hero-icon {{
        font-size: 2.8rem;
    }}

    .panel-title {{
        font-family: 'Playfair Display', serif;
        font-size: 1.2rem;
        font-weight: 700;
        color: {TEXT};
        margin-bottom: 0.75rem;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: {PANEL};
        border: 1px solid rgba(183, 110, 121, 0.14) !important;
        border-radius: 22px !important;
        box-shadow: 0 16px 36px rgba(150, 100, 110, 0.08);
    }}

    div[data-testid="stMetric"] {{
        background: {PANEL_2};
        border-radius: 16px;
        padding: 0.9rem 1rem;
        border: 1px solid rgba(183, 110, 121, 0.14);
    }}
    div[data-testid="stMetricLabel"] {{
        color: {MUTED};
    }}
    div[data-testid="stMetricValue"] {{
        color: {TEXT};
    }}

    .stButton>button, .stFormSubmitButton>button {{
        border: 0;
        border-radius: 12px;
        font-weight: 600;
        background: linear-gradient(135deg, {ACCENT}, {ACCENT_2});
        color: white;
        padding: 0.55rem 1.1rem;
    }}
    .stButton>button:hover, .stFormSubmitButton>button:hover {{
        color: white;
        border: 0;
        opacity: 0.92;
    }}

    button[kind="secondary"] {{
        background: transparent !important;
        border: 1px solid rgba(183,110,121,0.35) !important;
        color: {TEXT} !important;
    }}

    input, textarea, select, .stSelectbox div[data-baseweb="select"] > div {{
        background-color: {PANEL_2} !important;
        color: {TEXT} !important;
        border-radius: 10px !important;
    }}

    .transaction-item, .account-item, .investment-item {{
        padding: 0.9rem 1.1rem;
        border-radius: 16px;
        background: {PANEL_2};
        margin-bottom: 0.6rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        border: 1px solid rgba(183,110,121,0.10);
    }}
    .t-meta strong {{ display:block; color: {TEXT}; }}
    .t-meta span {{ color: {MUTED}; font-size: 0.85rem; }}
    .t-amount {{ font-weight: 700; white-space: nowrap; }}
    .t-amount.income {{ color: {SUCCESS}; }}
    .t-amount.expense {{ color: {DANGER}; }}
    .acc-balance {{ font-weight: 700; color: {SUCCESS}; }}
    .acc-balance.negative {{ color: {DANGER}; }}
    .empty-state {{
        padding: 1rem;
        border-radius: 14px;
        background: {PANEL_2};
        color: {MUTED};
        text-align: center;
    }}
    .legend-item {{
        display:flex; justify-content: space-between; color: {MUTED}; margin-bottom: 0.35rem;
    }}
    .legend-badge {{
        width: 12px; height:12px; border-radius: 999px; display:inline-block; margin-right: 0.45rem;
    }}

    .inv-card {{
        padding: 1rem 1.2rem;
        border-radius: 18px;
        background: {PANEL_2};
        border: 1px solid rgba(183,110,121,0.12);
        margin-bottom: 0.8rem;
    }}
    .inv-card .inv-top {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
    }}
    .inv-card .inv-name {{ font-weight: 700; color: {TEXT}; font-size: 1.02rem; }}
    .inv-card .inv-meta {{ color: {MUTED}; font-size: 0.82rem; margin-top: 0.15rem; }}
    .inv-badge {{
        display:inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        background: rgba(183,110,121,0.14);
        color: {ACCENT};
        font-size: 0.75rem;
        font-weight: 600;
        white-space: nowrap;
    }}
    .inv-value {{ font-size: 1.25rem; font-weight: 700; color: {TEXT}; text-align: right; }}
    .inv-gain {{ font-size: 0.85rem; text-align: right; }}
    .inv-gain.positive {{ color: {SUCCESS}; }}
    .inv-gain.neutral {{ color: {MUTED}; }}

    section[data-testid="stSidebar"] {{
        background: {PANEL};
        border-right: 1px solid rgba(183,110,121,0.12);
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
        <div style="text-align:center; padding: 0.5rem 0 1rem 0;">
            <div style="font-size:2rem;">💗</div>
            <div style="font-family:'Playfair Display', serif; font-size:1.2rem; color:{TEXT};">Nossas Finanças</div>
            <div style="color:{MUTED}; font-size:0.85rem;">Olá, {st.session_state.get('username', '')}!</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Sair", use_container_width=True, type="secondary"):
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
            <p class="subtitle">Organize gastos, ganhos, investimentos, contas e acompanhe o patrimônio de vocês em tempo real.</p>
        </div>
        <div class="hero-icon">🌷</div>
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
        st.markdown('<div class="panel-title">Nova movimentação</div>', unsafe_allow_html=True)
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

        submitted = st.form_submit_button("Adicionar")

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
m4.metric("Disponível nas contas", format_currency(accounts_total))
m5.metric("Patrimônio total", format_currency(net_worth))

st.write("")

# ----------------------------------------------------------------------------
# Movimentações
# ----------------------------------------------------------------------------

with st.container(border=True):
    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown('<div class="panel-title">Movimentações</div>', unsafe_allow_html=True)
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
        st.markdown('<div class="empty-state">Nenhuma movimentação para este período ainda.</div>', unsafe_allow_html=True)
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
            st.markdown("<hr style='border-color: rgba(183,110,121,0.12); margin: 0.3rem 0;'>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Contas
# ----------------------------------------------------------------------------

with st.container(border=True):
    st.markdown('<div class="panel-title">Contas</div>', unsafe_allow_html=True)

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

        acc_submitted = st.form_submit_button("Atualizar conta")

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
                        <div style="color:{MUTED}; font-size:0.85rem;">{'Saldo negativo' if neg else 'Saldo disponível'}</div>
                    </div>
                    <div class="acc-balance {'negative' if neg else ''}">{format_currency(a['balance'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ----------------------------------------------------------------------------
# Gráficos
# ----------------------------------------------------------------------------

with st.container(border=True):
    st.markdown('<div class="panel-title">Gráficos</div>', unsafe_allow_html=True)

    g1, g2 = st.columns([1.2, 0.8])

    with g1:
        st.markdown("**Receitas x Despesas**")
        bar_fig = go.Figure(
            data=[
                go.Bar(
                    x=["Ganhos", "Gastos"],
                    y=[income, expenses],
                    marker_color=[SUCCESS, DANGER],
                    text=[format_currency(income), format_currency(expenses)],
                    textposition="outside",
                    width=0.5,
                )
            ]
        )
        bar_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT),
            yaxis=dict(showgrid=False, visible=False),
            xaxis=dict(showgrid=False, color=MUTED),
            margin=dict(l=10, r=10, t=30, b=10),
            height=280,
            showlegend=False,
        )
        st.plotly_chart(bar_fig, use_container_width=True)

    with g2:
        st.markdown("**Despesas por categoria**")
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
                        marker=dict(colors=COLORS * 3),
                        textinfo="none",
                    )
                ]
            )
        donut_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT),
            margin=dict(l=10, r=10, t=30, b=10),
            height=280,
            showlegend=False,
            annotations=[dict(text=format_currency(sum(totals_by_cat.values())) if totals_by_cat else "Sem dados",
                               x=0.5, y=0.5, font_size=14, showarrow=False, font_color=TEXT)],
        )
        st.plotly_chart(donut_fig, use_container_width=True)

        if totals_by_cat:
            for idx, (name, value) in enumerate(totals_by_cat.items()):
                color = COLORS[idx % len(COLORS)]
                st.markdown(
                    f"""
                    <div class="legend-item">
                        <span><span class="legend-badge" style="background:{color}"></span>{name}</span>
                        <strong>{format_currency(value)}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ----------------------------------------------------------------------------
# Investimentos
# ----------------------------------------------------------------------------

with st.container(border=True):
    st.markdown('<div class="panel-title">Investimentos</div>', unsafe_allow_html=True)
    st.caption("O valor de cada investimento é recalculado automaticamente com base na taxa de juros e no tempo desde o aporte.")

    iv1, iv2, iv3 = st.columns(3)
    iv1.metric("Total aportado", format_currency(invested_principal_total))
    iv2.metric("Valor atual (com juros)", format_currency(invested_current_total))
    iv3.metric("Rendimento acumulado", format_currency(investment_gain_total))

    st.write("")

    with st.form("investment_form", clear_on_submit=True):
        st.markdown("**Novo investimento**")
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

        inv_submitted = st.form_submit_button("Salvar investimento")

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
                            <div style="margin-top:0.4rem;"><span class="inv-badge">{rate_label(inv)}</span></div>
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
        st.markdown("**Adicionar aporte a um investimento existente**")
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
            extra_submitted = st.form_submit_button("Adicionar aporte")

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
