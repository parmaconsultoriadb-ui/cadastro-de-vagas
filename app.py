import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

# ==============================
# Configuração inicial da página
# ==============================
st.set_page_config(page_title="Parma Consultoria", layout="wide")

# ==============================
# Arquivos CSV
# ==============================
CLIENTES_CSV = "clientes.csv"
VAGAS_CSV = "vagas.csv"
CANDIDATOS_CSV = "candidatos.csv"
LOGS_CSV = "logs.csv"

# ==============================
# Colunas esperadas
# ==============================
CLIENTES_COLS = ["ID", "Data", "Cliente", "Nome", "Cidade", "UF", "Telefone", "E-mail"]
VAGAS_COLS = [
    "ID",
    "Cliente",
    "Status",
    "Data de Abertura",
    "Cargo",
    "Recrutador",
    "Atualização",
    "Salário 1",
    "Salário 2",
    "Descrição / Observação",
]
CANDIDATOS_COLS = ["ID", "Cliente", "Cargo", "Nome", "Telefone", "Recrutador", "Status", "Data de Início"]
LOGS_COLS = ["DataHora", "Usuario", "Aba", "Acao", "ItemID", "Campo", "ValorAnterior", "ValorNovo", "Detalhe"]

# ==============================
# Usuários e permissões
# ==============================
USUARIOS = {
    "admin": {"senha": "Parma!123@", "permissoes": ["menu", "clientes", "vagas", "candidatos", "logs"]},
    "andre": {"senha": "And!123@", "permissoes": ["menu", "clientes", "vagas", "candidatos", "logs"]},
    "lorrayne": {"senha": "Lrn!123@", "permissoes": ["menu", "vagas", "candidatos"]},
}

def load_csv(path, expected_cols):
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, dtype=str)
            df = df.fillna("")
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            df = df[expected_cols]
            if "ID" in df.columns:
                df["ID"] = df["ID"].astype(str)
            return df
        except Exception:
            return pd.DataFrame(columns=expected_cols)
    else:
        return pd.DataFrame(columns=expected_cols)

def save_csv(df, path):
    df.to_csv(path, index=False, encoding="utf-8")

def next_id(df, id_col="ID"):
    if df is None or df.empty:
        return 1
    try:
        vals = pd.to_numeric(df[id_col], errors="coerce").fillna(0).astype(int)
        return int(vals.max()) + 1
    except Exception:
        return 1

def ensure_logs_file():
    if not os.path.exists(LOGS_CSV):
        save_csv(pd.DataFrame(columns=LOGS_COLS), LOGS_CSV)

def registrar_log(aba, acao, item_id="", campo="", valor_anterior="", valor_novo="", detalhe=""):
    ensure_logs_file()
    datahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    usuario = st.session_state.get("usuario", "admin")
    log_df = pd.DataFrame([{
        "DataHora": datahora,
        "Usuario": usuario,
        "Aba": aba,
        "Acao": acao,
        "ItemID": str(item_id) if item_id is not None else "",
        "Campo": campo,
        "ValorAnterior": "" if valor_anterior is None else str(valor_anterior),
        "ValorNovo": "" if valor_novo is None else str(valor_novo),
        "Detalhe": detalhe
    }])
    if os.path.exists(LOGS_CSV):
        atual = pd.read_csv(LOGS_CSV, dtype=str).fillna("")
        log_df = pd.concat([atual, log_df], ignore_index=True)
    save_csv(log_df, LOGS_CSV)

def carregar_logs():
    ensure_logs_file()
    try:
        df = pd.read_csv(LOGS_CSV, dtype=str)
        return df.fillna("")
    except Exception:
        return pd.DataFrame(columns=LOGS_COLS)

for key, default in [
    ("page", "login"),
    ("logged_in", False),
    ("usuario", ""),
    ("permissoes", []),
    ("edit_mode", None),
    ("edit_record", {}),
    ("confirm_delete", {"df_name": None, "row_id": None}),
]:
    if key not in st.session_state:
        st.session_state[key] = default

for df_key, csv_path, cols in [
    ("clientes_df", CLIENTES_CSV, CLIENTES_COLS),
    ("vagas_df", VAGAS_CSV, VAGAS_COLS),
    ("candidatos_df", CANDIDATOS_CSV, CANDIDATOS_COLS),
]:
    if df_key not in st.session_state:
        st.session_state[df_key] = load_csv(csv_path, cols)

st.markdown(
    """
    <style>
    :root {
        --parma-blue-dark: #004488;
        --parma-blue-medium: #0066AA;
        --parma-blue-light: #E0F2F7;
        --parma-text-dark: #333333;
    }
    div.stButton > button {
        background-color: var(--parma-blue-dark) !important;
        color: white !important;
        border-radius: 8px;
        height: 2.5em;
        font-size: 14px;
        font-weight: bold;
        border: none;
    }
    div.stButton > button:hover {
        background-color: var(--parma-blue-medium) !important;
    }
    .parma-header {
        background-color: var(--parma-blue-light);
        padding:6px;
        font-weight:bold;
        color:var(--parma-text-dark);
        border-radius:4px;
        text-align:center;
        font-size:13px;
        border-bottom: 1px solid #cfcfcf;
    }
    .parma-cell {
        padding:6px;
        text-align:center;
        color:var(--parma-text-dark);
        font-size:13px;
        background-color: white;
        border: none;
    }
    .stDataFrame div[data-testid="stStyledTable"] table {
        font-size: 13px !important;
        border-collapse: collapse !important;
    }
    .stDataFrame div[data-testid="stStyledTable"] thead th {
        font-size: 13px !important;
        background-color: #f6f9fb !important;
        padding: 6px !important;
        border-bottom: 1px solid #cfcfcf !important;
        border-left: none !important;
        border-right: none !important;
    }
    .stDataFrame div[data-testid="stStyledTable"] td {
        padding: 6px !important;
        border: none !important;
    }
    hr.parma-hr {
        border: none;
        border-bottom: 1px solid #e0e0e0;
        margin: 0;
    }
    .streamlit-expanderHeader, .stMarkdown, .stText {
        font-size:13px !important;
    }
    /* Botão Editar e Excluir em tabelas: metade do tamanho */
    .parma-btn-small > button {
        height: 1.25em !important;
        font-size: 11px !important;
        padding: 2px 6px !important;
        min-width: 0 !important;
        width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def download_button(df, filename, label="⬇️ Baixar CSV"):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv, file_name=filename, mime="text/csv", use_container_width=True)

def show_table(df, cols, df_name, csv_path):
    if df is None or df.empty:
        st.info("Nenhum registro para exibir.")
        return

    header_cols = st.columns(len(cols) + 2)
    for i, c in enumerate(cols):
        header_cols[i].markdown(f"<div class='parma-header'>{c}</div>", unsafe_allow_html=True)
    header_cols[-2].markdown("<div class='parma-header'>Editar</div>", unsafe_allow_html=True)
    header_cols[-1].markdown("<div class='parma-header'>Excluir</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    for _, row in df.iterrows():
        row_cols = st.columns(len(cols) + 2)
        for i, c in enumerate(cols):
            value = row.get(c, "")
            if pd.isna(value):
                value = ""
            row_cols[i].markdown(f"<div class='parma-cell'>{value}</div>", unsafe_allow_html=True)
        # Editar (metade do tamanho)
        with row_cols[-2]:
            st.markdown('<div class="parma-btn-small">', unsafe_allow_html=True)
            if st.button("✏️", key=f"edit_{df_name}_{str(row.get('ID',''))}", use_container_width=True):
                st.session_state.edit_mode = df_name
                st.session_state.edit_record = row.to_dict()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        # Excluir (metade do tamanho)
        with row_cols[-1]:
            st.markdown('<div class="parma-btn-small">', unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_{df_name}_{str(row.get('ID',''))}", use_container_width=True):
                st.session_state.confirm_delete = {"df_name": df_name, "row_id": row["ID"]}
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<hr class='parma-hr' />", unsafe_allow_html=True)

    if st.session_state.confirm_delete["df_name"] == df_name:
        row_id = st.session_state.confirm_delete["row_id"]
        st.error(f"⚠️ Deseja realmente excluir o registro **ID {row_id}**? Esta ação é irreversível.")
        col_sp1, col_yes, col_no, col_sp2 = st.columns([2, 1, 1, 2])
        with col_yes:
            if st.button("✅ Sim, excluir", key=f"confirm_{df_name}_{row_id}", use_container_width=True):
                # ... [código igual para exclusão] ...
                pass  # O restante do código permanece igual!
        with col_no:
            if st.button("❌ Cancelar", key=f"cancel_{df_name}_{row_id}", use_container_width=True):
                st.session_state.confirm_delete = {"df_name": None, "row_id": None}
                st.rerun()
    st.divider()

# ... [todas as demais funções do app permanecem iguais, sem mudança]

if st.session_state.logged_in:
    st.image("https://parmaconsultoria.com.br/wp-content/uploads/2023/10/logo-parma-1.png", width=180)
    st.caption(f"Usuário: {st.session_state.usuario}")
    page_label_map = {
        "menu": "Menu Principal",
        "clientes": "Clientes",
        "vagas": "Vagas",
        "candidatos": "Candidatos",
        "logs": "Logs do Sistema"
    }
    perms = st.session_state.get("permissoes", [])
    if "menu" not in perms:
        perms = ["menu"] + perms
    ordered_page_keys = ["menu", "clientes", "vagas", "candidatos", "logs"]
    allowed_pages = [p for p in ordered_page_keys if p in perms]
    labels = [page_label_map[p] for p in allowed_pages]
    try:
        index_initial = allowed_pages.index(st.session_state.page)
    except Exception:
        index_initial = 0

    # Todos os botões da barra superior têm o mesmo tamanho
    total_buttons = len(labels) + 2
    menu_cols = st.columns([1] * total_buttons)
    for i, label in enumerate(labels):
        if menu_cols[i].button(label, use_container_width=True):
            st.session_state.page = allowed_pages[i]
            st.rerun()
    if menu_cols[-2].button("🔄 Refresh", use_container_width=True):
        refresh_data()
        st.rerun()
    if menu_cols[-1].button("Sair", use_container_width=True):
        registrar_log("Login", "Logout", detalhe=f"Usuário {st.session_state.usuario} saiu do sistema.")
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()
    current_page = st.session_state.page
    if current_page == "menu":
        tela_menu_interno()
    elif current_page == "clientes":
        if "clientes" in perms:
            tela_clientes()
        else:
            st.warning("⚠️ Você não tem permissão para acessar esta página.")
    elif current_page == "vagas":
        if "vagas" in perms:
            tela_vagas()
        else:
            st.warning("⚠️ Você não tem permissão para acessar esta página.")
    elif current_page == "candidatos":
        if "candidatos" in perms:
            tela_candidatos()
        else:
            st.warning("⚠️ Você não tem permissão para acessar esta página.")
    elif current_page == "logs":
        if "logs" in perms:
            tela_logs()
        else:
            st.warning("⚠️ Você não tem permissão para acessar esta página.")
else:
    tela_login()
