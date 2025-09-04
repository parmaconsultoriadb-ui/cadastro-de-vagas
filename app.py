import streamlit as st
import pandas as pd
from datetime import date

# Inicialização da sessão
if 'vagas' not in st.session_state:
    st.session_state.vagas = []

if 'vaga_id' not in st.session_state:  # contador de IDs
    st.session_state.vaga_id = 1

st.title("📋 Cadastro de Vagas")

with st.form("form_vaga", enter_to_submit=False):  # 🚫 Enter não envia o formulário
    # Status fixo
    st.write("**Status:** Aberta")
    status = "Aberta"

    # Entrada de data (sempre objeto date)
    data_abertura = st.date_input("Data de Abertura", value=date.today())
    # Converter para string no formato brasileiro
    data_abertura_str = data_abertura.strftime("%d/%m/%Y")

    cliente = st.text_input("Cliente")
    cargo = st.text_input("Cargo")
    salario1 = st.number_input("Salário 1 (mínimo)", step=100.0, format="%.2f")
    salario2 = st.number_input("Salário 2 (máximo)", step=100.0, format="%.2f")
    recrutador = st.text_input("Recrutador")

    submitted = st.form_submit_button("Cadastrar Vaga")

    if submitted:
        # Validações
        if not cliente or not cargo or not recrutador:
            st.warning("⚠️ Preencha todos os campos obrigatórios: Cliente, Cargo e Recrutador.")
        elif cliente.isnumeric() or cargo.isnumeric() or recrutador.isnumeric():
            st.warn
