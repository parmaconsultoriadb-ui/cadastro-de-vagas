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
            st.warning("⚠️ Os campos Cliente, Cargo e Recrutador não podem ser apenas números.")
        elif salario1 == 0.0 or salario2 == 0.0:
            st.warning("⚠️ Os campos de salário não podem ser zero.")
        elif salario2 < salario1:
            st.warning("⚠️ O salário máximo não pode ser menor que o salário mínimo.")
        else:
            # Adiciona a vaga com ID
            st.session_state.vagas.append({
                "ID": st.session_state.vaga_id,  # chave primária
                "Status": status,  # sempre "Aberta"
                "Data de Abertura": data_abertura_str,  # ✅ formato DD/MM/YYYY
                "Cliente": cliente,
                "Cargo": cargo,
                "Salário 1": salario1,
                "Salário 2": salario2,
                "Recrutador": recrutador,
                "Data de Fechamento": ""  # inicialmente vazio
            })
            st.session_state.vaga_id += 1  # incrementa o ID
            st.success("✅ Vaga cadastrada com sucesso!")

# Mostrar vagas cadastradas
if st.session_state.vagas:
    st.subheader("📄 Vagas Cadastradas")

    # 🔽 Filtro de status
    filtro_status = st.selectbox(
        "Filtrar por status:",
        ["Todas", "Aberta", "Fechada", "Em andamento"]
    )

    # Aplicar filtro
    if filtro_status != "Todas":
        vagas_filtradas = [v for v in st.session_state.vagas if v["Status"] == filtro_status]
    else:
        vagas_filtradas = st.session_state.vagas

    if vagas_filtradas:
        # Cabeçalho da "tabela"
        header_cols = st.columns([1, 2, 2, 2, 2, 2, 2, 2, 1])
        headers = ["ID", "Status", "Abertura", "Cliente", "Cargo", "Salário 1", "Salário 2", "Fechamento", "🗑️"]
        for col, h in zip(header_cols, headers):
            col.markdown(f"**{h}**")

        # Linhas da "tabela"
        for i, vaga in enumerate(vagas_filtradas):
            cols = st.columns([1, 2, 2, 2, 2, 2, 2, 2, 1])
            cols[0].write(vaga["ID"])
            
            # 🔽 Selectbox para alterar status
            novo_status = cols[1].selectbox(
                "",
                ["Aberta", "Fechada", "Em andamento"],
                index=["Aberta", "Fechada", "Em andamento"].index(vaga["Status"]),
                key=f"status_{vaga['ID']}"
            )
            if novo_status != vaga["Status"]:
                # Atualiza status na lista principal
                for v in st.session_state.vagas:
                    if v["ID"] == vaga["ID"]:
                        v["Status"] = novo_status
                        if novo_status == "Fechada":
                            v["Data de Fechamento"] = date.today().strftime("%d/%m/%Y")
                        else:
                            v["Data de Fechamento"] = ""

            cols[2].write(vaga["Data de Abertura"])
            cols[3].write(vaga["Cliente"])
            cols[4].write(vaga["Cargo"])
            cols[5].write(f"R$ {vaga['Salário 1']:.2f}")
            cols[6].write(f"R$ {vaga['Salário 2']:.2f}")
            cols[7].write(vaga["Data de Fechamento"] if vaga["Data de Fechamento"] else "-")
            if cols[8].button("🗑️", key=f"del_{vaga['ID']}"):
                st.session_state.vagas = [v for v in st.session_state.vagas if v["ID"] != vaga["ID"]]
                st.experimental_rerun()

        # Exportar CSV (mantendo formato da data e status atualizado)
        df = pd.DataFrame(vagas_filtradas)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📁 Exportar para CSV", csv, "vagas.csv", "text/csv")
    else:
        st.info(f"Nenhuma vaga encontrada com status **{filtro_status}**.")
else:
    st.info("Nenhuma vaga cadastrada ainda.")
