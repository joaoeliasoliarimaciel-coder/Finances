import json
import os
import uuid
from datetime import date, datetime

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
# Persistência
# ----------------------------------------------------------------------------


def default_state():
    return {
        "transactions": [],
        "investments": [],
        "accounts": [dict(a) for a in DEFAULT_ACCOUNTS],
        "period": date.today().strftime("%Y-%m"),
    }


def load_state():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.setdefault("transactions", [])
            data.setdefault("investments", [])
            data.setdefault("accounts", [dict(a) for a in DEFAULT_ACCOUNTS])
            data.setdefault("period", date.today().strftime("%Y-%m"))
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
# CSS - replica o visual do app original (dark fintech)
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
    div[data-testid="stMetricLabel"] {{
        color: {MUTED};
    }}
    div[data-testid="stMetricValue"] {{
        color: {TEXT};
    }}

    .stButton>button, .stFormSubmitButton>button {{
        border: 0;
        border-radius: 12px;
        font-weight: 700;
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
        border: 1px solid rgba(255,255,255,0.15) !important;
        color: {TEXT} !important;
    }}

    input, textarea, select, .stSelectbox div[data-baseweb="select"] > div {{
        background-color: {PANEL_2} !important;
        color: {TEXT} !important;
        border-radius: 10px !important;
    }}

    .transaction-item, .account-item, .investment-item {{
        padding: 0.8rem 1rem;
        border-radius: 14px;
        background: rgba(255,255,255,0.03);
        margin-bottom: 0.6rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
    }}
    .t-meta strong {{ display:block; color: {TEXT}; }}
    .t-meta span {{ color: {MUTED}; font-size: 0.85rem; }}
    .t-amount {{ font-weight: 700; white-space: nowrap; }}
    .t-amount.income {{ color: {ACCENT}; }}
    .t-amount.expense {{ color: {DANGER}; }}
    .acc-balance {{ font-weight: 700; }}
    .acc-balance.negative {{ color: {DANGER}; }}
    .empty-state {{
        padding: 1rem;
        border-radius: 14px;
        background: rgba(255,255,255,0.03);
        color: {MUTED};
        text-align: center;
    }}
    .legend-item {{
        display:flex; justify-content: space-between; color: {MUTED}; margin-bottom: 0.35rem;
    }}
    .legend-badge {{
        width: 12px; height:12px; border-radius: 999px; display:inline-block; margin-right: 0.45rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Cabeçalho
# ----------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <p class="eyebrow">Controle financeiro</p>
        <h1>Finanças Pessoais</h1>
        <p class="subtitle">Organize gastos, ganhos, investimentos, contas e acompanhe seu saldo em tempo real.</p>
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
invested_value = sum(i["amount"] for i in state["investments"])
net_worth = accounts_total + invested_value

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
            st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 0.3rem 0;'>", unsafe_allow_html=True)

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
                    marker_color=[ACCENT, DANGER],
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
            total_exp = sum(totals_by_cat.values())
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
