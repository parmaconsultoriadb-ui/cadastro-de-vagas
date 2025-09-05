import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

# ==============================
# Configuração inicial da página
# ==============================
st.set_page_config(page_title="Parma Consultoria", layout="wide")

# ==============================
# Persistência em CSV (helpers)
# ==============================
CLIENTES_CSV = "clientes.csv"
VAGAS_CSV = "vagas.csv"
CANDIDATOS_CSV = "candidatos.csv"
LOGS_CSV = "logs.csv"   # <-- Novo CSV de logs

def load_csv(path, expected_cols):
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, dtype=str)
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            df = df[expected_cols]
            return df
        except Exception:
            return pd.DataFrame(columns=expected_cols)
    return pd.DataFrame(columns=expected_cols)

def save_csv(df, path):
    df.to_csv(path, index=False, encoding="utf-8")

def next_id(df, id_col="ID"):
    if df.empty or df[id_col].isna().all():
        return 1
    try:
        vals = pd.to_numeric(df[id_col], errors="coerce").fillna(0).astype(int)
        return int(vals.max()) + 1
    except Exception:
        return 1

# ==============================
# Função de Logs
# ==============================
def registrar_log(acao, detalhe):
    datahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    log_df = pd.DataFrame([{
        "DataHora": datahora,
        "Ação": acao,
        "Detalhe": detalhe
    }])
    if os.path.exists(LOGS_CSV):
        atual = pd.read_csv(LOGS_CSV, dtype=str)
        log_df = pd.concat([atual, log_df], ignore_index=True)
    save_csv(log_df, LOGS_CSV)

def carregar_logs():
    if os.path.exists(LOGS_CSV):
        return pd.read_csv(LOGS_CSV, dtype=str)
    return pd.DataFrame(columns=["DataHora", "Ação", "Detalhe"])

# ==============================
# Inicialização do estado
# ==============================
if "page" not in st.session_state:
    st.session_state.page = "login"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = None
if "edit_record" not in st.session_state:
    st.session_state.edit_record = {}
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = {"df_name": None, "row_id": None}

# Definição das colunas
CLIENTES_COLS = ["ID", "Data", "Cliente", "Nome", "Cidade", "UF", "Telefone", "E-mail"]
VAGAS_COLS = [
    "ID","ClienteID","Status","Data de Abertura","Cargo",
    "Salário 1","Salário 2","Recrutador","Data de Fechamento"
]
CANDIDATOS_COLS = ["ID","VagaID","Status","Nome","Telefone","Recrutador"]

# Carregar CSVs locais
if "clientes_df" not in st.session_state:
    st.session_state.clientes_df = load_csv(CLIENTES_CSV, CLIENTES_COLS)
if "vagas_df" not in st.session_state:
    st.session_state.vagas_df = load_csv(VAGAS_CSV, VAGAS_COLS)
if "candidatos_df" not in st.session_state:
    st.session_state.candidatos_df = load_csv(CANDIDATOS_CSV, CANDIDATOS_COLS)

# ==============================
# Garantir integridade referencial
# ==============================
clientes_ids = set(st.session_state.clientes_df["ID"])
st.session_state.vagas_df = st.session_state.vagas_df[
    st.session_state.vagas_df["ClienteID"].isin(clientes_ids)
]
vagas_ids = set(st.session_state.vagas_df["ID"])
st.session_state.candidatos_df = st.session_state.candidatos_df[
    st.session_state.candidatos_df["VagaID"].isin(vagas_ids)
]

# ==============================
# Carregar lista de Cargos
# ==============================
CARGOS_URL = "https://raw.githubusercontent.com/parmaconsultoriadb-ui/cadastro-de-vagas/refs/heads/main/cargos.csv.csv"
try:
    cargos_df = pd.read_csv(CARGOS_URL, dtype=str)
    LISTA_CARGOS = cargos_df.iloc[:, 0].dropna().unique().tolist()
except Exception as e:
    st.warning(f"⚠️ Não foi possível carregar os cargos do GitHub: {e}")
    LISTA_CARGOS = []

# ==============================
# Estilo
# ==============================
st.markdown(
    """
    <style>
    div.stButton > button {
        background-color: royalblue !important;
        color: white !important;
        border-radius: 8px;
        height: 2.5em;
        font-size: 15px;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #27408B !important;
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================
# Telas principais
# ==============================
def tela_login():
    st.title("🔒 Login - Parma Consultoria")
    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        if submitted:
            if usuario == "admin" and senha == "Parma!123@":
                st.session_state.logged_in = True
                st.session_state.page = "menu"
                registrar_log("Login", f"Usuário {usuario} acessou o sistema.")
                st.success("✅ Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos.")

def tela_logs():
    st.header("📜 Logs do Sistema")
    df_logs = carregar_logs()
    if df_logs.empty:
        st.info("Nenhum log registrado ainda.")
    else:
        st.dataframe(df_logs, use_container_width=True)
        csv = df_logs.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Baixar Logs", csv, "logs.csv", "text/csv", use_container_width=True)
    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()

def tela_menu():
    st.title("📊 Sistema Parma Consultoria")
    st.subheader("Escolha uma opção:")
    st.divider()

    if st.button("👥 Clientes", use_container_width=True):
        st.session_state.page = "clientes"; st.rerun()
    if st.button("📋 Vagas", use_container_width=True):
        st.session_state.page = "vagas"; st.rerun()
    if st.button("🧑‍💼 Candidatos", use_container_width=True):
        st.session_state.page = "candidatos"; st.rerun()
    if st.button("📜 Logs", use_container_width=True):
        st.session_state.page = "logs"; st.rerun()

    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        registrar_log("Logout", "Usuário saiu do sistema.")
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()

# ==============================
# (demais telas continuam iguais, mas devem chamar registrar_log em cadastrar, editar, excluir)
# Exemplo:
# registrar_log("Novo Cliente", f"Cliente {cliente} cadastrado (ID {prox_id})")
# registrar_log("Excluir Vaga", f"Vaga {row_id} excluída")
# registrar_log("Editar Candidato", f"Candidato {record['Nome']} alterado")
# ==============================

# ==============================
# Roteamento
# ==============================
if st.session_state.page == "login":
    tela_login()
elif not st.session_state.logged_in:
    tela_login()
elif st.session_state.page == "menu":
    tela_menu()
elif st.session_state.page == "clientes":
    tela_clientes()
elif st.session_state.page == "vagas":
    tela_vagas()
elif st.session_state.page == "candidatos":
    tela_candidatos()
elif st.session_state.page == "logs":
    tela_logs()
