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
            # Garante colunas esperadas
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            # Reordena
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
CLIENTES_COLS = ["ID", "Data", "Cliente", "Cidade", "UF", "Telefone", "E-mail"]
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
# Função: Tela de Cadastro de Clientes
# ==============================
def tela_clientes():
    # Botão voltar
    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()

    st.markdown("<h1 style='font-size:36px;'>👥 Cadastro de Clientes</h1>", unsafe_allow_html=True)

    # Próximo ID
    prox_id = next_id(st.session_state.clientes_df, "ID")

    with st.form("form_clientes", enter_to_submit=False):
        col_id, col_data = st.columns([1, 2])
        with col_id:
            st.text_input("ID (gerado automaticamente)", value=str(prox_id), disabled=True)
        with col_data:
            data_hoje = date.today().strftime("%d/%m/%Y")
            st.text_input("Data", value=data_hoje, disabled=True)

        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("Cliente *")
            cidade = st.text_input("Cidade *")
            uf = st.text_input("UF *", max_chars=2)
        with col2:
            telefone = st.text_input("Telefone *")
            email = st.text_input("E-mail *")

        c1, c2 = st.columns(2)
        with c1:
            submitted = st.form_submit_button("Cadastrar Cliente", use_container_width=True)
        with c2:
            limpar = st.form_submit_button("Limpar Formulário", use_container_width=True)

        if limpar:
            st.rerun()

        if submitted:
            # Valida obrigatórios
            if not all([cliente.strip(), cidade.strip(), uf.strip(), telefone.strip(), email.strip()]):
                st.warning("⚠️ Preencha todos os campos obrigatórios.")
            else:
                novo = pd.DataFrame([{
                    "ID": str(prox_id),
                    "Data": data_hoje,
                    "Cliente": cliente.strip(),
                    "Cidade": cidade.strip(),
                    "UF": uf.strip().upper(),
                    "Telefone": telefone.strip(),
                    "E-mail": email.strip()
                }])
                st.session_state.clientes_df = pd.concat([st.session_state.clientes_df, novo], ignore_index=True)
                save_csv(st.session_state.clientes_df, CLIENTES_CSV)
                st.success("✅ Cliente cadastrado com sucesso!")
                st.rerun()

    # Lista de Clientes (sempre visível)
    st.markdown("<h2 style='font-size:28px;'>📄 Clientes Cadastrados</h2>", unsafe_allow_html=True)

    if st.session_state.clientes_df.empty:
        st.info("Nenhum cliente cadastrado ainda.")
    else:
        # Filtro
        colf1, colf2 = st.columns([2, 1])
        with colf1:
            busca = st.text_input("Buscar por Cliente/Cidade/UF/E-mail:")
        with colf2:
            st.download_button(
                "📁 Exportar CSV",
                st.session_state.clientes_df.to_csv(index=False).encode("utf-8"),
                "clientes.csv",
                "text/csv",
                use_container_width=True
            )

        df = st.session_state.clientes_df.copy()
        if busca:
            b = busca.lower()
            mask = (
                df["Cliente"].str.lower().str.contains(b, na=False) |
                df["Cidade"].str.lower().str.contains(b, na=False) |
                df["UF"].str.lower().str.contains(b, na=False) |
                df["E-mail"].str.lower().str.contains(b, na=False)
            )
            df = df[mask]

        # Cabeçalho
        header_cols = st.columns([1, 2, 3, 2, 1, 2, 2, 1])
        headers = ["ID", "Data", "Cliente", "Cidade", "UF", "Telefone", "E-mail", "🗑️"]
        for col, h in zip(header_cols, headers):
            col.markdown(f"<b style='font-size:16px;'>{h}</b>", unsafe_allow_html=True)

        for _, row in df.iterrows():
            cols = st.columns([1, 2, 3, 2, 1, 2, 2, 1])
            cols[0].write(f"**{row['ID']}**")
            cols[1].write(row["Data"])
            cols[2].write(row["Cliente"])
            cols[3].write(row["Cidade"])
            cols[4].write(row["UF"])
            cols[5].write(row["Telefone"])
            cols[6].write(row["E-mail"])
            if cols[7].button("🗑️", key=f"del_cli_{row['ID']}"):
                st.session_state.clientes_df = st.session_state.clientes_df[st.session_state.clientes_df["ID"] != row["ID"]]
                save_csv(st.session_state.clientes_df, CLIENTES_CSV)
                st.rerun()

# ==============================
# Função: Tela de Cadastro de Vagas
# ==============================
def tela_vagas():
    # Botão para voltar ao menu
    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()

    st.markdown("<h1 style='font-size:36px;'>📋 Cadastro de Vagas</h1>", unsafe_allow_html=True)

    # Próximo ID
    prox_id = next_id(st.session_state.vagas_df, "ID")

    with st.form("form_vaga", enter_to_submit=False):
        st.write("**Status:** Aberta")
        status = "Aberta"

        data_abertura = date.today().strftime("%d/%m/%Y")  # travada no dia atual
        st.text_input("Data de Abertura", value=data_abertura, disabled=True)

        cliente = st.text_input("Cliente")
        cargo = st.text_input("Cargo")
        salario1 = st.number_input("Salário 1 (mínimo)", step=100.0, format="%.2f", value=0.0)
        salario2 = st.number_input("Salário 2 (máximo)", step=100.0, format="%.2f", value=0.0)
        recrutador = st.text_input("Recrutador")

        c1, c2 = st.columns(2)
        with c1:
            submitted = st.form_submit_button("Cadastrar Vaga", use_container_width=True)
        with c2:
            limpar = st.form_submit_button("Limpar Formulário", use_container_width=True)

        if limpar:
            st.rerun()

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
                nova = pd.DataFrame([{
                    "ID": str(prox_id),
                    "Status": status,
                    "Data de Abertura": data_abertura,
                    "Cliente": cliente,
                    "Cargo": cargo,
                    "Salário 1": f"{float(salario1):.2f}",
                    "Salário 2": f"{float(salario2):.2f}",
                    "Recrutador": recrutador,
                    "Data de Fechamento": ""
                }])
                st.session_state.vagas_df = pd.concat([st.session_state.vagas_df, nova], ignore_index=True)
                save_csv(st.session_state.vagas_df, VAGAS_CSV)
                st.success("✅ Vaga cadastrada com sucesso!")
                st.rerun()

    # Lista de Vagas (sempre visível)
    st.markdown("<h2 style='font-size:28px;'>📄 Vagas Cadastradas</h2>", unsafe_allow_html=True)

    if st.session_state.vagas_df.empty:
        st.info("Nenhuma vaga cadastrada ainda.")
    else:
        filtro_col1, filtro_col2 = st.columns([1, 2])
        with filtro_col1:
            filtro_status = st.selectbox("Filtrar por status:", ["Todas", "Aberta", "Fechada", "Em andamento"])
        with filtro_col2:
            filtro_cliente = st.text_input("Buscar por Cliente:")

        df = st.session_state.vagas_df.copy()

        if filtro_status != "Todas":
            df = df[df["Status"] == filtro_status]
        if filtro_cliente:
            df = df[df["Cliente"].str.lower().str.contains(filtro_cliente.lower(), na=False)]

        # Cabeçalho
        header_cols = st.columns([1, 3, 3, 4, 4, 2, 2, 2, 1])
        headers = ["ID", "Status", "Abertura", "Cliente", "Cargo", "Salário 1", "Salário 2", "Fechamento", "🗑️"]
        for col, h in zip(header_cols, headers):
            col.markdown(f"<b style='font-size:16px;'>{h}</b>", unsafe_allow_html=True)

        for idx, row in df.iterrows():
            cols = st.columns([1, 3, 3, 4, 4, 2, 2, 2, 1])
            cols[0].write(f"**{row['ID']}**")

            # Status editável
            novo_status = cols[1].selectbox(
                "",
                ["Aberta", "Fechada", "Em andamento"],
                index=["Aberta", "Fechada", "Em andamento"].index(row["Status"]) if row["Status"] in ["Aberta", "Fechada", "Em andamento"] else 0,
                key=f"status_{row['ID']}"
            )
            if novo_status != row["Status"]:
                # Atualiza na base principal
                st.session_state.vagas_df.loc[st.session_state.vagas_df["ID"] == row["ID"], "Status"] = novo_status
                st.session_state.vagas_df.loc[st.session_state.vagas_df["ID"] == row["ID"], "Data de Fechamento"] = \
                    date.today().strftime("%d/%m/%Y") if novo_status == "Fechada" else ""
                save_csv(st.session_state.vagas_df, VAGAS_CSV)
                st.rerun()

            cols[2].write(row["Data de Abertura"])
            cols[3].write(row["Cliente"])
            cols[4].write(row["Cargo"])

            # Formata salário
            def fmt(x):
                try:
                    return f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except Exception:
                    return x

            cols[5].write(fmt(row["Salário 1"]))
            cols[6].write(fmt(row["Salário 2"]))
            cols[7].write(row["Data de Fechamento"] if str(row["Data de Fechamento"]).strip() else "-")

            if cols[8].button("🗑️", key=f"del_vaga_{row['ID']}"):
                st.session_state.vagas_df = st.session_state.vagas_df[st.session_state.vagas_df["ID"] != row["ID"]]
                save_csv(st.session_state.vagas_df, VAGAS_CSV)
                st.rerun()

        # Download CSV (após filtros aplicados)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📁 Exportar para CSV", csv, "vagas.csv", "text/csv", use_container_width=True)

# ==============================
# Função: Tela de Cadastro de Candidatos
# ==============================
def tela_candidatos():
    # Botão voltar
    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()

    st.markdown("<h1 style='font-size:36px;'>🧑‍💼 Cadastro de Candidatos</h1>", unsafe_allow_html=True)

    # Checa se há clientes cadastrados
    if st.session_state.clientes_df.empty:
        st.warning("⚠️ Cadastre ao menos um Cliente antes de cadastrar Candidatos.")
        if st.button("Ir para Cadastro de Clientes", use_container_width=True):
            st.session_state.page = "clientes"
            st.rerun()
        return

    # Próximo ID
    prox_id = next_id(st.session_state.candidatos_df, "ID")

    with st.form("form_candidatos", enter_to_submit=False):
        # Cliente a partir da base
        lista_clientes = st.session_state.clientes_df["Cliente"].dropna().unique().tolist()
        cliente_sel = st.selectbox("Cliente *", options=lista_clientes)

        col1, col2 = st.columns(2)
        with col1:
            cargo = st.text_input("Cargo *")
            nome = st.text_input("Nome *")
        with col2:
            telefone = st.text_input("Telefone *")
            recrutador = st.text_input("Recrutador *")

        c1, c2 = st.columns(2)
        with c1:
            submitted = st.form_submit_button("Cadastrar Candidato", use_container_width=True)
        with c2:
            limpar = st.form_submit_button("Limpar Formulário", use_container_width=True)

        if limpar:
            st.rerun()

        if submitted:
            if not all([cliente_sel.strip(), cargo.strip(), nome.strip(), telefone.strip(), recrutador.strip()]):
                st.warning("⚠️ Preencha todos os campos obrigatórios.")
            else:
                novo = pd.DataFrame([{
                    "ID": str(prox_id),
                    "Cliente": cliente_sel.strip(),
                    "Cargo": cargo.strip(),
                    "Nome": nome.strip(),
                    "Telefone": telefone.strip(),
                    "Recrutador": recrutador.strip()
                }])
                st.session_state.candidatos_df = pd.concat([st.session_state.candidatos_df, novo], ignore_index=True)
                save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)
                st.success("✅ Candidato cadastrado com sucesso!")
                st.rerun()

    # Lista de Candidatos (sempre visível)
    st.markdown("<h2 style='font-size:28px;'>📄 Candidatos Cadastrados</h2>", unsafe_allow_html=True)

    if st.session_state.candidatos_df.empty:
        st.info("Nenhum candidato cadastrado ainda.")
    else:
        colf1, colf2 = st.columns([2, 1])
        with colf1:
            busca = st.text_input("Buscar por Cliente/Cargo/Nome/Recrutador:")
        with colf2:
            st.download_button(
                "📁 Exportar CSV",
                st.session_state.candidatos_df.to_csv(index=False).encode("utf-8"),
                "candidatos.csv",
                "text/csv",
                use_container_width=True
            )

        df = st.session_state.candidatos_df.copy()
        if busca:
            b = busca.lower()
            mask = (
                df["Cliente"].str.lower().str.contains(b, na=False) |
                df["Cargo"].str.lower().str.contains(b, na=False) |
                df["Nome"].str.lower().str.contains(b, na=False) |
                df["Recrutador"].str.lower().str.contains(b, na=False)
            )
            df = df[mask]

        # Cabeçalho
        header_cols = st.columns([1, 3, 3, 3, 2, 2, 1])
        headers = ["ID", "Cliente", "Cargo", "Nome", "Telefone", "Recrutador", "🗑️"]
        for col, h in zip(header_cols, headers):
            col.markdown(f"<b style='font-size:16px;'>{h}</b>", unsafe_allow_html=True)

        for _, row in df.iterrows():
            cols = st.columns([1, 3, 3, 3, 2, 2, 1])
            cols[0].write(f"**{row['ID']}**")
            cols[1].write(row["Cliente"])
            cols[2].write(row["Cargo"])
            cols[3].write(row["Nome"])
            cols[4].write(row["Telefone"])
            cols[5].write(row["Recrutador"])
            if cols[6].button("🗑️", key=f"del_cand_{row['ID']}"):
                st.session_state.candidatos_df = st.session_state.candidatos_df[st.session_state.candidatos_df["ID"] != row["ID"]]
                save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)
                st.rerun()

# ==============================
# Menu principal
# ==============================
if st.session_state.page == "menu":
    st.markdown("<h1 style='font-size:40px; color:royalblue;'>Parma Consultoria</h1>", unsafe_allow_html=True)
    st.write("Escolha uma das opções abaixo:")

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
