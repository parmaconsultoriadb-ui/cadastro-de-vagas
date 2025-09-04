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
    status = st.selectbox("Status", ['Aberta', 'Fechada', 'Em andamento'])
    data_abertura = st.date_input("Data de Abertura", value=date.today())
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
        elif salario1 == 0.0 or salario2 == 0.0:
            st.warning("⚠️ Os campos de salário não podem ser zero.")
        elif salario2 < salario1:
            st.warning("⚠️ O salário máximo não pode ser menor que o salário mínimo.")
        else:
            # Adiciona a vaga com ID
            st.session_state.vagas.append({
                "ID": st.session_state.vaga_id,  # chave primária
                "Status": status,
                "Data de Abertura": data_abertura.strftime('%d/%m/%Y'),  # ✅ formato BR
                "Cliente": cliente,
                "Cargo": cargo,
                "Salário 1": salario1,
                "Salário 2": salario2,
                "Recrutador": recrutador
            })
            st.session_state.vaga_id += 1  # incrementa o ID
            st.success("✅ Vaga cadastrada com sucesso!")

# Mostrar vagas cadastradas
if st.session_state.vagas:
    st.subheader("📄 Vagas Cadastradas")
    df = pd.DataFrame(st.session_state.vagas)
    # garantir que ID fique como primeira coluna
    cols = ["ID"] + [c for c in df.columns if c != "ID"]
    df = df[cols]
    st.dataframe(df)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📁 Exportar para CSV", csv, "vagas.csv", "text/csv")
else:
    st.info("Nenhuma vaga cadastrada ainda.")
