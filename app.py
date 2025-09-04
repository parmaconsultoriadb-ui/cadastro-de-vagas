import streamlit as st
import pandas as pd
from datetime import date
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
# Inicialização do estado
# ==============================
if "page" not in st.session_state:
    st.session_state.page = "menu"

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = None
if "edit_record" not in st.session_state:
    st.session_state.edit_record = {}

# Definição das colunas
CLIENTES_COLS = ["ID", "Data", "Nome", "Cliente", "Cidade", "UF", "Telefone", "E-mail"]
VAGAS_COLS = ["ID", "Status", "Data de Abertura", "Cliente", "Cargo", "Salário 1", "Salário 2", "Recrutador", "Data de Fechamento"]
CANDIDATOS_COLS = ["ID", "Cliente", "Cargo", "Nome", "Telefone", "Recrutador"]

# Carregar CSVs
if "clientes_df" not in st.session_state:
    st.session_state.clientes_df = load_csv(CLIENTES_CSV, CLIENTES_COLS)
if "vagas_df" not in st.session_state:
    st.session_state.vagas_df = load_csv(VAGAS_CSV, VAGAS_COLS)
if "candidatos_df" not in st.session_state:
    st.session_state.candidatos_df = load_csv(CANDIDATOS_CSV, CANDIDATOS_COLS)

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
    unsafe_allow_html=True
)

# ==============================
# Funções auxiliares
# ==============================
def show_edit_form(df_name, cols, csv_path):
    record = st.session_state.edit_record
    with st.form("edit_form", enter_to_submit=False):
        new_data = {}
        for c in cols:
            if c == "ID":
                new_data[c] = st.text_input(c, value=record[c], disabled=True)
            else:
                new_data[c] = st.text_input(c, value=record[c])
        submitted = st.form_submit_button("Salvar Alterações", use_container_width=True)
        if submitted:
            df = st.session_state[df_name]
            idx = df[df["ID"] == record["ID"]].index
            if not idx.empty:
                for c in cols:
                    df.loc[idx, c] = new_data[c]
                st.session_state[df_name] = df
                save_csv(df, csv_path)
                st.success("✅ Registro atualizado com sucesso!")
                st.session_state.edit_mode = None
                st.session_state.edit_record = {}
                st.rerun()

    if st.button("❌ Cancelar Edição", use_container_width=True):
        st.session_state.edit_mode = None
        st.session_state.edit_record = {}
        st.rerun()

def show_table(df, cols, df_name, csv_path):
    # Cabeçalho estilizado
    cols_ui = st.columns(len(cols) + 2)
    for i, c in enumerate(cols):
        cols_ui[i].markdown(
            f"<div style='background-color:#f0f0f0; padding:6px; font-weight:bold; color:black; border-radius:4px; text-align:center;'>{c}</div>",
            unsafe_allow_html=True
        )
    cols_ui[-2].markdown(
        "<div style='background-color:#f0f0f0; padding:6px; font-weight:bold; color:black; border-radius:4px; text-align:center;'>Editar</div>",
        unsafe_allow_html=True
    )
    cols_ui[-1].markdown(
        "<div style='background-color:#f0f0f0; padding:6px; font-weight:bold; color:black; border-radius:4px; text-align:center;'>Excluir</div>",
        unsafe_allow_html=True
    )

    # Linhas da tabela (zebrado + centralizado)
    for idx, row in df.iterrows():
        bg_color = "#ffffff" if idx % 2 == 0 else "#f9f9f9"  # zebra
        cols_ui = st.columns(len(cols) + 2)
        for i, c in enumerate(cols):
            cols_ui[i].markdown(
                f"<div style='background-color:{bg_color}; padding:6px; text-align:center; color:black;'>{row[c]}</div>",
                unsafe_allow_html=True
            )

        # Botão Editar (texto)
        with cols_ui[-2]:
            if st.button("Editar", key=f"edit_{df_name}_{row['ID']}", use_container_width=True):
                st.session_state.edit_mode = df_name
                st.session_state.edit_record = row.to_dict()
                st.rerun()

        # Botão Excluir (texto)
        with cols_ui[-1]:
            if st.button("Excluir", key=f"del_{df_name}_{row['ID']}", use_container_width=True):
                df2 = df[df["ID"] != row["ID"]]
                st.session_state[df_name] = df2
                save_csv(df2, csv_path)
                st.success(f"Registro {row['ID']} excluído com sucesso!")
                st.rerun()

    st.divider()

def download_button(df, filename, label="⬇️ Baixar CSV"):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime="text/csv",
        use_container_width=True
    )

# ==============================
# Telas
# ==============================
def tela_clientes():
    if st.session_state.edit_mode == "clientes_df":
        st.markdown("### ✏️ Editar Cliente")
        show_edit_form("clientes_df", CLIENTES_COLS, CLIENTES_CSV)
        return

    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()

    st.header("👥 Cadastro de Clientes")
    data_hoje = date.today().strftime("%d/%m/%Y")

    with st.form("form_clientes", enter_to_submit=False):
        nome = st.text_input("Nome *")
        cliente = st.text_input("Cliente *")
        cidade = st.text_input("Cidade *")
        uf = st.text_input("UF *", max_chars=2)
        telefone = st.text_input("Telefone *")
        email = st.text_input("E-mail *")
        submitted = st.form_submit_button("Cadastrar Cliente", use_container_width=True)

        if submitted:
            if not all([nome, cliente, cidade, uf, telefone, email]):
                st.warning("⚠️ Preencha todos os campos obrigatórios.")
            else:
                prox_id = next_id(st.session_state.clientes_df, "ID")
                novo = pd.DataFrame([{
                    "ID": str(prox_id),
                    "Data": data_hoje,
                    "Nome": nome,
                    "Cliente": cliente,
                    "Cidade": cidade,
                    "UF": uf.upper(),
                    "Telefone": telefone,
                    "E-mail": email
                }])
                st.session_state.clientes_df = pd.concat([st.session_state.clientes_df, novo], ignore_index=True)
                save_csv(st.session_state.clientes_df, CLIENTES_CSV)
                st.success(f"✅ Cliente cadastrado com sucesso! ID: {prox_id}")
                st.rerun()

    st.subheader("📄 Clientes Cadastrados")
    df = st.session_state.clientes_df
    if df.empty:
        st.info("Nenhum cliente cadastrado.")
    else:
        filtro = st.text_input("🔎 Buscar por Cliente")
        df_filtrado = df[df["Cliente"].str.contains(filtro, case=False, na=False)] if filtro else df
        download_button(df_filtrado, "clientes.csv", "⬇️ Baixar Clientes")
        show_table(df_filtrado, CLIENTES_COLS, "clientes_df", CLIENTES_CSV)

def tela_vagas():
    if st.session_state.edit_mode == "vagas_df":
        st.markdown("### ✏️ Editar Vaga")
        show_edit_form("vagas_df", VAGAS_COLS, VAGAS_CSV)
        return

    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()

    st.header("📋 Cadastro de Vagas")
    data_abertura = date.today().strftime("%d/%m/%Y")

    with st.form("form_vaga", enter_to_submit=False):
        lista_clientes = st.session_state.clientes_df["Cliente"].dropna().unique().tolist()
        cliente = st.selectbox("Cliente * (digite para buscar)", options=lista_clientes) if lista_clientes else st.text_input("Cliente *")
        cargo = st.text_input("Cargo *")
        salario1 = st.text_input("Salário 1")
        salario2 = st.text_input("Salário 2")
        recrutador = st.text_input("Recrutador *")
        submitted = st.form_submit_button("Cadastrar Vaga", use_container_width=True)

        if submitted:
            if not cliente or not cargo or not recrutador:
                st.warning("⚠️ Preencha todos os campos obrigatórios.")
            else:
                prox_id = next_id(st.session_state.vagas_df, "ID")
                nova = pd.DataFrame([{
                    "ID": str(prox_id),
                    "Status": "Aberta",
                    "Data de Abertura": data_abertura,
                    "Cliente": cliente,
                    "Cargo": cargo,
                    "Salário 1": salario1,
                    "Salário 2": salario2,
                    "Recrutador": recrutador,
                    "Data de Fechamento": ""
                }])
                st.session_state.vagas_df = pd.concat([st.session_state.vagas_df, nova], ignore_index=True)
                save_csv(st.session_state.vagas_df, VAGAS_CSV)
                st.success(f"✅ Vaga cadastrada com sucesso! ID: {prox_id}")
                st.rerun()

    st.subheader("📄 Vagas Cadastradas")
    df = st.session_state.vagas_df
    if df.empty:
        st.info("Nenhuma vaga cadastrada.")
    else:
        col1, col2, col3 = st.columns(3)
        filtro_status = col1.text_input("🔎 Buscar por Status")
        filtro_cliente = col2.text_input("🔎 Buscar por Cliente")
        filtro_cargo = col3.text_input("🔎 Buscar por Cargo")

        df_filtrado = df
        if filtro_status:
            df_filtrado = df_filtrado[df_filtrado["Status"].str.contains(filtro_status, case=False, na=False)]
        if filtro_cliente:
            df_filtrado = df_filtrado[df_filtrado["Cliente"].str.contains(filtro_cliente, case=False, na=False)]
        if filtro_cargo:
            df_filtrado = df_filtrado[df_filtrado["Cargo"].str.contains(filtro_cargo, case=False, na=False)]

        download_button(df_filtrado, "vagas.csv", "⬇️ Baixar Vagas")
        show_table(df_filtrado, VAGAS_COLS, "vagas_df", VAGAS_CSV)

def tela_candidatos():
    if st.session_state.edit_mode == "candidatos_df":
        st.markdown("### ✏️ Editar Candidato")
        show_edit_form("candidatos_df", CANDIDATOS_COLS, CANDIDATOS_CSV)
        return

    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()

    st.header("🧑‍💼 Cadastro de Candidatos")
    if st.session_state.vagas_df.empty:
        st.warning("⚠️ Cadastre uma Vaga antes de cadastrar Candidatos.")
        return

    with st.form("form_candidatos", enter_to_submit=False):
        clientes_com_vagas = st.session_state.vagas_df["Cliente"].dropna().unique().tolist()
        cliente_sel = st.selectbox("Cliente *", options=clientes_com_vagas) if clientes_com_vagas else st.text_input("Cliente *")

        lista_cargos = st.session_state.vagas_df["Cargo"].dropna().unique().tolist()
        cargo = st.selectbox("Cargo * (digite para buscar)", options=lista_cargos) if lista_cargos else st.text_input("Cargo *")

        nome = st.text_input("Nome *")
        telefone = st.text_input("Telefone *")
        recrutador = st.text_input("Recrutador *")
        submitted = st.form_submit_button("Cadastrar Candidato", use_container_width=True)

        if submitted:
            if not all([cliente_sel, cargo, nome, telefone, recrutador]):
                st.warning("⚠️ Preencha todos os campos obrigatórios.")
            else:
                prox_id = next_id(st.session_state.candidatos_df, "ID")
                novo = pd.DataFrame([{
                    "ID": str(prox_id),
                    "Cliente": cliente_sel,
                    "Cargo": cargo,
                    "Nome": nome,
                    "Telefone": telefone,
                    "Recrutador": recrutador
                }])
                st.session_state.candidatos_df = pd.concat([st.session_state.candidatos_df, novo], ignore_index=True)
                save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)
                st.success(f"✅ Candidato cadastrado com sucesso! ID: {prox_id}")
                st.rerun()

    st.subheader("📄 Candidatos Cadastrados")
    df = st.session_state.candidatos_df
    if df.empty:
        st.info("Nenhum candidato cadastrado.")
    else:
        col1, col2, col3 = st.columns(3)
        filtro_cliente = col1.text_input("🔎 Buscar por Cliente")
        filtro_cargo = col2.text_input("🔎 Buscar por Cargo")
        filtro_recrutador = col3.text_input("🔎 Buscar por Recrutador")

        df_filtrado = df
        if filtro_cliente:
            df_filtrado = df_filtrado[df_filtrado["Cliente"].str.contains(filtro_cliente, case=False, na=False)]
        if filtro_cargo:
            df_filtrado = df_filtrado[df_filtrado["Cargo"].str.contains(filtro_cargo, case=False, na=False)]
        if filtro_recrutador:
            df_filtrado = df_filtrado[df_filtrado["Recrutador"].str.contains(filtro_recrutador, case=False, na=False)]

        download_button(df_filtrado, "candidatos.csv", "⬇️ Baixar Candidatos")
        show_table(df_filtrado, CANDIDATOS_COLS, "candidatos_df", CANDIDATOS_CSV)

# ==============================
# Menu principal
# ==============================
if st.session_state.page == "menu":
    st.markdown("<h1 style='font-size:40px; color:royalblue;'>Parma Consultoria</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👥 Cadastro de Clientes", use_container_width=True):
            st.session_state.page = "clientes"
            st.rerun()
    with col2:
        if st.button("📋 Cadastro de Vagas", use_container_width=True):
            st.session_state.page = "vagas"
            st.rerun()
    with col3:
        if st.button("🧑‍💼 Cadastro de Candidatos", use_container_width=True):
            st.session_state.page = "candidatos"
            st.rerun()

elif st.session_state.page == "clientes":
    tela_clientes()
elif st.session_state.page == "vagas":
    tela_vagas()
elif st.session_state.page == "candidatos":
    tela_candidatos()
