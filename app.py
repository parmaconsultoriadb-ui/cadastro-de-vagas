import streamlit as st
import pandas as pd
from datetime import date, datetime
import os
import re

# ==============================
# Configuração inicial da página
# ==============================
st.set_page_config(page_title="Parma Consultoria", layout="wide")

# ==============================
# CSVs de persistência
# ==============================
CLIENTES_CSV = "clientes.csv"
VAGAS_CSV = "vagas.csv"
CANDIDATOS_CSV = "candidatos.csv"
LOGS_CSV = "logs.csv"

# ==============================
# Funções auxiliares
# ==============================
def load_csv(file, default_cols):
    if os.path.exists(file):
        return pd.read_csv(file)
    else:
        return pd.DataFrame(columns=default_cols)

def save_csv(df, file):
    df.to_csv(file, index=False)

def log_action(user, action):
    log_df = load_csv(LOGS_CSV, ["DataHora", "Usuario", "Acao"])
    log_df = pd.concat([log_df, pd.DataFrame([{
        "DataHora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Usuario": user,
        "Acao": action
    }])], ignore_index=True)
    save_csv(log_df, LOGS_CSV)

def atualizar_status_vaga(vaga_id):
    candidatos = st.session_state.candidatos_df
    vaga_row = st.session_state.vagas_df[st.session_state.vagas_df["ID"] == vaga_id]
    if not vaga_row.empty:
        vaga_row = vaga_row.iloc[0]
        validados = candidatos[(candidatos["VagaID"]==vaga_id) & (candidatos["Status"]=="Validado")]
        desistentes = candidatos[(candidatos["VagaID"]==vaga_id) & (candidatos["Status"]=="Desistiu")]
        if len(validados) > 0:
            st.session_state.vagas_df.loc[st.session_state.vagas_df["ID"]==vaga_id, "Status"] = "Fechada"
        elif len(desistentes) == len(candidatos[candidatos["VagaID"]==vaga_id]):
            st.session_state.vagas_df.loc[st.session_state.vagas_df["ID"]==vaga_id, "Status"] = "Em Aberto"
        save_csv(st.session_state.vagas_df, VAGAS_CSV)

def validar_email(email):
    pattern = r"[^@]+@[^@]+\.[^@]+"
    return re.match(pattern, email)

def validar_telefone(telefone):
    pattern = r"^\+?\d{8,15}$"
    return re.match(pattern, telefone)

# ==============================
# Inicializar session_state
# ==============================
if "clientes_df" not in st.session_state:
    st.session_state.clientes_df = load_csv(CLIENTES_CSV, ["ID","Nome","Email","Telefone","Observacoes"])

if "vagas_df" not in st.session_state:
    st.session_state.vagas_df = load_csv(VAGAS_CSV, ["ID","Status","Cliente","Cargo","Salario1","Salario2","Descricao"])

if "candidatos_df" not in st.session_state:
    st.session_state.candidatos_df = load_csv(CANDIDATOS_CSV, ["ID","Nome","Email","Telefone","VagaID","Status","Observacoes"])

if "logs_df" not in st.session_state:
    st.session_state.logs_df = load_csv(LOGS_CSV, ["DataHora","Usuario","Acao"])

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "permissoes" not in st.session_state:
    st.session_state.permissoes = []

# ==============================
# Login simples
# ==============================
USUARIOS = {
    "admin": {"senha": "Admin@123", "permissoes":["menu","Clientes","Vagas","Candidatos"]},
    "lorrayne": {"senha": "Lrn!123@", "permissoes":["menu","Vagas","Candidatos"]}
}

def login():
    st.title("Login - Parma Consultoria")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
            st.session_state.usuario = usuario
            st.session_state.permissoes = USUARIOS[usuario]["permissoes"]
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos")

if st.session_state.usuario is None:
    login()
    st.stop()

# ==============================
# Menu lateral
# ==============================
menu = st.sidebar.selectbox("Menu", st.session_state.permissoes)

# ==============================
# Tela Clientes
# ==============================
def tela_clientes():
    st.header("Clientes")
    df = st.session_state.clientes_df

    with st.expander("Adicionar Cliente"):
        nome = st.text_input("Nome")
        email = st.text_input("Email")
        telefone = st.text_input("Telefone")
        obs = st.text_area("Observações")
        if st.button("Salvar"):
            if not nome or not email or not telefone:
                st.warning("Preencha todos os campos obrigatórios")
            elif not validar_email(email):
                st.warning("Email inválido")
            elif not validar_telefone(telefone):
                st.warning("Telefone inválido")
            else:
                new_id = df["ID"].max() + 1 if not df.empty else 1
                df = pd.concat([df, pd.DataFrame([{
                    "ID": new_id,
                    "Nome": nome,
                    "Email": email,
                    "Telefone": telefone,
                    "Observacoes": obs
                }])], ignore_index=True).reset_index(drop=True)
                st.session_state.clientes_df = df
                save_csv(df, CLIENTES_CSV)
                log_action(st.session_state.usuario, f"Adicionou cliente {nome}")
                st.success("Cliente adicionado")
    
    st.dataframe(df)

# ==============================
# Tela Vagas
# ==============================
def tela_vagas():
    st.header("Vagas")
    df = st.session_state.vagas_df

    with st.expander("Adicionar Vaga"):
        cliente = st.selectbox("Cliente", st.session_state.clientes_df["Nome"])
        cargo = st.text_input("Cargo")
        salario1 = st.number_input("Salário 1", 0.0)
        salario2 = st.number_input("Salário 2", 0.0)
        descricao = st.text_area("Descrição / Observações")
        if st.button("Salvar Vaga"):
            if not cliente or not cargo:
                st.warning("Preencha todos os campos obrigatórios")
            else:
                new_id = df["ID"].max() + 1 if not df.empty else 1
                df = pd.concat([df, pd.DataFrame([{
                    "ID": new_id,
                    "Status": "Em Aberto",
                    "Cliente": cliente,
                    "Cargo": cargo,
                    "Salario1": salario1,
                    "Salario2": salario2,
                    "Descricao": descricao
                }])], ignore_index=True).reset_index(drop=True)
                st.session_state.vagas_df = df
                save_csv(df, VAGAS_CSV)
                log_action(st.session_state.usuario, f"Adicionou vaga {cargo}")
                st.success("Vaga adicionada")

    st.dataframe(df)

# ==============================
# Tela Candidatos
# ==============================
def tela_candidatos():
    st.header("Candidatos")
    df = st.session_state.candidatos_df

    with st.expander("Adicionar Candidato"):
        nome = st.text_input("Nome", key="cand_nome")
        email = st.text_input("Email", key="cand_email")
        telefone = st.text_input("Telefone", key="cand_telefone")
        vaga_id = st.selectbox("Vaga", st.session_state.vagas_df["ID"])
        obs = st.text_area("Observações", key="cand_obs")
        status = st.selectbox("Status", ["Em Aberto","Validado","Desistiu"])
        if st.button("Salvar Candidato"):
            if not nome or not email or not telefone:
                st.warning("Preencha todos os campos obrigatórios")
            elif not validar_email(email):
                st.warning("Email inválido")
            elif not validar_telefone(telefone):
                st.warning("Telefone inválido")
            else:
                new_id = df["ID"].max() + 1 if not df.empty else 1
                df = pd.concat([df, pd.DataFrame([{
                    "ID": new_id,
                    "Nome": nome,
                    "Email": email,
                    "Telefone": telefone,
                    "VagaID": vaga_id,
                    "Status": status,
                    "Observacoes": obs
                }])], ignore_index=True).reset_index(drop=True)
                st.session_state.candidatos_df = df
                save_csv(df, CANDIDATOS_CSV)
                log_action(st.session_state.usuario, f"Adicionou candidato {nome}")
                atualizar_status_vaga(vaga_id)
                st.success("Candidato adicionado")

    st.dataframe(df)

    # Info vaga selecionada
    vaga_id_select = st.selectbox("Visualizar dados da vaga", st.session_state.vagas_df["ID"])
    vaga_row = st.session_state.vagas_df[st.session_state.vagas_df["ID"]==vaga_id_select]
    if not vaga_row.empty:
        vaga_row = vaga_row.iloc[0]
        st.subheader("Informações da vaga")
        st.write(f"Status: {vaga_row['Status']}")
        st.write(f"Cliente: {vaga_row['Cliente']}")
        st.write(f"Cargo: {vaga_row['Cargo']}")
        st.write(f"Salario 1: {vaga_row['Salario1']}")
        st.write(f"Salario 2: {vaga_row['Salario2']}")
        st.write(f"Descrição: {vaga_row['Descricao']}")

# ==============================
# Navegação
# ==============================
if menu == "Clientes":
    tela_clientes()
elif menu == "Vagas":
    tela_vagas()
elif menu == "Candidatos":
    tela_candidatos()
