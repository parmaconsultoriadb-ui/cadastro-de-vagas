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

# ==============================
# Funções auxiliares
# ==============================
def carregar_csv(caminho):
    if os.path.exists(caminho):
        return pd.read_csv(caminho)
    else:
        return pd.DataFrame()

def salvar_csv(df, caminho):
    df.to_csv(caminho, index=False)

def atualizar_timestamp(df, indice):
    df.loc[indice, "Atualizado"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return df

# ==============================
# Carregar os dados
# ==============================
clientes_df = carregar_csv(CLIENTES_CSV)
vagas_df = carregar_csv(VAGAS_CSV)
candidatos_df = carregar_csv(CANDIDATOS_CSV)

# Garante coluna "Atualizado" nas tabelas
for df in [vagas_df, candidatos_df]:
    if "Atualizado" not in df.columns:
        df["Atualizado"] = ""

# ==============================
# Login simples (usuário admin)
# ==============================
usuario = st.sidebar.text_input("Usuário")
eh_admin = (usuario == "admin")

# ==============================
# Páginas do app
# ==============================
pagina = st.sidebar.selectbox("Selecione a página", ["Clientes", "Vagas", "Candidatos"])

# ==============================
# Página Clientes
# ==============================
if pagina == "Clientes":
    st.title("Clientes")

    if eh_admin:
        if st.button("Importar Clientes"):
            arquivo = st.file_uploader("Selecione um CSV de Clientes", type="csv")
            if arquivo is not None:
                clientes_df = pd.read_csv(arquivo)
                salvar_csv(clientes_df, CLIENTES_CSV)
                st.success("Clientes importados com sucesso!")

    st.dataframe(clientes_df)

# ==============================
# Página Vagas
# ==============================
elif pagina == "Vagas":
    st.title("Vagas")

    # --- Filtros com autocomplete ---
    col1, col2, col3, col4 = st.columns(4)
    filtro_cliente = col1.selectbox("Cliente", [""] + sorted(vagas_df["Cliente"].dropna().unique().tolist()))
    filtro_cargo = col2.selectbox("Cargo", [""] + sorted(vagas_df["Cargo"].dropna().unique().tolist()))
    filtro_recrutador = col3.selectbox("Recrutador", [""] + sorted(vagas_df["Recrutador"].dropna().unique().tolist()))
    filtro_status = col4.selectbox("Status", [""] + sorted(vagas_df["Status"].dropna().unique().tolist()))

    filtrado = vagas_df.copy()
    if filtro_cliente:
        filtrado = filtrado[filtrado["Cliente"] == filtro_cliente]
    if filtro_cargo:
        filtrado = filtrado[filtrado["Cargo"] == filtro_cargo]
    if filtro_recrutador:
        filtrado = filtrado[filtrado["Recrutador"] == filtro_recrutador]
    if filtro_status:
        filtrado = filtrado[filtrado["Status"] == filtro_status]

    # --- Oculta coluna ID e mostra "Atualizado" ---
    colunas_visiveis = [c for c in filtrado.columns if c != "ID"]
    st.dataframe(filtrado[colunas_visiveis])

    # --- Importar vagas (apenas admin) ---
    if eh_admin:
        if st.button("Importar Vagas"):
            arquivo = st.file_uploader("Selecione um CSV de Vagas", type="csv")
            if arquivo is not None:
                vagas_df = pd.read_csv(arquivo)
                if "Atualizado" not in vagas_df.columns:
                    vagas_df["Atualizado"] = ""
                salvar_csv(vagas_df, VAGAS_CSV)
                st.success("Vagas importadas com sucesso!")

    # --- Formulário para nova vaga ---
    st.subheader("Cadastrar Nova Vaga")
    with st.form("form_vaga"):
        cliente = st.selectbox("Cliente", sorted(clientes_df["Cliente"].dropna().unique().tolist()))
        cargo = st.text_input("Cargo")
        status = "Aberta"  # Travado
        data_abertura = date.today().strftime("%d/%m/%Y")
        recrutador = st.text_input("Recrutador")
        data_inicio = st.date_input("Data de Início", value=None)

        if st.form_submit_button("Cadastrar"):
            nova_vaga = {
                "ID": len(vagas_df) + 1,
                "Cliente": cliente,
                "Status": status,
                "Data de Abertura": data_abertura,
                "Cargo": cargo,
                "Recrutador": recrutador,
                "Data de Início": data_inicio.strftime("%d/%m/%Y") if data_inicio else "",
                "Atualizado": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            vagas_df = pd.concat([vagas_df, pd.DataFrame([nova_vaga])], ignore_index=True)
            salvar_csv(vagas_df, VAGAS_CSV)
            st.success("Vaga cadastrada com sucesso!")

    # --- Edição de vaga (bloquear alguns campos) ---
    st.subheader("Editar Vaga")
    if not vagas_df.empty:
        vaga_id = st.selectbox("Selecione a vaga pelo ID", vagas_df["ID"])
        vaga = vagas_df[vagas_df["ID"] == vaga_id].iloc[0]

        with st.form("form_editar_vaga"):
            st.text_input("ID", value=vaga["ID"], disabled=True)
            st.text_input("Cliente", value=vaga["Cliente"], disabled=True)
            st.text_input("Data de Abertura", value=vaga["Data de Abertura"], disabled=True)
            st.text_input("Cargo", value=vaga["Cargo"], disabled=True)
            status = st.selectbox("Status", ["Aberta", "Ag. Início", "Fechada"], index=["Aberta", "Ag. Início", "Fechada"].index(vaga["Status"]))
            recrutador = st.text_input("Recrutador", value=vaga["Recrutador"])
            data_inicio = st.text_input("Data de Início", value=vaga["Data de Início"], disabled=True)

            if st.form_submit_button("Salvar alterações"):
                vagas_df.loc[vagas_df["ID"] == vaga_id, ["Status", "Recrutador"]] = [status, recrutador]
                vagas_df = atualizar_timestamp(vagas_df, vagas_df["ID"] == vaga_id)
                salvar_csv(vagas_df, VAGAS_CSV)
                st.success("Vaga atualizada com sucesso!")

# ==============================
# Página Candidatos
# ==============================
elif pagina == "Candidatos":
    st.title("Candidatos")

    # --- Filtros com autocomplete ---
    col1, col2, col3, col4 = st.columns(4)
    filtro_cliente = col1.selectbox("Cliente", [""] + sorted(candidatos_df["Cliente"].dropna().unique().tolist()))
    filtro_cargo = col2.selectbox("Cargo", [""] + sorted(candidatos_df["Cargo"].dropna().unique().tolist()))
    filtro_recrutador = col3.selectbox("Recrutador", [""] + sorted(candidatos_df["Recrutador"].dropna().unique().tolist()))
    filtro_status = col4.selectbox("Status", [""] + sorted(candidatos_df["Status"].dropna().unique().tolist()))

    filtrado = candidatos_df.copy()
    if filtro_cliente:
        filtrado = filtrado[filtrado["Cliente"] == filtro_cliente]
    if filtro_cargo:
        filtrado = filtrado[filtrado["Cargo"] == filtro_cargo]
    if filtro_recrutador:
        filtrado = filtrado[filtrado["Recrutador"] == filtro_recrutador]
    if filtro_status:
        filtrado = filtrado[filtrado["Status"] == filtro_status]

    st.dataframe(filtrado)

    # --- Importar candidatos (apenas admin) ---
    if eh_admin:
        if st.button("Importar Candidatos"):
            arquivo = st.file_uploader("Selecione um CSV de Candidatos", type="csv")
            if arquivo is not None:
                candidatos_df = pd.read_csv(arquivo)
                if "Atualizado" not in candidatos_df.columns:
                    candidatos_df["Atualizado"] = ""
                salvar_csv(candidatos_df, CANDIDATOS_CSV)
                st.success("Candidatos importados com sucesso!")

    # --- Edição de candidato (bloquear alguns campos + campo Atualizado) ---
    st.subheader("Editar Candidato")
    if not candidatos_df.empty:
        cand_id = st.selectbox("Selecione o candidato pelo ID", candidatos_df["ID"])
        cand = candidatos_df[candidatos_df["ID"] == cand_id].iloc[0]

        with st.form("form_editar_cand"):
            st.text_input("ID", value=cand["ID"], disabled=True)
            st.text_input("Cliente", value=cand["Cliente"], disabled=True)
            st.text_input("Cargo", value=cand["Cargo"], disabled=True)
            st.text_input("Nome", value=cand["Nome"], disabled=True)
            st.text_input("Telefone", value=cand["Telefone"], disabled=True)
            recrutador = st.text_input("Recrutador", value=cand["Recrutador"])
            status = st.selectbox("Status", ["Validado", "Entrevista", "Reprovado", "Contratado"], index=["Validado", "Entrevista", "Reprovado", "Contratado"].index(cand["Status"]))
            data_inicio = st.text_input("Data de Início", value=cand["Data de Início"])
            atualizado = st.text_input("Atualizado", value=cand["Atualizado"], disabled=True)

            if st.form_submit_button("Salvar alterações"):
                candidatos_df.loc[candidatos_df["ID"] == cand_id, ["Recrutador", "Status", "Data de Início"]] = [recrutador, status, data_inicio]
                candidatos_df = atualizar_timestamp(candidatos_df, candidatos_df["ID"] == cand_id)
                salvar_csv(candidatos_df, CANDIDATOS_CSV)
                st.success("Candidato atualizado com sucesso!")
