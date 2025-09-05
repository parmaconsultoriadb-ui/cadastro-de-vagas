import streamlit as st
import pandas as pd
import os

# ==============================
# Configuração Inicial
# ==============================
st.set_page_config(page_title="Sistema Parma Consultoria", layout="wide")

# Arquivos locais
CLIENTES_CSV = "clientes.csv"
VAGAS_CSV = "vagas.csv"
CANDIDATOS_CSV = "candidatos.csv"

# ==============================
# Carregar lista de cargos do GitHub
# ==============================
CARGOS_URL = "https://raw.githubusercontent.com/parmaconsultoriadb-ui/cadastro-de-vagas/refs/heads/main/cargos.csv.csv"
try:
    df_cargos = pd.read_csv(CARGOS_URL)
    cargos_sugestoes = df_cargos.iloc[:, 0].dropna().unique().tolist()
except Exception as e:
    st.warning(f"⚠️ Não foi possível carregar os cargos do GitHub: {e}")
    cargos_sugestoes = []

# ==============================
# Funções Auxiliares
# ==============================
def load_data(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    else:
        return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

def show_table(df, cols, state_key, file):
    st.dataframe(df[cols], use_container_width=True)
    if st.button("🗑️ Limpar todos os dados", key=f"clear_{state_key}"):
        df.drop(df.index, inplace=True)
        save_data(df, file)
        st.rerun()

def download_button(df, filename, label):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label, csv, file_name=filename, mime="text/csv")

# ==============================
# Carregar Dados
# ==============================
clientes = load_data(CLIENTES_CSV, ["ID", "Cliente", "Responsavel", "Telefone", "Email"])
vagas = load_data(VAGAS_CSV, ["ID", "ClienteID", "Cargo", "Status"])
candidatos = load_data(CANDIDATOS_CSV, ["ID", "VagaID", "Status", "Nome", "Telefone", "Recrutador"])

if "page" not in st.session_state:
    st.session_state.page = "menu"

if "clientes_df" not in st.session_state:
    st.session_state.clientes_df = clientes
if "vagas_df" not in st.session_state:
    st.session_state.vagas_df = vagas
if "candidatos_df" not in st.session_state:
    st.session_state.candidatos_df = candidatos

# ==============================
# Telas
# ==============================
def tela_clientes():
    st.title("👥 Cadastro de Clientes")

    with st.form("cliente_form"):
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("Nome do Cliente *")
            telefone = st.text_input("Telefone")
        with col2:
            responsavel = st.text_input("Responsável")
            email = st.text_input("Email")

        submitted = st.form_submit_button("💾 Salvar")
        if submitted:
            if cliente.strip() == "":
                st.error("⚠️ O campo Nome do Cliente é obrigatório!")
            else:
                df = st.session_state.clientes_df
                prox_id = int(df["ID"].max() + 1) if not df.empty else 1
                novo = pd.DataFrame([[prox_id, cliente, responsavel, telefone, email]],
                                    columns=df.columns)
                df.loc[len(df)] = novo.iloc[0]
                save_data(df, CLIENTES_CSV)
                st.success(f"✅ Cliente cadastrado com sucesso! ID: {prox_id}")
                st.rerun()

    st.subheader("📄 Clientes Cadastrados")
    df = st.session_state.clientes_df
    if df.empty:
        st.info("Nenhum cliente cadastrado.")
    else:
        cols_show = ["ID", "Cliente", "Responsavel", "Telefone", "Email"]
        download_button(df[cols_show], "clientes.csv", "⬇️ Baixar Clientes")
        show_table(df, cols_show, "clientes_df", CLIENTES_CSV)

def tela_vagas():
    st.title("📋 Cadastro de Vagas")

    clientes = st.session_state.clientes_df
    if clientes.empty:
        st.warning("⚠️ Cadastre clientes antes de criar vagas.")
        return

    with st.form("vaga_form"):
        cliente_id = st.selectbox("Cliente *", clientes["ID"].astype(str) + " - " + clientes["Cliente"])
        
        # Campo de cargo com autocomplete
        cargo = st.selectbox(
            "Cargo *",
            options=cargos_sugestoes + ["(Outro)"],
            index=0,
            placeholder="Digite ou selecione um cargo"
        )

        if cargo == "(Outro)":
            cargo = st.text_input("Digite o Cargo")

        status = st.selectbox("Status", ["Aberta", "Fechada", "Pausada"])

        submitted = st.form_submit_button("💾 Salvar")
        if submitted:
            if not cliente_id or not cargo:
                st.error("⚠️ Cliente e Cargo são obrigatórios!")
            else:
                cliente_id = int(cliente_id.split(" - ")[0])
                df = st.session_state.vagas_df
                prox_id = int(df["ID"].max() + 1) if not df.empty else 1
                novo = pd.DataFrame([[prox_id, cliente_id, cargo, status]], columns=df.columns)
                df.loc[len(df)] = novo.iloc[0]
                save_data(df, VAGAS_CSV)
                st.success(f"✅ Vaga cadastrada com sucesso! ID: {prox_id}")
                st.rerun()

    st.subheader("📄 Vagas Cadastradas")
    df = st.session_state.vagas_df
    if df.empty:
        st.info("Nenhuma vaga cadastrada.")
    else:
        clientes_map = clientes.set_index("ID")["Cliente"].to_dict()
        df["Cliente"] = df["ClienteID"].map(clientes_map)
        cols_show = ["ID", "Cliente", "Cargo", "Status"]
        download_button(df[cols_show], "vagas.csv", "⬇️ Baixar Vagas")
        show_table(df, cols_show, "vagas_df", VAGAS_CSV)

def tela_candidatos():
    st.title("🧑‍💼 Cadastro de Candidatos")

    vagas = st.session_state.vagas_df
    clientes = st.session_state.clientes_df

    if vagas.empty:
        st.warning("⚠️ Cadastre vagas antes de cadastrar candidatos.")
        return

    with st.form("candidato_form"):
        vaga_id = st.selectbox("Vaga *", vagas["ID"].astype(str) + " - " + vagas["Cargo"])
        nome = st.text_input("Nome *")
        telefone = st.text_input("Telefone")
        recrutador = st.text_input("Recrutador")
        status = st.selectbox("Status", ["Novo", "Entrevista", "Aprovado", "Rejeitado"])

        submitted = st.form_submit_button("💾 Salvar")
        if submitted:
            if not vaga_id or not nome:
                st.error("⚠️ Vaga e Nome são obrigatórios!")
            else:
                vaga_id = int(vaga_id.split(" - ")[0])
                df = st.session_state.candidatos_df
                prox_id = int(df["ID"].max() + 1) if not df.empty else 1
                novo = pd.DataFrame([[prox_id, vaga_id, status, nome, telefone, recrutador]], columns=df.columns)
                df.loc[len(df)] = novo.iloc[0]
                save_data(df, CANDIDATOS_CSV)
                st.success(f"✅ Candidato cadastrado com sucesso! ID: {prox_id}")
                st.rerun()

    st.subheader("📄 Candidatos Cadastrados")
    df = st.session_state.candidatos_df
    if df.empty:
        st.info("Nenhum candidato cadastrado.")
    else:
        vagas_map = vagas.set_index("ID")[["Cargo", "ClienteID"]].to_dict("index")
        df["Vaga (Cliente - Cargo)"] = df["VagaID"].map(
            lambda vid: f"{clientes.loc[vagas_map[vid]['ClienteID'], 'Cliente']} - {vagas_map[vid]['Cargo']}"
            if vid in vagas_map else "Vaga não encontrada"
        )
        cols_show = ["ID", "Vaga (Cliente - Cargo)", "Status", "Nome", "Telefone", "Recrutador"]
        download_button(df[cols_show], "candidatos.csv", "⬇️ Baixar Candidatos")
        show_table(df, cols_show, "candidatos_df", CANDIDATOS_CSV)

def tela_menu():
    st.title("📊 Sistema Parma Consultoria")
    st.subheader("Escolha uma opção:")
    st.divider()
    if st.button("👥 Clientes", use_container_width=True):
        st.session_state.page = "clientes"
        st.rerun()
    if st.button("📋 Vagas", use_container_width=True):
        st.session_state.page = "vagas"
        st.rerun()
    if st.button("🧑‍💼 Candidatos", use_container_width=True):
        st.session_state.page = "candidatos"
        st.rerun()

# ==============================
# Roteamento
# ==============================
if st.session_state.page == "menu":
    tela_menu()
elif st.session_state.page == "clientes":
    tela_clientes()
elif st.session_state.page == "vagas":
    tela_vagas()
elif st.session_state.page == "candidatos":
    tela_candidatos()
