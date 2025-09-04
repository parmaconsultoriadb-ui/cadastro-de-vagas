import streamlit as st
import pandas as pd
from datetime import date

# Inicialização da sessão
if 'vagas' not in st.session_state:
    st.session_state.vagas = []

if 'vaga_id' not in st.session_state:  # contador de IDs
    st.session_state.vaga_id = 1

st.title("📋 Cadastro de Vagas")

with st.form("form_vaga", enter_to_submit=False):  
    st.write("**Status:** Aberta")
    status = "Aberta"

    data_abertura = st.date_input("Data de Abertura", value=date.today())
    data_abertura_str = data_abertura.strftime("%d/%m/%Y")

    cliente = st.text_input("Cliente")
    cargo = st.text_input("Cargo")
    salario1 = st.number_input("Salário 1 (mínimo)", step=100.0, format="%.2f")
    salario2 = st.number_input("Salário 2 (máximo)", step=100.0, format="%.2f")
    recrutador = st.text_input("Recrutador")

    submitted = st.form_submit_button("Cadastrar Vaga")

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

# Mostrar vagas cadastradas
if st.session_state.vagas:
    st.subheader("📄 Vagas Cadastradas")

    filtro_col1, filtro_col2 = st.columns([1, 2])
    with filtro_col1:
        filtro_status = st.selectbox("Filtrar por status:", ["Todas", "Aberta", "Fechada", "Em andamento"])
    with filtro_col2:
        filtro_cliente = st.text_input("Buscar por Cliente:")

    vagas_filtradas = st.session_state.vagas
    if filtro_status != "Todas":
        vagas_filtradas = [v for v in vagas_filtradas if v["Status"] == filtro_status]
    if filtro_cliente:
        vagas_filtradas = [v for v in vagas_filtradas if filtro_cliente.lower() in v["Cliente"].lower()]

    if vagas_filtradas:
        # Layout mais compacto
        header_cols = st.columns([1, 2, 2, 2, 2, 2, 2, 2, 1])
        headers = ["ID", "Status", "Abertura", "Cliente", "Cargo", "Salário 1", "Salário 2", "Fechamento", "🗑️"]
        for col, h in zip(header_cols, headers):
            col.markdown(f"**{h}**")

        for vaga in vagas_filtradas:
            cols = st.columns([1, 2, 2, 2, 2, 2, 2, 2, 1])
            cols[0].write(vaga["ID"])

            novo_status = cols[1].selectbox(
                "", ["Aberta", "Fechada", "Em andamento"],
                index=["Aberta", "Fechada", "Em andamento"].index(vaga["Status"]),
                key=f"status_{vaga['ID']}"
            )
            if novo_status != vaga["Status"]:
                for v in st.session_state.vagas:
                    if v["ID"] == vaga["ID"]:
                        v["Status"] = novo_status
                        v["Data de Fechamento"] = date.today().strftime("%d/%m/%Y") if novo_status == "Fechada" else ""

            cols[2].write(vaga["Data de Abertura"])
            cols[3].write(vaga["Cliente"])
            cols[4].write(vaga["Cargo"])
            cols[5].write(f"{vaga['Salário 1']:.0f}")  # mais compacto
            cols[6].write(f"{vaga['Salário 2']:.0f}")
            cols[7].write(vaga["Data de Fechamento"] if vaga["Data de Fechamento"] else "-")
            if cols[8].button("🗑️", key=f"del_{vaga['ID']}"):
                st.session_state.vagas = [v for v in st.session_state.vagas if v["ID"] != vaga["ID"]]
                st.experimental_rerun()

        df = pd.DataFrame(vagas_filtradas)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📁 Exportar para CSV", csv, "vagas.csv", "text/csv")
    else:
        st.info("Nenhuma vaga encontrada com os filtros aplicados.")
else:
    st.info("Nenhuma vaga cadastrada ainda.")
