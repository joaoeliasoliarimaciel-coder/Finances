import csv
import hashlib
import io
import json
import os
import uuid
from datetime import date

import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# Caminhos e constantes
# ----------------------------------------------------------------------------

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
os.makedirs(DATA_DIR, exist_ok=True)

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

COLORS = ["#41c7ae", "#6f7cff", "#ff6987", "#ffbe5c", "#5dc9ff", "#e36dff", "#8df0c8"]

ACCENT = "#41c7ae"
ACCENT_2 = "#6f7cff"
DANGER = "#ff6987"
WARNING = "#ffbe5c"
MUTED = "#93a7c9"
TEXT = "#f3f7ff"
PANEL = "#0f1b2d"
PANEL_2 = "#16263b"
BG = "#07111f"

st.set_page_config(page_title="Finanças Pessoais", page_icon="💰", layout="wide")

# ----------------------------------------------------------------------------
# Autenticação
# ----------------------------------------------------------------------------


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


def hash_password(password: str, salt: str = None):
    if salt is None:
        salt = os.urandom(16).hex()
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 150_000
    ).hex()
    return salt, pwd_hash


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    _, pwd_hash = hash_password(password, salt)
    return pwd_hash == expected_hash


def register_user(username: str, password: str, display_name: str):
    users = load_users()
    key = username.strip().lower()
    if not key or not password:
        return False, "Preencha usuário e senha."
    if key in users:
        return False, "Esse usuário já existe."
    if len(password) < 4:
        return False, "A senha precisa ter pelo menos 4 caracteres."
    salt, pwd_hash = hash_password(password)
    users[key] = {"salt": salt, "hash": pwd_hash, "display_name": display_name.strip() or username}
    save_users(users)
    return True, "Conta criada com sucesso! Faça login."


def authenticate(username: str, password: str):
    users = load_users()
    key = username.strip().lower()
    user = users.get(key)
    if not user:
        return False, None
    if verify_password(password, user["salt"], user["hash"]):
        return True, user.get("display_name", username)
    return False, None


# ----------------------------------------------------------------------------
# Persistência dos dados financeiros (por usuário)
# ----------------------------------------------------------------------------


def default_state():
    return {
        "transactions": [],
        "investments": [],
        "accounts": [dict(a) for a in DEFAULT_ACCOUNTS],
        "period": date.today().strftime("%Y-%m"),
        "budgets": {},          # {categoria: valor_limite_mensal}
        "fixed_bills": [],      # [{id, name, amount, due_day, category, accountId}]
        "paid_bills": {},       # {"YYYY-MM": [bill_id, ...]}
        "goals": [],            # [{id, name, target, current}]
    }


def data_file_for(username):
    return os.path.join(DATA_DIR, f"{username}_finances.json")


def load_state(username):
    path = data_file_for(username)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            base = default_state()
            for k, v in base.items():
                data.setdefault(k, v)
            return data
        except Exception:
            return default_state()
    return default_state()


def save_state():
    path = data_file_for(st.session_state.auth_user)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(st.session_state.state, f, ensure_ascii=False, indent=2)


# ----------------------------------------------------------------------------
# Helpers gerais
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


def find_account(account_id, state):
    return next((a for a in state["accounts"] if a["id"] == account_id), None)


def progress_bar_html(pct, color):
    pct_clamped = max(0, min(pct, 100))
    return f"""
    <div style="background: rgba(255,255,255,0.06); border-radius: 999px; height: 10px; overflow: hidden; margin: 0.35rem 0 0.15rem;">
        <div style="width:{pct_clamped}%; background:{color}; height:100%; border-radius:999px;"></div>
    </div>
    """


# ----------------------------------------------------------------------------
# CSS
# ----------------------------------------------------------------------------

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', Arial, sans-serif;
    }}

    .stApp {{
        background: linear-gradient(135deg, {BG}, #101f34);
        color: {TEXT};
    }}

    .block-container {{
        max-width: 1180px;
        padding-top: 1.5rem;
    }}

    .hero {{
        padding: 1.5rem 1.75rem;
        border-radius: 20px;
        background: radial-gradient(circle at top left, rgba(65, 199, 174, 0.25), transparent 60%), {PANEL};
        border: 1px solid rgba(255,255,255,0.06);
        margin-bottom: 1.5rem;
    }}
    .hero .eyebrow {{
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.25rem;
        color: {ACCENT};
        font-weight: 700;
        font-size: 0.8rem;
    }}
    .hero h1 {{
        margin: 0.2rem 0;
        font-size: 2.2rem;
        color: {TEXT};
    }}
    .hero p.subtitle {{
        color: {MUTED};
        max-width: 650px;
        margin: 0;
    }}

    .panel-title {{
        font-size: 1.15rem;
        font-weight: 700;
        color: {TEXT};
        margin-bottom: 0.75rem;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: rgba(15, 27, 45, 0.92);
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 20px !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.2);
    }}

    div[data-testid="stMetric"] {{
        background: rgba(255,255,255,0.03);
        border-radius: 16px;
        padding: 0.9rem 1rem;
        border: 1px solid rgba(255,255,255,0.06);
    }}
    div[data-testid="stMetricLabel"] {{ color: {MUTED}; }}
    div[data-testid="stMetricValue"] {{ color: {TEXT}; }}

    .stButton>button, .stFormSubmitButton>button {{
        border: 0;
        border-radius: 12px;
        font-weight: 700;
        background: linear-gradient(135deg, {ACCENT}, {ACCENT_2});
        color: white;
        padding: 0.55rem 1.1rem;
    }}
    .stButton>button:hover, .stFormSubmitButton>button:hover {{
        color: white; border: 0; opacity: 0.92;
    }}
    button[kind="secondary"] {{
        background: transparent !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        color: {TEXT} !important;
    }}

    input, textarea, select, .stSelectbox div[data-baseweb="select"] > div {{
        background-color: {PANEL_2} !important;
        color: {TEXT} !important;
        border-radius: 10px !important;
    }}

    .transaction-item, .account-item, .investment-item, .bill-item, .goal-item {{
        padding: 0.8rem 1rem;
        border-radius: 14px;
        background: rgba(255,255,255,0.03);
        margin-bottom: 0.6rem;
    }}
    .t-meta strong {{ display:block; color: {TEXT}; }}
    .t-meta span {{ color: {MUTED}; font-size: 0.85rem; }}
    .t-amount {{ font-weight: 700; white-space: nowrap; }}
    .t-amount.income {{ color: {ACCENT}; }}
    .t-amount.expense {{ color: {DANGER}; }}
    .acc-balance {{ font-weight: 700; }}
    .acc-balance.negative {{ color: {DANGER}; }}
    .empty-state {{
        padding: 1rem; border-radius: 14px; background: rgba(255,255,255,0.03);
        color: {MUTED}; text-align: center;
    }}
    .legend-item {{ display:flex; justify-content: space-between; color: {MUTED}; margin-bottom: 0.35rem; }}
    .legend-badge {{ width: 12px; height:12px; border-radius: 999px; display:inline-block; margin-right: 0.45rem; }}
    .status-pill {{
        display:inline-block; padding: 0.15rem 0.6rem; border-radius: 999px;
        font-size: 0.78rem; font-weight: 700;
    }}
    .status-pago {{ background: rgba(65,199,174,0.15); color: {ACCENT}; }}
    .status-pendente {{ background: rgba(255,190,92,0.15); color: {WARNING}; }}
    .login-card {{
        max-width: 420px; margin: 3rem auto; padding: 2rem; border-radius: 20px;
        background: rgba(15,27,45,0.92); border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 20px 40px rgba(0,0,0,0.25);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Portão de autenticação
# ----------------------------------------------------------------------------

if "auth_user" not in st.session_state:
    st.session_state.auth_user = None
    st.session_state.auth_display_name = None

if not st.session_state.auth_user:
    st.markdown(
        """
        <div class="hero" style="text-align:center; max-width:420px; margin:2rem auto 0;">
            <p class="eyebrow">Controle financeiro</p>
            <h1>Finanças Pessoais</h1>
            <p class="subtitle" style="margin:0 auto;">Entre com sua conta para acessar seus dados financeiros.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_col = st.columns([1, 2, 1])[1]
    with login_col:
        with st.container(border=True):
            tab_login, tab_register = st.tabs(["Entrar", "Criar conta"])

            with tab_login:
                with st.form("login_form"):
                    login_user = st.text_input("Usuário")
                    login_pass = st.text_input("Senha", type="password")
                    login_submit = st.form_submit_button("Entrar", use_container_width=True)
                    if login_submit:
                        ok, display_name = authenticate(login_user, login_pass)
                        if ok:
                            st.session_state.auth_user = login_user.strip().lower()
                            st.session_state.auth_display_name = display_name
                            st.rerun()
                        else:
                            st.error("Usuário ou senha inválidos.")

            with tab_register:
                with st.form("register_form"):
                    reg_name = st.text_input("Como você quer ser chamado(a)")
                    reg_user = st.text_input("Usuário (login)")
                    reg_pass = st.text_input("Senha", type="password")
                    reg_pass_confirm = st.text_input("Confirmar senha", type="password")
                    reg_submit = st.form_submit_button("Criar conta", use_container_width=True)
                    if reg_submit:
                        if reg_pass != reg_pass_confirm:
                            st.error("As senhas não coincidem.")
                        else:
                            ok, msg = register_user(reg_user, reg_pass, reg_name)
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)
    st.stop()

# ----------------------------------------------------------------------------
# Estado carregado por usuário
# ----------------------------------------------------------------------------

if st.session_state.get("state_owner") != st.session_state.auth_user:
    st.session_state.state = load_state(st.session_state.auth_user)
    st.session_state.state_owner = st.session_state.auth_user

state = st.session_state.state

if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = False

with st.sidebar:
    st.markdown(f"**Logado como**  \n{st.session_state.auth_display_name or st.session_state.auth_user}")
    if st.button("Sair", use_container_width=True):
        st.session_state.auth_user = None
        st.session_state.auth_display_name = None
        st.session_state.pop("state", None)
        st.session_state.pop("state_owner", None)
        st.rerun()

# ----------------------------------------------------------------------------
# Cabeçalho
# ----------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <p class="eyebrow">Controle financeiro</p>
        <h1>Finanças Pessoais</h1>
        <p class="subtitle">Organize gastos, ganhos, investimentos, contas, orçamentos e metas em um só lugar.</p>
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
            "Mês", options, index=options.index(state["period"]), format_func=format_month,
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
invested_value = sum(i["amount"] for i in state["investments"])
net_worth = accounts_total + invested_value

paid_ids_this_month = set(state["paid_bills"].get(state["period"], []))
pending_bills_total = sum(
    b["amount"] for b in state["fixed_bills"] if b["id"] not in paid_ids_this_month
)

st.write("")
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Ganhos", format_currency(income))
m2.metric("Gastos", format_currency(expenses))
m3.metric("Saldo do mês", format_currency(balance))
m4.metric("Disponível nas contas", format_currency(accounts_total))
m5.metric("Patrimônio total", format_currency(net_worth))
m6.metric("Contas fixas pendentes", format_currency(pending_bills_total))

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

    fc1, fc2 = st.columns([2, 2])
    with fc1:
        search_term = st.text_input("Buscar por descrição", key="search_term", placeholder="Ex.: mercado")
    with fc2:
        all_cats = sorted({t["category"] for t in current_transactions}) or EXPENSE_CATEGORIES
        cat_filter = st.multiselect("Filtrar por categoria", all_cats, key="cat_filter")

    filtered_transactions = current_transactions
    if search_term.strip():
        filtered_transactions = [
            t for t in filtered_transactions if search_term.strip().lower() in t["description"].lower()
        ]
    if cat_filter:
        filtered_transactions = [t for t in filtered_transactions if t["category"] in cat_filter]

    if not filtered_transactions:
        st.markdown('<div class="empty-state">Nenhuma movimentação encontrada para este período/filtro.</div>', unsafe_allow_html=True)
    else:
        for t in filtered_transactions:
            meta_line = f'{t["category"]} • {t["date"]}'
            if t.get("accountName"):
                meta_line += f' • {t["accountName"]}'
            sign = "+" if t["type"] == "income" else "-"
            cls = "income" if t["type"] == "income" else "expense"

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
                        acc = find_account(t["accountId"], state)
                        if acc:
                            if t["type"] == "expense":
                                acc["balance"] += t["amount"]
                            else:
                                acc["balance"] -= t["amount"]
                    state["transactions"] = [x for x in state["transactions"] if x["id"] != t["id"]]
                    save_state()
                    st.rerun()
            st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 0.3rem 0;'>", unsafe_allow_html=True)

    if current_transactions:
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["Data", "Tipo", "Categoria", "Descrição", "Valor", "Conta", "Mês"])
        for t in current_transactions:
            writer.writerow([
                t["date"],
                "Ganho" if t["type"] == "income" else "Gasto",
                t["category"],
                t["description"],
                f'{t["amount"]:.2f}',
                t.get("accountName") or "",
                t["month"],
            ])
        st.download_button(
            "Exportar movimentações (CSV)",
            data=csv_buffer.getvalue().encode("utf-8-sig"),
            file_name=f"movimentacoes_{state['period']}.csv",
            mime="text/csv",
        )

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
                        "type": "income",
                        "category": "Ajuste",
                        "description": acc_description.strip(),
                        "amount": 0.0 if operation == "Subtrair" else float(acc_amount),
                        "date": date.today().isoformat(),
                        "month": state["period"],
                        "accountId": acc["id"],
                        "accountName": acc["name"],
                    })
                save_state()
                st.rerun()

    with st.expander("Adicionar nova conta"):
        with st.form("new_account_form", clear_on_submit=True):
            new_acc_name = st.text_input("Nome da conta", placeholder="Ex.: Nubank")
            new_acc_balance = st.number_input("Saldo inicial", step=0.01, format="%.2f")
            new_acc_submit = st.form_submit_button("Criar conta")
            if new_acc_submit:
                if not new_acc_name.strip():
                    st.warning("Informe um nome para a conta.")
                else:
                    state["accounts"].append({
                        "id": str(uuid.uuid4()),
                        "name": new_acc_name.strip(),
                        "balance": float(new_acc_balance),
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
                <div class="account-item" style="display:flex; justify-content:space-between; align-items:center;">
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
# Orçamentos por categoria
# ----------------------------------------------------------------------------

with st.container(border=True):
    st.markdown('<div class="panel-title">Orçamentos mensais por categoria</div>', unsafe_allow_html=True)
    st.caption("Defina um limite de gastos mensal para cada categoria e acompanhe o quanto já foi usado.")

    with st.form("budget_form", clear_on_submit=True):
        bc1, bc2 = st.columns([2, 1])
        with bc1:
            budget_cat = st.selectbox("Categoria", EXPENSE_CATEGORIES, key="budget_cat")
        with bc2:
            budget_value = st.number_input("Limite mensal", min_value=0.0, step=0.01, format="%.2f", key="budget_value")
        budget_submit = st.form_submit_button("Definir orçamento")
        if budget_submit:
            if budget_value <= 0:
                state["budgets"].pop(budget_cat, None)
            else:
                state["budgets"][budget_cat] = float(budget_value)
            save_state()
            st.rerun()

    if not state["budgets"]:
        st.markdown('<div class="empty-state">Nenhum orçamento definido ainda.</div>', unsafe_allow_html=True)
    else:
        spent_by_cat = {}
        for t in current_transactions:
            if t["type"] == "expense":
                spent_by_cat[t["category"]] = spent_by_cat.get(t["category"], 0) + t["amount"]

        for cat, limit in state["budgets"].items():
            spent = spent_by_cat.get(cat, 0)
            pct = (spent / limit * 100) if limit > 0 else 0
            color = DANGER if pct >= 100 else (WARNING if pct >= 80 else ACCENT)
            bcol1, bcol2 = st.columns([5, 1])
            with bcol1:
                st.markdown(
                    f"""
                    <div style="margin-bottom: 0.6rem;">
                        <div style="display:flex; justify-content:space-between; color:{MUTED}; font-size:0.9rem;">
                            <span>{cat}</span>
                            <span>{format_currency(spent)} / {format_currency(limit)}</span>
                        </div>
                        {progress_bar_html(pct, color)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with bcol2:
                if st.button("Remover", key=f"rm_budget_{cat}"):
                    state["budgets"].pop(cat, None)
                    save_state()
                    st.rerun()

# ----------------------------------------------------------------------------
# Contas fixas / recorrentes
# ----------------------------------------------------------------------------

with st.container(border=True):
    st.markdown('<div class="panel-title">Contas fixas mensais</div>', unsafe_allow_html=True)
    st.caption("Cadastre contas recorrentes (aluguel, assinaturas, etc.) e marque como pagas a cada mês.")

    with st.form("bill_form", clear_on_submit=True):
        bf1, bf2, bf3, bf4 = st.columns(4)
        with bf1:
            bill_name = st.text_input("Nome", placeholder="Ex.: Aluguel")
        with bf2:
            bill_amount = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f", key="bill_amount")
        with bf3:
            bill_day = st.number_input("Dia do vencimento", min_value=1, max_value=31, step=1, value=5)
        with bf4:
            bill_category = st.selectbox("Categoria", EXPENSE_CATEGORIES, key="bill_category")
        bill_account_names = ["Sem conta"] + [a["name"] for a in state["accounts"]]
        bill_account_choice = st.selectbox("Conta para débito automático", bill_account_names, key="bill_account")
        bill_submit = st.form_submit_button("Adicionar conta fixa")

        if bill_submit:
            if not bill_name.strip() or bill_amount <= 0:
                st.warning("Informe nome e valor da conta fixa.")
            else:
                acc = None
                if bill_account_choice != "Sem conta":
                    acc = next((a for a in state["accounts"] if a["name"] == bill_account_choice), None)
                state["fixed_bills"].append({
                    "id": str(uuid.uuid4()),
                    "name": bill_name.strip(),
                    "amount": float(bill_amount),
                    "due_day": int(bill_day),
                    "category": bill_category,
                    "accountId": acc["id"] if acc else None,
                    "accountName": acc["name"] if acc else None,
                })
                save_state()
                st.rerun()

    if not state["fixed_bills"]:
        st.markdown('<div class="empty-state">Nenhuma conta fixa cadastrada.</div>', unsafe_allow_html=True)
    else:
        paid_list = state["paid_bills"].setdefault(state["period"], [])
        for bill in state["fixed_bills"]:
            is_paid = bill["id"] in paid_list
            pcol1, pcol2, pcol3 = st.columns([4, 1.5, 1.5])
            with pcol1:
                acc_txt = f' • {bill["accountName"]}' if bill.get("accountName") else ""
                st.markdown(
                    f'<div class="t-meta"><strong>{bill["name"]}</strong>'
                    f'<span>Vence dia {bill["due_day"]} • {bill["category"]}{acc_txt} • {format_currency(bill["amount"])}</span></div>',
                    unsafe_allow_html=True,
                )
            with pcol2:
                pill_cls = "status-pago" if is_paid else "status-pendente"
                pill_txt = "Pago" if is_paid else "Pendente"
                st.markdown(f'<span class="status-pill {pill_cls}">{pill_txt}</span>', unsafe_allow_html=True)
            with pcol3:
                bcol_a, bcol_b = st.columns(2)
                with bcol_a:
                    if not is_paid:
                        if st.button("Pagar", key=f"pay_{bill['id']}"):
                            acc = find_account(bill.get("accountId"), state) if bill.get("accountId") else None
                            if acc:
                                acc["balance"] -= bill["amount"]
                            state["transactions"].insert(0, {
                                "id": str(uuid.uuid4()),
                                "type": "expense",
                                "category": bill["category"],
                                "description": bill["name"],
                                "amount": bill["amount"],
                                "date": date.today().isoformat(),
                                "month": state["period"],
                                "accountId": bill.get("accountId"),
                                "accountName": bill.get("accountName"),
                                "billId": bill["id"],
                            })
                            paid_list.append(bill["id"])
                            save_state()
                            st.rerun()
                    else:
                        if st.button("Desfazer", key=f"unpay_{bill['id']}"):
                            linked = next(
                                (t for t in state["transactions"]
                                 if t.get("billId") == bill["id"] and t["month"] == state["period"]),
                                None,
                            )
                            if linked:
                                if linked.get("accountId"):
                                    acc = find_account(linked["accountId"], state)
                                    if acc:
                                        acc["balance"] += linked["amount"]
                                state["transactions"] = [t for t in state["transactions"] if t["id"] != linked["id"]]
                            state["paid_bills"][state["period"]] = [
                                b for b in paid_list if b != bill["id"]
                            ]
                            save_state()
                            st.rerun()
                with bcol_b:
                    if st.button("Excluir", key=f"del_bill_{bill['id']}"):
                        state["fixed_bills"] = [b for b in state["fixed_bills"] if b["id"] != bill["id"]]
                        for month_key in state["paid_bills"]:
                            state["paid_bills"][month_key] = [
                                b for b in state["paid_bills"][month_key] if b != bill["id"]
                            ]
                        save_state()
                        st.rerun()
            st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 0.3rem 0;'>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Metas financeiras
# ----------------------------------------------------------------------------

with st.container(border=True):
    st.markdown('<div class="panel-title">Metas financeiras</div>', unsafe_allow_html=True)
    st.caption("Defina objetivos (viagem, reserva de emergência, etc.) e acompanhe o progresso.")

    with st.form("goal_form", clear_on_submit=True):
        gf1, gf2, gf3 = st.columns(3)
        with gf1:
            goal_name = st.text_input("Nome da meta", placeholder="Ex.: Reserva de emergência")
        with gf2:
            goal_target = st.number_input("Valor alvo", min_value=0.0, step=0.01, format="%.2f", key="goal_target")
        with gf3:
            goal_current = st.number_input("Valor já guardado", min_value=0.0, step=0.01, format="%.2f", key="goal_current")
        goal_submit = st.form_submit_button("Criar meta")
        if goal_submit:
            if not goal_name.strip() or goal_target <= 0:
                st.warning("Informe nome e valor alvo da meta.")
            else:
                state["goals"].append({
                    "id": str(uuid.uuid4()),
                    "name": goal_name.strip(),
                    "target": float(goal_target),
                    "current": float(goal_current),
                })
                save_state()
                st.rerun()

    if not state["goals"]:
        st.markdown('<div class="empty-state">Nenhuma meta cadastrada.</div>', unsafe_allow_html=True)
    else:
        for goal in state["goals"]:
            pct = (goal["current"] / goal["target"] * 100) if goal["target"] > 0 else 0
            color = ACCENT if pct < 100 else ACCENT_2
            gcol1, gcol2, gcol3 = st.columns([4, 1.3, 1])
            with gcol1:
                st.markdown(
                    f"""
                    <div style="margin-bottom:0.3rem;">
                        <div style="display:flex; justify-content:space-between; color:{MUTED}; font-size:0.9rem;">
                            <span><strong style="color:{TEXT};">{goal['name']}</strong></span>
                            <span>{format_currency(goal['current'])} / {format_currency(goal['target'])} ({pct:.0f}%)</span>
                        </div>
                        {progress_bar_html(pct, color)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with gcol2:
                add_val = st.number_input(
                    "Adicionar", min_value=0.0, step=0.01, format="%.2f",
                    key=f"goal_add_{goal['id']}", label_visibility="collapsed",
                )
            with gcol3:
                if st.button("Guardar", key=f"goal_add_btn_{goal['id']}"):
                    if add_val > 0:
                        goal["current"] += float(add_val)
                        save_state()
                        st.rerun()
                if st.button("Excluir", key=f"goal_del_{goal['id']}"):
                    state["goals"] = [g for g in state["goals"] if g["id"] != goal["id"]]
                    save_state()
                    st.rerun()

# ----------------------------------------------------------------------------
# Gráficos
# ----------------------------------------------------------------------------

with st.container(border=True):
    st.markdown('<div class="panel-title">Gráficos</div>', unsafe_allow_html=True)

    g1, g2 = st.columns([1.2, 0.8])

    with g1:
        st.markdown("**Receitas x Despesas (mês atual)**")
        bar_fig = go.Figure(
            data=[
                go.Bar(
                    x=["Ganhos", "Gastos"],
                    y=[income, expenses],
                    marker_color=[ACCENT, DANGER],
                    text=[format_currency(income), format_currency(expenses)],
                    textposition="outside",
                    width=0.5,
                )
            ]
        )
        bar_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT), yaxis=dict(showgrid=False, visible=False),
            xaxis=dict(showgrid=False, color=MUTED),
            margin=dict(l=10, r=10, t=30, b=10), height=280, showlegend=False,
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
                data=[go.Pie(labels=labels, values=values, hole=0.65, marker=dict(colors=COLORS * 3), textinfo="none")]
            )
        donut_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT), margin=dict(l=10, r=10, t=30, b=10), height=280, showlegend=False,
            annotations=[dict(
                text=format_currency(sum(totals_by_cat.values())) if totals_by_cat else "Sem dados",
                x=0.5, y=0.5, font_size=14, showarrow=False, font_color=TEXT,
            )],
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

    st.markdown("**Evolução mensal (Ganhos, Gastos e Saldo)**")
    months_present = sorted({t["month"] for t in state["transactions"]})
    if len(months_present) < 2 and state["period"] not in months_present:
        months_present.append(state["period"])
        months_present.sort()

    if not months_present:
        st.markdown('<div class="empty-state">Sem histórico suficiente ainda.</div>', unsafe_allow_html=True)
    else:
        monthly_income, monthly_expense, monthly_balance = [], [], []
        for month_key in months_present:
            inc = sum(t["amount"] for t in state["transactions"] if t["month"] == month_key and t["type"] == "income")
            exp = sum(t["amount"] for t in state["transactions"] if t["month"] == month_key and t["type"] == "expense")
            monthly_income.append(inc)
            monthly_expense.append(exp)
            monthly_balance.append(inc - exp)

        evo_fig = go.Figure()
        evo_fig.add_trace(go.Scatter(x=months_present, y=monthly_income, mode="lines+markers", name="Ganhos", line=dict(color=ACCENT)))
        evo_fig.add_trace(go.Scatter(x=months_present, y=monthly_expense, mode="lines+markers", name="Gastos", line=dict(color=DANGER)))
        evo_fig.add_trace(go.Scatter(x=months_present, y=monthly_balance, mode="lines+markers", name="Saldo", line=dict(color=ACCENT_2, dash="dot")))
        evo_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT),
            xaxis=dict(showgrid=False, color=MUTED, tickvals=months_present, ticktext=[format_month(m) for m in months_present]),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", color=MUTED),
            margin=dict(l=10, r=10, t=30, b=10), height=320,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(evo_fig, use_container_width=True)

# ----------------------------------------------------------------------------
# Investimentos
# ----------------------------------------------------------------------------

with st.container(border=True):
    st.markdown('<div class="panel-title">Investimentos</div>', unsafe_allow_html=True)

    with st.form("investment_form", clear_on_submit=True):
        ic1, ic2, ic3 = st.columns(3)
        with ic1:
            inv_name = st.text_input("Nome do investimento", placeholder="Ex.: Poupança")
        with ic2:
            inv_amount = st.number_input("Valor aplicado", min_value=0.0, step=0.01, format="%.2f", key="inv_amount")
        with ic3:
            inv_location = st.text_input("Onde está aplicado", placeholder="Ex.: Banco, Tesouro, CDB")

        inv_submitted = st.form_submit_button("Salvar investimento")

        if inv_submitted:
            if not inv_name.strip():
                st.warning("Informe um nome para o investimento.")
            else:
                state["investments"].append({
                    "id": str(uuid.uuid4()),
                    "name": inv_name.strip(),
                    "amount": float(inv_amount),
                    "location": inv_location.strip() or "Sem local informado",
                })
                save_state()
                st.rerun()

    if not state["investments"]:
        st.markdown('<div class="empty-state">Nenhum investimento cadastrado.</div>', unsafe_allow_html=True)
    else:
        for inv in state["investments"]:
            rc1, rc2, rc3 = st.columns([4, 2, 1])
            with rc1:
                st.markdown(
                    f'<div class="t-meta"><strong>{inv["name"]}</strong><span>{inv["location"]}</span></div>',
                    unsafe_allow_html=True,
                )
            with rc2:
                st.markdown(f'<div class="t-amount">{format_currency(inv["amount"])}</div>', unsafe_allow_html=True)
            with rc3:
                if st.button("Remover", key=f"rm_i_{inv['id']}"):
                    state["investments"] = [x for x in state["investments"] if x["id"] != inv["id"]]
                    save_state()
                    st.rerun()

    st.write("")
    with st.form("invest_more_form", clear_on_submit=True):
        st.markdown("**Adicionar valor a um investimento existente**")
        if state["investments"]:
            im1, im2 = st.columns([2, 1])
            with im1:
                inv_choice = st.selectbox(
                    "Investimento",
                    [f'{i["name"]} — {format_currency(i["amount"])}' for i in state["investments"]],
                )
            with im2:
                extra_amount = st.number_input("Valor extra", min_value=0.0, step=0.01, format="%.2f", key="extra_amount")
            extra_submitted = st.form_submit_button("Adicionar valor")

            if extra_submitted:
                if extra_amount <= 0:
                    st.warning("Informe um valor maior que zero.")
                else:
                    idx = [f'{i["name"]} — {format_currency(i["amount"])}' for i in state["investments"]].index(inv_choice)
                    state["investments"][idx]["amount"] += float(extra_amount)
                    save_state()
                    st.rerun()
        else:
            st.caption("Cadastre um investimento primeiro.")
            st.form_submit_button("Adicionar valor", disabled=True)
