import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

# ==============================
# Configuração inicial da página
# ==============================
st.set_page_config(page_title="Parma Consultoria", layout="wide")

# ==============================
# Arquivos CSV
# ==============================
CLIENTES_CSV = "clientes.csv"
VAGAS_CSV = "vagas.csv"
CANDIDATOS_CSV = "candidatos.csv"
LOGS_CSV = "logs.csv"

# ==============================
# Colunas esperadas
# ==============================
CLIENTES_COLS = ["ID", "Data", "Cliente", "Nome", "Cidade", "UF", "Telefone", "E-mail"]
VAGAS_COLS = [
    "ID",
    "Cliente",
    "Status",
    "Data de Abertura",
    "Cargo",
    "Recrutador",
    "Data de Início",
    "Salário 1",
    "Salário 2",
    "Descrição / Observação",
]
CANDIDATOS_COLS = ["ID", "Cliente", "Cargo", "Nome", "Telefone", "Recrutador", "Status", "Data de Início"]
LOGS_COLS = ["DataHora", "Usuario", "Aba", "Acao", "ItemID", "Campo", "ValorAnterior", "ValorNovo", "Detalhe"]

# ==============================
# Usuários e permissões
# ==============================
USUARIOS = {
    "admin": {"senha": "Parma!123@", "permissoes": ["menu", "clientes", "vagas", "candidatos", "logs"]},
    "andre": {"senha": "And!123@", "permissoes": ["menu", "clientes", "vagas", "candidatos", "logs"]},
    "lorrayne": {"senha": "Lrn!123@", "permissoes": ["menu", "vagas", "candidatos"]},
}

# ==============================
# Helpers de persistência
# ==============================
def load_csv(path, expected_cols):
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, dtype=str).fillna("")
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            df = df[expected_cols]
            if "ID" in df.columns:
                df["ID"] = df["ID"].astype(str)
            return df
        except Exception:
            return pd.DataFrame(columns=expected_cols)
    else:
        return pd.DataFrame(columns=expected_cols)

def save_csv(df, path):
    df.to_csv(path, index=False, encoding="utf-8")

def next_id(df, id_col="ID"):
    if df is None or df.empty:
        return 1
    try:
        vals = pd.to_numeric(df[id_col], errors="coerce").fillna(0).astype(int)
        return int(vals.max()) + 1
    except Exception:
        return 1

# ==============================
# Logs
# ==============================
def ensure_logs_file():
    if not os.path.exists(LOGS_CSV):
        save_csv(pd.DataFrame(columns=LOGS_COLS), LOGS_CSV)

def registrar_log(aba, acao, item_id="", campo="", valor_anterior="", valor_novo="", detalhe=""):
    ensure_logs_file()
    datahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    usuario = st.session_state.get("usuario", "admin")
    log_df = pd.DataFrame([{
        "DataHora": datahora,
        "Usuario": usuario,
        "Aba": aba,
        "Acao": acao,
        "ItemID": str(item_id) if item_id is not None else "",
        "Campo": campo,
        "ValorAnterior": "" if valor_anterior is None else str(valor_anterior),
        "ValorNovo": "" if valor_novo is None else str(valor_novo),
        "Detalhe": detalhe
    }])
    if os.path.exists(LOGS_CSV):
        atual = pd.read_csv(LOGS_CSV, dtype=str).fillna("")
        log_df = pd.concat([atual, log_df], ignore_index=True)
    save_csv(log_df, LOGS_CSV)

def carregar_logs():
    ensure_logs_file()
    try:
        df = pd.read_csv(LOGS_CSV, dtype=str)
        return df.fillna("")
    except Exception:
        return pd.DataFrame(columns=LOGS_COLS)

# ==============================
# Inicialização do estado
# ==============================
if "page" not in st.session_state:
    st.session_state.page = "login"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "permissoes" not in st.session_state:
    st.session_state.permissoes = []
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = None
if "edit_record" not in st.session_state:
    st.session_state.edit_record = {}
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = {"df_name": None, "row_id": None}

if "clientes_df" not in st.session_state:
    st.session_state.clientes_df = load_csv(CLIENTES_CSV, CLIENTES_COLS)
if "vagas_df" not in st.session_state:
    st.session_state.vagas_df = load_csv(VAGAS_CSV, VAGAS_COLS)
if "candidatos_df" not in st.session_state:
    st.session_state.candidatos_df = load_csv(CANDIDATOS_CSV, CANDIDATOS_COLS)

# ==============================
# Estilo
# ==============================
st.markdown(
    """
    <style>
    /* Botões, células e headers */
    div.stButton > button { background-color: #004488 !important; color: white !important; border-radius: 8px; height: 2.5em; font-size: 14px; font-weight: bold; border: none; }
    div.stButton > button:hover { background-color: #0066AA !important; }
    .parma-header { background-color: #E0F2F7; padding:6px; font-weight:bold; color:#333; border-radius:4px; text-align:center; font-size:13px; border-bottom: 1px solid #cfcfcf; }
    .parma-cell { padding:6px; text-align:center; color:#333; font-size:13px; background-color: white; border: none; }
    hr.parma-hr { border: none; border-bottom: 1px solid #e0e0e0; margin: 0; }
    .stDataFrame div[data-testid="stStyledTable"] table { font-size: 13px !important; border-collapse: collapse !important; }
    .stDataFrame div[data-testid="stStyledTable"] thead th { font-size: 13px !important; background-color: #f6f9fb !important; padding: 6px !important; border-bottom: 1px solid #cfcfcf !important; border-left: none !important; border-right: none !important; }
    .stDataFrame div[data-testid="stStyledTable"] td { padding: 6px !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True
)

# ==============================
# UI helpers
# ==============================
def download_button(df, filename, label="⬇️ Baixar CSV"):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv, file_name=filename, mime="text/csv", use_container_width=True)

def show_table(df, cols, df_name, csv_path):
    if df is None or df.empty:
        st.info("Nenhum registro para exibir.")
        return
    header_cols = st.columns(len(cols) + 2)
    for i, c in enumerate(cols):
        header_cols[i].markdown(f"<div class='parma-header'>{c}</div>", unsafe_allow_html=True)
    header_cols[-2].markdown("<div class='parma-header'>Editar</div>", unsafe_allow_html=True)
    header_cols[-1].markdown("<div class='parma-header'>Excluir</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    for _, row in df.iterrows():
        row_cols = st.columns(len(cols) + 2)
        for i, c in enumerate(cols):
            value = row.get(c, "")
            if pd.isna(value):
                value = ""
            row_cols[i].markdown(f"<div class='parma-cell'>{value}</div>", unsafe_allow_html=True)
        with row_cols[-2]:
            if st.button("✏️", key=f"edit_{df_name}_{str(row.get('ID',''))}", use_container_width=True):
                st.session_state.edit_mode = df_name
                st.session_state.edit_record = row.to_dict()
                st.rerun()
        with row_cols[-1]:
            if st.button("🗑️", key=f"del_{df_name}_{str(row.get('ID',''))}", use_container_width=True):
                st.session_state.confirm_delete = {"df_name": df_name, "row_id": row["ID"]}
                st.rerun()
        st.markdown("<hr class='parma-hr' />", unsafe_allow_html=True)

    if st.session_state.confirm_delete["df_name"] == df_name:
        row_id = st.session_state.confirm_delete["row_id"]
        st.error(f"⚠️ Deseja realmente excluir o registro **ID {row_id}**? Esta ação é irreversível.")
        col_sp1, col_yes, col_no = st.columns([1,1,1])
        with col_yes:
            if st.button("Sim, excluir"):
                st.session_state[df_name + "_df"] = st.session_state[df_name + "_df"].loc[st.session_state[df_name + "_df"]["ID"] != row_id]
                save_csv(st.session_state[df_name + "_df"], csv_path)
                registrar_log(df_name.capitalize(), "Exclusão", item_id=row_id)
                st.session_state.confirm_delete = {"df_name": None, "row_id": None}
                st.success("Registro excluído com sucesso.")
                st.rerun()
        with col_no:
            if st.button("Cancelar"):
                st.session_state.confirm_delete = {"df_name": None, "row_id": None}
                st.rerun()

def validar_data_inicio(data_str):
    if not data_str:
        return True
    try:
        datetime.strptime(data_str, "%d/%m/%Y")
        return True
    except Exception:
        return False

# ==============================
# Login
# ==============================
def login():
    st.title("Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
            st.session_state.logged_in = True
            st.session_state.usuario = usuario
            st.session_state.permissoes = USUARIOS[usuario]["permissoes"]
            st.session_state.page = "menu"
            st.success("Login realizado com sucesso!")
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos.")

# ==============================
# Menu principal
# ==============================
def menu():
    st.title("Parma Consultoria - Menu")
    abas = st.session_state.permissoes
    aba = st.radio("Selecione a aba:", abas, horizontal=True)
    st.session_state.page = aba
    st.experimental_rerun()

# ==============================
# Clientes
# ==============================
def clientes_page():
    st.header("Clientes")
    df = st.session_state.clientes_df
    show_table(df, CLIENTES_COLS, "clientes", CLIENTES_CSV)
    st.subheader("Adicionar novo cliente")
    with st.form("add_cliente_form", clear_on_submit=True):
        novo = {c: st.text_input(c) for c in CLIENTES_COLS if c != "ID"}
        submitted = st.form_submit_button("Salvar")
        if submitted:
            novo_id = next_id(df)
            novo["ID"] = novo_id
            novo["Data"] = datetime.now().strftime("%d/%m/%Y")
            st.session_state.clientes_df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
            save_csv(st.session_state.clientes_df, CLIENTES_CSV)
            registrar_log("Clientes", "Inclusão", item_id=novo_id)
            st.success("Cliente adicionado com sucesso!")
            st.experimental_rerun()

# ==============================
# Vagas
# ==============================
def vagas_page():
    st.header("Vagas")
    df = st.session_state.vagas_df
    show_table(df, VAGAS_COLS, "vagas", VAGAS_CSV)

    if st.session_state.edit_mode == "vagas":
        st.subheader(f"Editar Vaga ID {st.session_state.edit_record['ID']}")
        record = st.session_state.edit_record
        with st.form("edit_vaga_form"):
            edited = {c: st.text_input(c, record.get(c, "")) for c in VAGAS_COLS if c != "ID"}
            submitted = st.form_submit_button("Salvar Alterações")
            if submitted:
                # Validação Data de Início
                if not validar_data_inicio(edited.get("Data de Início","")):
                    st.error("Data de Início inválida! Use formato DD/MM/YYYY.")
                else:
                    for c in edited:
                        old_val = record.get(c,"")
                        new_val = edited[c]
                        if old_val != new_val:
                            registrar_log("Vagas", "Edição", item_id=record["ID"], campo=c, valor_anterior=old_val, valor_novo=new_val)
                            st.session_state.vagas_df.loc[st.session_state.vagas_df["ID"] == record["ID"], c] = new_val
                    save_csv(st.session_state.vagas_df, VAGAS_CSV)
                    st.success("Registro atualizado com sucesso!")
                    st.session_state.edit_mode = None
                    st.session_state.edit_record = {}
                    st.experimental_rerun()

# ==============================
# Candidatos
# ==============================
def candidatos_page():
    st.header("Candidatos")
    df = st.session_state.candidatos_df
    show_table(df, CANDIDATOS_COLS, "candidatos", CANDIDATOS_CSV)

    if st.session_state.edit_mode == "candidatos":
        st.subheader(f"Editar Candidato ID {st.session_state.edit_record['ID']}")
        record = st.session_state.edit_record
        with st.form("edit_candidato_form"):
            edited = {c: st.text_input(c, record.get(c, "")) for c in CANDIDATOS_COLS if c != "ID"}
            submitted = st.form_submit_button("Salvar Alterações")
            if submitted:
                # Validação Data de Início
                if not validar_data_inicio(edited.get("Data de Início","")):
                    st.error("Data de Início inválida! Use formato DD/MM/YYYY.")
                else:
                    for c in edited:
                        old_val = record.get(c,"")
                        new_val = edited[c]
                        if old_val != new_val:
                            registrar_log("Candidatos", "Edição", item_id=record["ID"], campo=c, valor_anterior=old_val, valor_novo=new_val)
                            st.session_state.candidatos_df.loc[st.session_state.candidatos_df["ID"] == record["ID"], c] = new_val
                    save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)
                    st.success("Registro atualizado com sucesso!")
                    st.session_state.edit_mode = None
                    st.session_state.edit_record = {}
                    st.experimental_rerun()

# ==============================
# Logs
# ==============================
def logs_page():
    st.header("Logs")
    df = carregar_logs()
    if df.empty:
        st.info("Nenhum log disponível.")
    else:
        st.dataframe(df)

# ==============================
# Roteamento
# ==============================
if not st.session_state.logged_in:
    login()
else:
    page = st.session_state.page
    if page == "menu":
        menu()
    elif page == "clientes":
        clientes_page()
    elif page == "vagas":
        vagas_page()
    elif page == "candidatos":
        candidatos_page()
    elif page == "logs":
        logs_page()
