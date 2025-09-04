import streamlit as st
import pandas as pd
from datetime import date

# Configuração inicial da página (modo wide)
st.set_page_config(page_title="Parma Consultoria", layout="wide")

# Controle de navegação
if "page" not in st.session_state:
    st.session_state.page = "menu"

# ==============================
# Função: Tela de Cadastro de Vagas
# ==============================
def tela_vagas():
    # ... (código igual ao que você já tem para tela_vagas)
    pass

# ==============================
# Função: Tela de Cadastro de Clientes (placeholder)
# ==============================
def tela_clientes():
    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()

    st.markdown("<h1 style='font-size:36px;'>👥 Cadastro de Clientes</h1>", unsafe_allow_html=True)
    st.info("Tela de cadastro de clientes em desenvolvimento...")

# ==============================
# Função: Tela de Cadastro de Candidatos (placeholder)
# ==============================
def tela_candidatos():
    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()

    st.markdown("<h1 style='font-size:36px;'>🧑‍💼 Cadastro de Candidatos</h1>", unsafe_allow_html=True)
    st.info("Tela de cadastro de candidatos em desenvolvimento...")

# ==============================
# Menu principal
# ==============================
if st.session_state.page == "menu":
    # Cabeçalho com logo + nome da empresa
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        st.image("logo_parma.png", width=100)  # 👉 coloque o arquivo logo_parma.png na mesma pasta do código
    with col_title:
        st.markdown("<h1 style='font-size:40px; color:royalblue;'>Parma Consultoria</h1>", unsafe_allow_html=True)

    st.write("Escolha uma das opções abaixo:")

    # 🔵 CSS para deixar todos os botões azul royal
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

elif st.session_state.page == "vagas":
    tela_vagas()
elif st.session_state.page == "clientes":
    tela_clientes()
elif st.session_state.page == "candidatos":
    tela_candidatos()
