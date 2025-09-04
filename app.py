import streamlit as st
import pandas as pd
from datetime import date
import os

# ==============================
# Configuração inicial da página (modo wide)
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
# Inicialização do estado e carga de dados
# ==============================
if "page" not in st.session_state:
    st.session_state.page = "menu"

# Clientes
CLIENTES_COLS = ["ID", "Data", "Nome", "Cliente", "Cidade", "UF", "Telefone", "E-mail"]
if "clientes_df" not in st.session_state:
    st.session_state.clientes_df = load_csv(CLIENTES_CSV, CLIENTES_COLS)

# Vagas
VAGAS_COLS = ["ID", "Status", "Data de Abertura", "Cliente", "Cargo", "Salário 1", "Salário 2", "Recrutador", "Data de Fechamento"]
if "vagas_df" not in st.session_state:
    st.session_state.vagas_df = load_csv(VAGAS_CSV, VAGAS_COLS)

# Candidatos
CANDIDATOS_COLS = ["ID", "Cliente", "Cargo", "Nome", "Telefone", "Recrutador"]
if "candidatos_df" not in st.session_state:
    st.session_state.candidatos_df = load_csv(CANDIDATOS_CSV, CANDIDATOS_COLS)

# ==============================
# Estilo (botões azul royal)
# ==============================
st.markdown(
    """
    <style>
    div.stButton > button {
        background-color: royalblue !important;
        color: white !important;
        border-radius: 8px;
        height: 3em;
        font-size: 16px;
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
# Tela de Clientes
# ==============================
def tela_clientes():
    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()

    st.markdown("<h1 style='font-size:36px;'>👥 Cadastro de Clientes</h1>", unsafe_allow_html=True)
    data_hoje = date.today().strftime("%d/%m/%Y")

    with st.form("form_clientes", enter_to_submit=False):
        col_id, col_data = st.columns([1, 2])
        with col_id:
            st.text_input("ID", value="", disabled=True)
        with col_data:
            st.text_input("Data", value=data_hoje, disabled=True)

        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome *")
            cliente = st.text_input("Cliente *")
            cidade = st.text_input("Cidade *")
            uf = st.text_input("UF *", max_chars=2)
        with col2:
            telefone = st.text_input("Telefone *")
            email = st.text_input("E-mail *")

        submitted = st.form_submit_button("Cadastrar Cliente", use_container_width=True)

        if submitted:
            if not all([nome.strip(), cliente.strip(), cidade.strip(), uf.strip(), telefone.strip(), email.strip()]):
                st.warning("⚠️ Preencha todos os campos obrigatórios.")
            else:
                prox_id = next_id(st.session_state.clientes_df, "ID")
                novo = pd.DataFrame([{
                    "ID": str(prox_id),
                    "Data": data_hoje,
                    "Nome": nome.strip(),
                    "Cliente": cliente.strip(),
                    "Cidade": cidade.strip(),
                    "UF": uf.strip().upper(),
                    "Telefone": telefone.strip(),
                    "E-mail": email.strip()
                }])
                st.session_state.clientes_df = pd.concat([st.session_state.clientes_df, novo], ignore_index=True)
                save_csv(st.session_state.clientes_df, CLIENTES_CSV)
                st.success(f"✅ Cliente cadastrado com sucesso! ID: {prox_id}")
                st.rerun()

    st.markdown("<h2 style='font-size:28px;'>📄 Clientes Cadastrados</h2>", unsafe_allow_html=True)
    if st.session_state.clientes_df.empty:
        st.info("Nenhum cliente cadastrado ainda.")
    else:
        st.dataframe(st.session_state.clientes_df, use_container_width=True)

# ==============================
# Tela de Vagas
# ==============================
def tela_vagas():
    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()

    st.markdown("<h1 style='font-size:36px;'>📋 Cadastro de Vagas</h1>", unsafe_allow_html=True)
    data_abertura = date.today().strftime("%d/%m/%Y")

    with st.form("form_vaga", enter_to_submit=False):
        st.write("**Status:** Aberta")
        st.text_input("ID", value="", disabled=True)
        st.text_input("Data de Abertura", value=data_abertura, disabled=True)
        cliente = st.text_input("Cliente *")
        cargo = st.text_input("Cargo *")
        salario1 = st.number_input("Salário 1", step=100.0, format="%.2f", value=0.0)
        salario2 = st.number_input("Salário 2", step=100.0, format="%.2f", value=0.0)
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
                    "Cliente": cliente.strip(),
                    "Cargo": cargo.strip(),
                    "Salário 1": f"{float(salario1):.2f}",
                    "Salário 2": f"{float(salario2):.2f}",
                    "Recrutador": recrutador.strip(),
                    "Data de Fechamento": ""
                }])
                st.session_state.vagas_df = pd.concat([st.session_state.vagas_df, nova], ignore_index=True)
                save_csv(st.session_state.vagas_df, VAGAS_CSV)
                st.success(f"✅ Vaga cadastrada com sucesso! ID: {prox_id}")
                st.rerun()

    st.markdown("<h2 style='font-size:28px;'>📄 Vagas Cadastradas</h2>", unsafe_allow_html=True)
    if st.session_state.vagas_df.empty:
        st.info("Nenhuma vaga cadastrada ainda.")
    else:
        st.dataframe(st.session_state.vagas_df, use_container_width=True)

# ==============================
# Tela de Candidatos
# ==============================
def tela_candidatos():
    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()

    st.markdown("<h1 style='font-size:36px;'>🧑‍💼 Cadastro de Candidatos</h1>", unsafe_allow_html=True)
    if st.session_state.clientes_df.empty:
        st.warning("⚠️ Cadastre um Cliente antes de cadastrar Candidatos.")
        return

    with st.form("form_candidatos", enter_to_submit=False):
        st.text_input("ID", value="", disabled=True)
        lista_clientes = st.session_state.clientes_df["Cliente"].dropna().unique().tolist()
        cliente_sel = st.selectbox("Cliente *", options=lista_clientes)
        cargo = st.text_input("Cargo *")
        nome = st.text_input("Nome *")
        telefone = st.text_input("Telefone *")
        recrutador = st.text_input("Recrutador *")

        submitted = st.form_submit_button("Cadastrar Candidato", use_container_width=True)

        if submitted:
            if not all([cliente_sel, cargo.strip(), nome.strip(), telefone.strip(), recrutador.strip()]):
                st.warning("⚠️ Preencha todos os campos obrigatórios.")
            else:
                prox_id = next_id(st.session_state.candidatos_df, "ID")
                novo = pd.DataFrame([{
                    "ID": str(prox_id),
                    "Cliente": cliente_sel,
                    "Cargo": cargo.strip(),
                    "Nome": nome.strip(),
                    "Telefone": telefone.strip(),
                    "Recrutador": recrutador.strip()
                }])
                st.session_state.candidatos_df = pd.concat([st.session_state.candidatos_df, novo], ignore_index=True)
                save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)
                st.success(f"✅ Candidato cadastrado com sucesso! ID: {prox_id}")
                st.rerun()

    st.markdown("<h2 style='font-size:28px;'>📄 Candidatos Cadastrados</h2>", unsafe_allow_html=True)
    if st.session_state.candidatos_df.empty:
        st.info("Nenhum candidato cadastrado ainda.")
    else:
        st.dataframe(st.session_state.candidatos_df, use_container_width=True)

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
