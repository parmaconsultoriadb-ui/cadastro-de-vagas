import streamlit as st
import pandas as pd
from datetime import date

# Inicialização da sessão
if 'vagas' not in st.session_state:
    st.session_state.vagas = []

st.title("📋 Cadastro de Vagas")

# 🔁 Insere JavaScript para pular para o próximo campo ao apertar Enter
st.markdown("""
<script>
document.addEventListener("DOMContentLoaded", function () {
    const inputs = Array.from(document.querySelectorAll("input, select, textarea"));

    inputs.forEach((input, index) => {
        input.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();  // Impede envio do formulário
                const nextInput = inputs[index + 1];
                if (nextInput) {
                    nextInput.focus();
                }
            }
        });
    });
});
</script>
""", unsafe_allow_html=True)

with st.form("form_vaga"):
    status = st.selectbox("Status", ['Aberta', 'Fechada', 'Em andamento'])
    data_abertura = st.date_input("Data de Abertura", value=date.today())
    cliente = st.text_input("Cliente")
    cargo = st.text_input("Cargo")
    salario1 = st.number_input("Salário 1 (mínimo)", step=100.0, format="%.2f")
    salario2 = st.number_input("Salário 2 (máximo)", step=100.0, format="%.2f")
    recrutador = st.text_input("Recrutador")

    submitted = st.form_submit_button("Cadastrar Vaga")

    if submitted:
        if not cliente or not cargo or not recrutador:
            st.warning("⚠️ Preencha todos os campos obrigatórios: Cliente, Cargo e Recrutador.")
        elif salario1 == 0.0 or salario2 == 0.0:
            st.warning("⚠️ Os campos de salário não podem ser zero.")
        elif salario2 < salario1:
            st.warning("⚠️ O salário máximo não pode ser menor que o salário mínimo.")
        else:
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
