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

# Paleta "girly" vibrante: pink, lilás e coral, com bom contraste de leitura
COLORS = ["#ff6fa5", "#a06cff", "#ff9ecf", "#5ec8d8", "#ffb347", "#c084fc", "#ff8bab"]

ACCENT = "#ff4d94"        # pink vibrante (principal)
ACCENT_2 = "#a259ff"      # lilás vibrante
DANGER = "#e5484d"        # vermelho coral (bem legível)
WARNING = "#d97b06"       # âmbar escuro (legível em fundo claro)
SUCCESS = "#1f9d63"       # verde esmeralda (bem legível)
MUTED = "#6b5b73"         # cinza-arroxeado escuro o bastante para ler
TEXT = "#2c1b30"          # quase preto arroxeado — alto contraste
PANEL = "#ffffff"
PANEL_2 = "#fdf1f8"
BG_1 = "#fff5fb"
BG_2 = "#f6ecff"

st.set_page_config(page_title="Nossas Finanças", page_icon="💗", layout="wide")

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
    # Login padrão de fábrica — troque em "Settings > Secrets" no Streamlit Cloud:
    # [credentials]
    # casal = "sua_senha_aqui"
    return {"casal": "financas2026"}


CREDENTIALS
