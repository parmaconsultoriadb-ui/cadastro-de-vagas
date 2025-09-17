import streamlit as st
from streamlit_autorefresh import st_autorefresh
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
COMERCIAL_CSV = "comercial.csv"  # NOVO

# ==============================
# Colunas esperadas
# ==============================
CLIENTES_COLS = ["ID", "Data", "Cliente", "Nome", "Cidade", "UF", "Telefone", "E-mail"]
VAGAS_COLS = ["ID", "Cliente", "Status", "Data de Abertura", "Cargo", "Recrutador", "Atualização", "Salário 1", "Salário 2"]
CANDIDATOS_COLS = ["ID", "Cliente", "Cargo", "Nome", "Telefone", "Recrutador", "Status", "Data de Início"]
LOGS_COLS = ["DataHora", "Usuario", "Aba", "Acao", "ItemID", "Campo", "ValorAnterior", "ValorNovo", "Detalhe"]
COMERCIAL_COLS = ["ID", "Data", "Empresa", "Cidade", "UF", "Nome", "Contato", "E-mail", "Canal", "Status"]  # NOVO

# ==============================
# Usuários e permissões
# ==============================
USUARIOS = {
    "admin": {"senha": "Parma!123@", "permissoes": ["menu", "clientes", "vagas", "candidatos", "logs"]},
    "andre": {"senha": "And!123@", "permissoes": ["clientes", "vagas", "candidatos"]},
    "lorrayne": {"senha": "Lrn!123@", "permissoes": ["vagas", "candidatos"]},
    "nikole": {"senha": "Nkl!123@", "permissoes": ["vagas", "candidatos"]},
    "julia": {"senha": "Jla!123@", "permissoes": ["vagas", "candidatos"]},
    "ricardo": {"senha": "Rcd!123@", "permissoes": ["clientes", "vagas", "candidatos"]},
}

RECRUTADORES_PADRAO = ["Lorrayne", "Kaline", "Nikole", "Leila", "Julia"]

# ==============================
# Funções auxiliares
# ==============================
def load_csv(path, expected_cols):
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, dtype=str).fillna("")
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
# ==============================
# Inicialização do session_state
# ==============================
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
    ("comercial_df", COMERCIAL_CSV, COMERCIAL_COLS),  # INCLUI COMERCIAL
]:
    if df_key not in st.session_state:
        st.session_state[df_key] = load_csv(csv_path, cols)

# ==============================
# CSS customizado
# ==============================
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
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================
# Botão de download reutilizável
# ==============================
def download_button(df, filename, label="⬇️ Baixar CSV"):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv, file_name=filename, mime="text/csv", use_container_width=True)
# ==============================
# Página: 📞 Comercial
# ==============================
def tela_comercial():
    if st.session_state.edit_mode == "comercial_df":
        show_edit_form("comercial_df", COMERCIAL_COLS, COMERCIAL_CSV)
        return

    st.header("📞 Comercial")
    st.markdown("Gerencie oportunidades comerciais com empresas em potencial.")

    with st.expander("➕ Cadastrar Empresa Comercial", expanded=False):
        data_hoje = date.today().strftime("%d/%m/%Y")
        with st.form("form_comercial", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                empresa = st.text_input("Empresa *")
                cidade = st.text_input("Cidade *")
                contato = st.text_input("Contato *")
                canal = st.text_input("Canal")
            with col2:
                nome = st.text_input("Nome *")
                uf = st.text_input("UF *", max_chars=2)
                email = st.text_input("E-mail *")
            submitted = st.form_submit_button("✅ Salvar Empresa", use_container_width=True)
            if submitted:
                if not all([empresa, cidade, uf, nome, contato, email]):
                    st.warning("⚠️ Preencha todos os campos obrigatórios.")
                else:
                    prox_id = str(next_id(st.session_state.comercial_df, "ID"))
                    novo = pd.DataFrame([{
                        "ID": prox_id,
                        "Data": data_hoje,
                        "Empresa": empresa,
                        "Cidade": cidade,
                        "UF": uf.upper(),
                        "Nome": nome,
                        "Contato": contato,
                        "E-mail": email,
                        "Canal": canal,
                        "Status": "Prospect"
                    }])
                    st.session_state.comercial_df = pd.concat([st.session_state.comercial_df, novo], ignore_index=True)
                    save_csv(st.session_state.comercial_df, COMERCIAL_CSV)
                    registrar_log("Comercial", "Criar", item_id=prox_id, detalhe=f"Empresa criada (ID {prox_id}) com status 'Prospect'.")
                    st.success(f"✅ Empresa cadastrada com sucesso! ID: {prox_id}")
                    st.rerun()

    st.subheader("🏢 Empresas Comerciais Cadastradas")
    df = st.session_state.comercial_df.copy()
    if df.empty:
        st.info("Nenhum registro comercial cadastrado.")
    else:
        col1, col2 = st.columns([2, 1])
        with col1:
            busca = st.text_input("🔎 Buscar por Empresa ou Nome")
        with col2:
            status_opts = ["(todos)", "Prospect", "Lead Qualificado", "Reunião", "Proposta Enviada", "Negócio Fechado", "Declinado"]
            status_sel = st.selectbox("Status", status_opts, index=0)

        if busca:
            df = df[
                df["Empresa"].str.contains(busca, case=False, na=False) |
                df["Nome"].str.contains(busca, case=False, na=False)
            ]
        if status_sel != "(todos)":
            df = df[df["Status"] == status_sel]

        download_button(df, "comercial.csv", "⬇️ Baixar Lista Comercial")
        show_table(df, COMERCIAL_COLS, "comercial_df", COMERCIAL_CSV)
# ==============================
# Tela do menu e navegação
# ==============================
def tela_menu_interno():
    if st.session_state.usuario == "admin":
        if "ping_auto" not in st.session_state:
            st.session_state["ping_auto"] = False

        col_ping, col_blank = st.columns([1, 6])
        with col_ping:
            if st.session_state["ping_auto"]:
                if st.button("⏸️ Pausar Ping Automático", use_container_width=True):
                    st.session_state["ping_auto"] = False
                    st.success("Ping automático pausado!")
                    st.rerun()
            else:
                if st.button("▶️ Iniciar Ping Automático", use_container_width=True):
                    st.session_state["ping_auto"] = True
                    st.success("Ping automático iniciado!")
                    st.rerun()

# ==============================
# Carrega tela com base no usuário logado
# ==============================
if st.session_state.logged_in:
    st.image("https://parmaconsultoria.com.br/wp-content/uploads/2023/10/logo-parma-1.png", width=180)
    st.caption(f"Usuário: {st.session_state.usuario}")

    # Inclui "comercial" na lista de páginas permitidas para usuários com permissão
    page_label_map = {
        "menu": "Menu Principal",
        "clientes": "Clientes",
        "vagas": "Vagas",
        "candidatos": "Candidatos",
        "logs": "Logs do Sistema",
        "comercial": "Comercial",  # NOVO
    }

    # Verifica permissões e inclui a página "comercial" se for admin, andre ou ricardo
    usuario = st.session_state.usuario
    permissoes = st.session_state.permissoes.copy()
    if usuario in ["admin", "andre", "ricardo"]:
        if "comercial" not in permissoes:
            permissoes.append("comercial")
    st.session_state.permissoes = permissoes

    if "menu" not in permissoes:
        permissoes = ["menu"] + permissoes

    ordered_page_keys = ["menu", "clientes", "vagas", "candidatos", "comercial", "logs"]
    allowed_pages = [p for p in ordered_page_keys if p in permissoes]
    labels = [page_label_map[p] for p in allowed_pages]
    try:
        index_initial = allowed_pages.index(st.session_state.page)
    except Exception:
        index_initial = 0

    menu_cols = st.columns([1] * (len(labels) + 2))  # +2 para refresh e sair

    for i, label in enumerate(labels):
        if menu_cols[i].button(label, use_container_width=True):
            st.session_state.page = allowed_pages[i]
            st.rerun()

    if menu_cols[-2].button("🔄 Refresh", use_container_width=True):
        refresh_data()
        st.rerun()
    if menu_cols[-1].button("Sair", use_container_width=True):
        registrar_log("Login", "Logout", detalhe=f"Usuário {usuario} saiu do sistema.")
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()

    current_page = st.session_state.page
    if current_page == "menu":
        tela_menu_interno()
    elif current_page == "clientes":
        tela_clientes()
    elif current_page == "vagas":
        tela_vagas()
    elif current_page == "candidatos":
        tela_candidatos()
    elif current_page == "logs":
        tela_logs()
    elif current_page == "comercial":
        tela_comercial()
else:
    tela_login()
