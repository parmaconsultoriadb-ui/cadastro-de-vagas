
import streamlit as st
import pandas as pd
from datetime import date

# Inicialização da sessão
if 'vagas' not in st.session_state:
    st.session_state.vagas = []

st.title("📋 Cadastro de Vagas")

with st.form("form_vaga"):
    status = st.selectbox("Status", ['Aberta', 'Fechada', 'Em andamento'])
    data_abertura = st.date_input("Data de Abertura", value=date.today())
    cliente = st.text_input("Cliente")
    cargo = st.text_input("Cargo")
    salario1 = st.number_input("Salário 1 (mínimo)", step=100.0)
    salario2 = st.number_input("Salário 2 (máximo)", step=100.0)
    recrutador = st.text_input("Recrutador")

    submitted = st.form_submit_button("Cadastrar Vaga")

    if submitted:
        # Validação de campos obrigatórios
        if not cliente or not cargo or not recrutador:
            st.warning("⚠️ Preencha todos os campos obrigatórios: Cliente, Cargo e Recrutador.")
        elif salario2 < salario1:
            st.warning("⚠️ O salário máximo não pode ser menor que o salário mínimo.")
        else:
            # Adiciona a vaga
            st.session_state.vagas.append({
                "Status": status,
                "Data de Abertura": data_abertura.strftime('%Y-%m-%d'),
                "Cliente": cliente,
                "Cargo": cargo,
                "Salário 1": salario1,
                "Salário 2": salario2,
                "Recrutador": recrutador
            })
            st.success("✅ Vaga cadastrada com sucesso!")

# Mostrar vagas cadastradas
if st.session_state.vagas:
    st.subheader("📄 Vagas Cadastradas")
    df = pd.DataFrame(st.session_state.vagas)
    st.dataframe(df)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📁 Exportar para CSV", csv, "vagas.csv", "text/csv")
else:
    st.info("Nenhuma vaga cadastrada ainda.")
