import streamlit as st
import pandas as pd
from datetime import date

# Configuração inicial da página (modo wide)
st.set_page_config(page_title="Cadastro de Vagas", layout="wide")

# Inicialização da sessão
if 'vagas' not in st.session_state:
    st.session_state.vagas = []

if 'vaga_id' not in st.session_state:  # contador de IDs
    st.session_state.vaga_id = 1

# Inicialização dos campos padrão (não conflitam com os widgets)
for campo in ["form_cliente", "form_cargo", "form_salario1", "form_salario2", "form_recrutador", "form_data_abertura"]:
    if campo not in st.session_state:
        if campo == "form_data_abertura":
            st.session_state[campo] = date.today()
        elif campo in ["form_salario1", "form_salario2"]:
            st.session_state[campo] = 0.0
        else:
            st.session_state[campo] = ""

# Título maior
st.markdown("<h1 style='font-size:36px;'>📋 Cadastro de Vagas</h1>", unsafe_allow_html=True)

with st.form("form_vaga", enter_to_submit=False):  
    st.write("**Status:** Aberta")
    status = "Aberta"

    data_abertura = st.date_input("Data de Abertura", value=st.session_state.form_data_abertura, key="data_abertura")
    data_abertura_str = data_abertura.strftime("%d/%m/%Y")

    cliente = st.text_input("Cliente", value=st.session_state.form_cliente, key="cliente")
    cargo = st.text_input("Cargo", value=st.session_state.form_cargo, key="cargo")
    salario1 = st.number_input("Salário 1 (mínimo)", step=100.0, format="%.2f", value=st.session_state.form_salario1, key="salario1")
    salario2 = st.number_input("Salário 2 (máximo)", step=100.0, format="%.2f", value=st.session_state.form_salario2, key="salario2")
    recrutador = st.text_input("Recrutador", value=st.session_state.form_recrutador, key="recrutador")

    submitted = st.form_submit_button("Cadastrar Vaga", use_container_width=True)

    if submitted:
        if not cliente or not cargo or not recrutador:
            st.warning("⚠️ Preencha todos os campos obrigatórios.")
        elif cliente.isnumeric() or cargo.isnumeric() or recrutador.isnumeric():
            st.warning("⚠️ Cliente, Cargo e Recrutador não podem ser apenas números.")
        elif salario1 == 0.0 or salario2 == 0.0:
            st.warning("⚠️ Os salários não podem ser zero.")
        elif salario2 < salario1:
            st.warning("⚠️ O salário máximo não pode ser menor que o salário mínimo.")
        else:
            st.session_state.vagas.append({
                "ID": st.session_state.vaga_id,
                "Status": status,
                "Data de Abertura": data_abertura_str,
                "Cliente": cliente,
                "Cargo": cargo,
                "Salário 1": salario1,
                "Salário 2": salario2,
                "Recrutador": recrutador,
                "Data de Fechamento": ""
            })
            st.session_state.vaga_id += 1
            st.success("✅ Vaga cadastrada com sucesso!")

            # 🔄 Resetar campos default (sem conflito com widgets)
            st.session_state.form_cliente = ""
            st.session_state.form_cargo = ""
            st.session_state.form_salario1 = 0.0
            st.session_state.form_salario2 = 0.0
            st.session_state.form_recrutador = ""
            st.session_state.form_data_abertura = date.today()
            st.experimental_rerun()  # recarregar tela com campos limpos
