import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

# ==============================
# Configuração inicial da página
# ==============================
st.set_page_config(page_title="Parma Consultoria", layout="wide")

# ==============================
# Persistência em CSV
# ==============================
CLIENTES_CSV = "clientes.csv"
VAGAS_CSV = "vagas.csv"
CANDIDATOS_CSV = "candidatos.csv"
LOGS_CSV = "logs.csv"

def load_csv(path, expected_cols):
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, dtype=str)
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            return df[expected_cols]
        except Exception:
            return pd.DataFrame(columns=expected_cols)
    return pd.DataFrame(columns=expected_cols)

def save_csv(df, path):
    df.to_csv(path, index=False, encoding="utf-8")

def next_id(df, id_col="ID"):
    if df.empty or df[id_col].isna().all():
        return 1
    vals = pd.to_numeric(df[id_col], errors="coerce").fillna(0).astype(int)
    return int(vals.max()) + 1

# ==============================
# Logs
# ==============================
def registrar_log(acao, detalhe):
    datahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    log_df = pd.DataFrame([{"DataHora": datahora, "Ação": acao, "Detalhe": detalhe}])
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
CLIENTES_COLS = ["ID","Data","Cliente","Nome","Cidade","UF","Telefone","E-mail"]
VAGAS_COLS = ["ID","ClienteID","Status","Data de Abertura","Cargo","Salário 1","Salário 2","Recrutador","Data de Fechamento"]
CANDIDATOS_COLS = ["ID","VagaID","Status","Nome","Telefone","Recrutador"]

# Carregar CSVs locais
if "clientes_df" not in st.session_state:
    st.session_state.clientes_df = load_csv(CLIENTES_CSV, CLIENTES_COLS)
if "vagas_df" not in st.session_state:
    st.session_state.vagas_df = load_csv(VAGAS_CSV, VAGAS_COLS)
if "candidatos_df" not in st.session_state:
    st.session_state.candidatos_df = load_csv(CANDIDATOS_CSV, CANDIDATOS_COLS)

# ==============================
# Telas
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
                registrar_log("Login", f"Usuário {usuario} entrou no sistema.")
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
    if st.button("👥 Clientes", use_container_width=True):
        st.session_state.page = "clientes"; st.rerun()
    if st.button("📋 Vagas", use_container_width=True):
        st.session_state.page = "vagas"; st.rerun()
    if st.button("🧑‍💼 Candidatos", use_container_width=True):
        st.session_state.page = "candidatos"; st.rerun()
    if st.button("📜 Logs", use_container_width=True):
        st.session_state.page = "logs"; st.rerun()
    if st.button("🚪 Sair", use_container_width=True):
        registrar_log("Logout", "Usuário saiu do sistema.")
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()

# ==============================
# Ajustes nas operações CRUD
# ==============================
# 👉 Onde houver sucesso de cadastro, edição ou exclusão,
# insira chamadas como estas:
# registrar_log("Novo Cliente", f"Cliente {cliente} cadastrado (ID {prox_id})")
# registrar_log("Editar Vaga", f"Vaga {record['Cargo']} alterada (ID {record['ID']})")
# registrar_log("Excluir Candidato", f"Candidato {row['Nome']} excluído (ID {row['ID']})")
# ==============================

# (Restante das telas clientes, vagas e candidatos continuam iguais,
# mas cada ação agora chama registrar_log conforme os exemplos acima)

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
