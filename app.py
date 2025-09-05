import streamlit as st
import pandas as pd
from datetime import date
import os

# ==============================
# Configuração inicial da página
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
# Inicialização do estado
# ==============================
if "page" not in st.session_state:
    st.session_state.page = "menu"
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = None
if "edit_record" not in st.session_state:
    st.session_state.edit_record = {}
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = {"df_name": None, "row_id": None}

# Definição das colunas
CLIENTES_COLS = ["ID", "Data", "Cliente", "Nome", "Cidade", "UF", "Telefone", "E-mail"]
VAGAS_COLS = [
    "ID",
    "ClienteID",
    "Status",
    "Data de Abertura",
    "Cargo",
    "Salário 1",
    "Salário 2",
    "Recrutador",
    "Data de Fechamento",
]
CANDIDATOS_COLS = [
    "ID",
    "VagaID",
    "Status",
    "Nome",
    "Telefone",
    "Recrutador",
]

# Carregar CSVs locais
if "clientes_df" not in st.session_state:
    st.session_state.clientes_df = load_csv(CLIENTES_CSV, CLIENTES_COLS)
if "vagas_df" not in st.session_state:
    st.session_state.vagas_df = load_csv(VAGAS_CSV, VAGAS_COLS)
if "candidatos_df" not in st.session_state:
    st.session_state.candidatos_df = load_csv(CANDIDATOS_CSV, CANDIDATOS_COLS)

# ==============================
# Garantir integridade referencial
# ==============================
# Remover vagas com Cliente inexistente
clientes_ids = set(st.session_state.clientes_df["ID"])
st.session_state.vagas_df = st.session_state.vagas_df[
    st.session_state.vagas_df["ClienteID"].isin(clientes_ids)
]

# Remover candidatos com Vaga inexistente
vagas_ids = set(st.session_state.vagas_df["ID"])
st.session_state.candidatos_df = st.session_state.candidatos_df[
    st.session_state.candidatos_df["VagaID"].isin(vagas_ids)
]

# ==============================
# Carregar lista de Cargos (do GitHub)
# ==============================
CARGOS_URL = "https://raw.githubusercontent.com/parmaconsultoriadb-ui/cadastro-de-vagas/refs/heads/main/cargos.csv.csv"

try:
    cargos_df = pd.read_csv(CARGOS_URL, dtype=str)
    LISTA_CARGOS = cargos_df.iloc[:, 0].dropna().unique().tolist()
except Exception as e:
    st.warning(f"⚠️ Não foi possível carregar os cargos do GitHub: {e}")
    LISTA_CARGOS = []

# ==============================
# Estilo
# ==============================
st.markdown(
    """
    <style>
    div.stButton > button {
        background-color: royalblue !important;
        color: white !important;
        border-radius: 8px;
        height: 2.5em;
        font-size: 15px;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #27408B !important;
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================
# Funções auxiliares
# ==============================
def show_edit_form(df_name, cols, csv_path):
    record = st.session_state.edit_record
    with st.form("edit_form", enter_to_submit=False):
        new_data = {}
        for c in cols:
            if c == "ID":
                new_data[c] = st.text_input(c, value=record[c], disabled=True)
            elif c == "Status" and df_name == "candidatos_df":
                opcoes_candidatos = ["Enviado", "Não entrevistado", "Validado", "Não validado", "Desistência"]
                new_data[c] = st.selectbox(
                    c,
                    options=opcoes_candidatos,
                    index=opcoes_candidatos.index(record[c]) if record[c] in opcoes_candidatos else 0,
                )
            elif c == "Status" and df_name == "vagas_df":
                opcoes_vagas = ["Aberta", "Ag. Inicio", "Cancelada", "Fechada", "Reaberta", "Pausada"]
                new_data[c] = st.selectbox(
                    c,
                    options=opcoes_vagas,
                    index=opcoes_vagas.index(record[c]) if record[c] in opcoes_vagas else 0,
                )
            else:
                new_data[c] = st.text_input(c, value=record[c])

        submitted = st.form_submit_button("Salvar Alterações", use_container_width=True)
        if submitted:
            df = st.session_state[df_name]
            idx = df[df["ID"] == record["ID"]].index
            if not idx.empty:
                for c in cols:
                    df.loc[idx, c] = new_data[c]
            st.session_state[df_name] = df
            save_csv(df, csv_path)

            # 🔄 Regras automáticas
            if df_name == "candidatos_df":
                vaga_id = record.get("VagaID")
                vagas_df = st.session_state.vagas_df
                idx_vaga = vagas_df[vagas_df["ID"] == vaga_id].index
                if not idx_vaga.empty:
                    if new_data.get("Status") == "Validado":
                        vagas_df.loc[idx_vaga, "Status"] = "Ag. Inicio"
                        st.success("🔄 Vaga atualizada para 'Ag. Inicio'!")
                    elif record.get("Status") == "Validado" and new_data.get("Status") != "Validado":
                        vagas_df.loc[idx_vaga, "Status"] = "Aberta"
                        st.info("🔄 Vaga reaberta automaticamente!")
                    st.session_state.vagas_df = vagas_df
                    save_csv(vagas_df, VAGAS_CSV)

            st.success("✅ Registro atualizado com sucesso!")
            st.session_state.edit_mode = None
            st.session_state.edit_record = {}
            st.rerun()

    if st.button("❌ Cancelar Edição", use_container_width=True):
        st.session_state.edit_mode = None
        st.session_state.edit_record = {}
        st.rerun()

def show_table(df, cols, df_name, csv_path):
    cols_ui = st.columns(len(cols) + 2)
    for i, c in enumerate(cols):
        cols_ui[i].markdown(
            f"<div style='background-color:#f0f0f0; padding:6px; font-weight:bold; color:black; border-radius:4px; text-align:center;'>{c}</div>",
            unsafe_allow_html=True,
        )
    cols_ui[-2].markdown("<div style='background-color:#f0f0f0; padding:6px; font-weight:bold; color:black; border-radius:4px; text-align:center;'>Editar</div>", unsafe_allow_html=True)
    cols_ui[-1].markdown("<div style='background-color:#f0f0f0; padding:6px; font-weight:bold; color:black; border-radius:4px; text-align:center;'>Excluir</div>", unsafe_allow_html=True)

    for idx, row in df.iterrows():
        bg_color = "#ffffff" if idx % 2 == 0 else "#f9f9f9"
        cols_ui = st.columns(len(cols) + 2)
        for i, c in enumerate(cols):
            cols_ui[i].markdown(f"<div style='background-color:{bg_color}; padding:6px; text-align:center; color:black;'>{row[c]}</div>", unsafe_allow_html=True)

        with cols_ui[-2]:
            if st.button("Editar", key=f"edit_{df_name}_{row['ID']}", use_container_width=True):
                st.session_state.edit_mode = df_name
                st.session_state.edit_record = row.to_dict()
                st.rerun()
        with cols_ui[-1]:
            if st.button("Excluir", key=f"del_{df_name}_{row['ID']}", use_container_width=True):
                st.session_state.confirm_delete = {"df_name": df_name, "row_id": row["ID"]}
                st.rerun()

    # Confirmação e exclusão com integridade
    if st.session_state.confirm_delete["df_name"] == df_name:
        row_id = st.session_state.confirm_delete["row_id"]
        st.warning(f"Deseja realmente excluir o registro **ID {row_id}**?")
        col_spacer1, col1, col2, col_spacer2 = st.columns([2, 1, 1, 2])
        with col1:
            if st.button("✅ Sim, quero excluir", key=f"confirm_{df_name}_{row_id}"):
                df2 = df[df["ID"] != row_id]
                st.session_state[df_name] = df2
                save_csv(df2, csv_path)

                # 🔗 Cascata
                if df_name == "clientes_df":
                    vagas_ids = st.session_state.vagas_df.loc[
                        st.session_state.vagas_df["ClienteID"] == row_id, "ID"
                    ].tolist()
                    st.session_state.vagas_df = st.session_state.vagas_df[
                        st.session_state.vagas_df["ClienteID"] != row_id
                    ]
                    st.session_state.candidatos_df = st.session_state.candidatos_df[
                        ~st.session_state.candidatos_df["VagaID"].isin(vagas_ids)
                    ]
                    save_csv(st.session_state.vagas_df, VAGAS_CSV)
                    save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)

                elif df_name == "vagas_df":
                    st.session_state.candidatos_df = st.session_state.candidatos_df[
                        st.session_state.candidatos_df["VagaID"] != row_id
                    ]
                    save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)

                st.success(f"Registro {row_id} excluído com sucesso!")
                st.session_state.confirm_delete = {"df_name": None, "row_id": None}
                st.rerun()
        with col2:
            if st.button("❌ Cancelar", key=f"cancel_{df_name}_{row_id}"):
                st.session_state.confirm_delete = {"df_name": None, "row_id": None}
                st.rerun()

    st.divider()

def download_button(df, filename, label="⬇️ Baixar CSV"):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv, file_name=filename, mime="text/csv", use_container_width=True)

# ==============================
# Telas
# ==============================
def tela_clientes():
    if st.session_state.edit_mode == "clientes_df":
        st.markdown("### ✏️ Editar Cliente")
        show_edit_form("clientes_df", CLIENTES_COLS, CLIENTES_CSV)
        return

    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()

    st.header("👥 Cadastro de Clientes")
    data_hoje = date.today().strftime("%d/%m/%Y")

    with st.form("form_clientes", enter_to_submit=False):
        nome = st.text_input("Nome *")
        cliente = st.text_input("Cliente *")
        cidade = st.text_input("Cidade *")
        uf = st.text_input("UF *", max_chars=2)
        telefone = st.text_input("Telefone *")
        email = st.text_input("E-mail *")

        submitted = st.form_submit_button("Cadastrar Cliente", use_container_width=True)
        if submitted:
            if not all([nome, cliente, cidade, uf, telefone, email]):
                st.warning("⚠️ Preencha todos os campos obrigatórios.")
            else:
                prox_id = next_id(st.session_state.clientes_df, "ID")
                novo = pd.DataFrame(
                    [{
                        "ID": str(prox_id),
                        "Data": data_hoje,
                        "Cliente": cliente,
                        "Nome": nome,
                        "Cidade": cidade,
                        "UF": uf.upper(),
                        "Telefone": telefone,
                        "E-mail": email,
                    }]
                )
                st.session_state.clientes_df = pd.concat([st.session_state.clientes_df, novo], ignore_index=True)
                save_csv(st.session_state.clientes_df, CLIENTES_CSV)
                st.success(f"✅ Cliente cadastrado com sucesso! ID: {prox_id}")
                st.rerun()

    st.subheader("📄 Clientes Cadastrados")
    df = st.session_state.clientes_df
    if df.empty:
        st.info("Nenhum cliente cadastrado.")
    else:
        filtro = st.text_input("🔎 Buscar por Cliente")
        df_filtrado = df[df["Cliente"].str.contains(filtro, case=False, na=False)] if filtro else df
        download_button(df_filtrado, "clientes.csv", "⬇️ Baixar Clientes")
        show_table(df_filtrado, CLIENTES_COLS, "clientes_df", CLIENTES_CSV)

def tela_vagas():
    if st.session_state.edit_mode == "vagas_df":
        st.markdown("### ✏️ Editar Vaga")
        show_edit_form("vagas_df", VAGAS_COLS, VAGAS_CSV)
        return

    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()

    st.header("📋 Cadastro de Vagas")
    data_abertura = date.today().strftime("%d/%m/%Y")

    with st.form("form_vaga", enter_to_submit=False):
        clientes = st.session_state.clientes_df
        if clientes.empty:
            st.warning("⚠️ Cadastre um Cliente antes de cadastrar Vagas.")
            return
        cliente_sel = st.selectbox("Cliente *", options=clientes.apply(lambda x: f"{x['ID']} - {x['Cliente']}", axis=1))
        cliente_id = cliente_sel.split(" - ")[0]

        cargo = st.selectbox(
            "Cargo *",
            options=[""] + LISTA_CARGOS,
            index=0,
            placeholder="Digite ou selecione um cargo"
        )

        salario1 = st.text_input("Salário 1 (R$)")
        salario2 = st.text_input("Salário 2 (R$)")
        recrutador = st.text_input("Recrutador *")

        submitted = st.form_submit_button("Cadastrar Vaga", use_container_width=True)
        if submitted:
            if not cargo or not recrutador:
                st.warning("⚠️ Preencha todos os campos obrigatórios.")
            else:
                prox_id = next_id(st.session_state.vagas_df, "ID")
                nova = pd.DataFrame([{
                    "ID": str(prox_id),
                    "ClienteID": cliente_id,
                    "Status": "Aberta",
                    "Data de Abertura": data_abertura,
                    "Cargo": cargo,
                    "Salário 1": salario1,
                    "Salário 2": salario2,
                    "Recrutador": recrutador,
                    "Data de Fechamento": "",
                }])
                st.session_state.vagas_df = pd.concat([st.session_state.vagas_df, nova], ignore_index=True)
                save_csv(st.session_state.vagas_df, VAGAS_CSV)
                st.success(f"✅ Vaga cadastrada com sucesso! ID: {prox_id}")
                st.rerun()

    st.subheader("📄 Vagas Cadastradas")
    df = st.session_state.vagas_df
    if df.empty:
        st.info("Nenhuma vaga cadastrada.")
    else:
        clientes_map = st.session_state.clientes_df.set_index("ID")["Cliente"].to_dict()
        df["Cliente"] = df["ClienteID"].map(lambda cid: clientes_map.get(cid, "Cliente não encontrado"))
        cols_show = ["ID", "Cliente", "Status", "Data de Abertura", "Cargo", "Salário 1", "Salário 2", "Recrutador", "Data de Fechamento"]
        download_button(df[cols_show], "vagas.csv", "⬇️ Baixar Vagas")
        show_table(df, cols_show, "vagas_df", VAGAS_CSV)

def tela_candidatos():
    if st.session_state.edit_mode == "candidatos_df":
        st.markdown("### ✏️ Editar Candidato")
        show_edit_form("candidatos_df", CANDIDATOS_COLS, CANDIDATOS_CSV)
        return

    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()

    st.header("🧑‍💼 Cadastro de Candidatos")

    vagas = st.session_state.vagas_df
    vagas_abertas = vagas[vagas["Status"] == "Aberta"]

    clientes = st.session_state.clientes_df.set_index("ID")

    with st.form("form_candidatos", enter_to_submit=False):
        if vagas_abertas.empty:
            st.warning("⚠️ Não há vagas abertas disponíveis.")
            return
        vagas_opts = vagas_abertas.apply(
            lambda x: f"{x['ID']} - {clientes.loc[x['ClienteID'], 'Cliente']} - {x['Cargo']}",
            axis=1,
        )
        vaga_sel = st.selectbox("Vaga *", options=vagas_opts)
        vaga_id = vaga_sel.split(" - ")[0]

        nome = st.text_input("Nome *")
        telefone = st.text_input("Telefone *")
        recrutador = st.text_input("Recrutador *")

        submitted = st.form_submit_button("Cadastrar Candidato", use_container_width=True)
        if submitted:
            if not nome or not telefone or not recrutador:
                st.warning("⚠️ Preencha todos os campos obrigatórios.")
            else:
                prox_id = next_id(st.session_state.candidatos_df, "ID")
                novo = pd.DataFrame([{
                    "ID": str(prox_id),
                    "VagaID": vaga_id,
                    "Status": "Enviado",
                    "Nome": nome,
                    "Telefone": telefone,
                    "Recrutador": recrutador,
                }])
                st.session_state.candidatos_df = pd.concat([st.session_state.candidatos_df, novo], ignore_index=True)
                save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)
                st.success(f"✅ Candidato cadastrado com sucesso! ID: {prox_id}")
                st.rerun()

    st.subheader("📄 Candidatos Cadastrados")
    df = st.session_state.candidatos_df
    if df.empty:
        st.info("Nenhum candidato cadastrado.")
    else:
        vagas_map = vagas.set_index("ID")[["Cargo", "ClienteID"]].to_dict("index")
        df["Vaga (Cliente - Cargo)"] = df["VagaID"].map(
            lambda vid: f"{clientes.loc[vagas_map[vid]['ClienteID'], 'Cliente']} - {vagas_map[vid]['Cargo']}"
            if vid in vagas_map else "Vaga não encontrada"
        )
        cols_show = ["ID", "Vaga (Cliente - Cargo)", "Status", "Nome", "Telefone", "Recrutador"]
        download_button(df[cols_show], "candidatos.csv", "⬇️ Baixar Candidatos")
        show_table(df, cols_show, "candidatos_df", CANDIDATOS_CSV)

# ==============================
# Menu principal
# ==============================
def tela_menu():
    st.title("📊 Sistema Parma Consultoria")
    st.subheader("Escolha uma opção:")
    st.divider()
    if st.button("👥 Clientes", use_container_width=True):
        st.session_state.page = "clientes"
        st.rerun()
    if st.button("📋 Vagas", use_container_width=True):
        st.session_state.page = "vagas"
        st.rerun()
    if st.button("🧑‍💼 Candidatos", use_container_width=True):
        st.session_state.page = "candidatos"
        st.rerun()

# ==============================
# Roteamento
# ==============================
if st.session_state.page == "menu":
    tela_menu()
elif st.session_state.page == "clientes":
    tela_clientes()
elif st.session_state.page == "vagas":
    tela_vagas()
elif st.session_state.page == "candidatos":
    tela_candidatos()
