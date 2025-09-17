import streamlit as st
from streamlit_autorefresh import st_autorefresh
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
COMERCIAL_CSV = "comercial.csv"  # NOVO

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
    "Atualização",
    "Salário 1",
    "Salário 2"
]
CANDIDATOS_COLS = ["ID", "Cliente", "Cargo", "Nome", "Telefone", "Recrutador", "Status", "Data de Início"]
LOGS_COLS = ["DataHora", "Usuario", "Aba", "Acao", "ItemID", "Campo", "ValorAnterior", "ValorNovo", "Detalhe"]
COMERCIAL_COLS = ["ID", "Data", "Empresa", "Cidade", "UF", "Nome", "Contato", "E-mail", "Canal", "Status"]  # NOVO

# ==============================
# Usuários e permissões
# ==============================
USUARIOS = {
    "admin": {"senha": "Parma!123@", "permissoes": ["menu", "clientes", "vagas", "candidatos", "logs", "comercial"]},
    "andre": {"senha": "And!123@", "permissoes": ["clientes", "vagas", "candidatos", "comercial"]},
    "lorrayne": {"senha": "Lrn!123@", "permissoes": ["vagas", "candidatos"]},
    "nikole": {"senha": "Nkl!123@", "permissoes": ["vagas", "candidatos"]},
    "julia": {"senha": "Jla!123@", "permissoes": ["vagas", "candidatos"]},
    "ricardo": {"senha": "Rcd!123@", "permissoes": ["clientes", "vagas", "candidatos", "comercial"]},
}

# ==============================
# Recrutadores padrão
# ==============================
RECRUTADORES_PADRAO = ["Lorrayne", "Kaline", "Nikole", "Leila", "Julia"]

# ==============================
# Inicializar sessão
# ==============================
for key, default in [
    ("page", "login"),
    ("logged_in", False),
    ("usuario", ""),
    ("permissoes", []),
    ("edit_mode", None),
    ("edit_record", {}),
    ("confirm_delete", {"df_name": None, "row_id": None}),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ==============================
# Funções utilitárias
# ==============================
def load_csv(path, expected_cols):
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, dtype=str)
            df = df.fillna("")
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

# ==============================
# Carregamento dos DataFrames
# ==============================
if "clientes_df" not in st.session_state:
    st.session_state.clientes_df = load_csv(CLIENTES_CSV, CLIENTES_COLS)
if "vagas_df" not in st.session_state:
    st.session_state.vagas_df = load_csv(VAGAS_CSV, VAGAS_COLS)
if "candidatos_df" not in st.session_state:
    st.session_state.candidatos_df = load_csv(CANDIDATOS_CSV, CANDIDATOS_COLS)
if "comercial_df" not in st.session_state:
    st.session_state.comercial_df = load_csv(COMERCIAL_CSV, COMERCIAL_COLS)
# ==============================
# Estilo customizado
# ==============================
st.markdown(
    """
    <style>
    div.stButton > button {
        background-color: #004488 !important;
        color: white !important;
        border-radius: 8px;
        height: 2.5em;
        font-size: 14px;
        font-weight: bold;
        border: none;
    }
    div.stButton > button:hover {
        background-color: #0066AA !important;
    }
    .parma-header {
        background-color: #E0F2F7;
        padding:6px;
        font-weight:bold;
        color:#333333;
        border-radius:4px;
        text-align:center;
        font-size:13px;
        border-bottom: 1px solid #cfcfcf;
    }
    .parma-cell {
        padding:6px;
        text-align:center;
        color:#333333;
        font-size:13px;
        background-color: white;
        border: none;
    }
    .stDataFrame div[data-testid="stStyledTable"] table {
        font-size: 13px !important;
        border-collapse: collapse !important;
    }
    .stDataFrame div[data-testid="stStyledTable"] thead th {
        font-size: 13px !important;
        background-color: #f6f9fb !important;
        padding: 6px !important;
        border-bottom: 1px solid #cfcfcf !important;
        border-left: none !important;
        border-right: none !important;
    }
    .stDataFrame div[data-testid="stStyledTable"] td {
        padding: 6px !important;
        border: none !important;
    }
    hr.parma-hr {
        border: none;
        border-bottom: 1px solid #e0e0e0;
        margin: 0;
    }
    .streamlit-expanderHeader, .stMarkdown, .stText {
        font-size:13px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================
# Funções auxiliares de exibição
# ==============================
def download_button(df, filename, label="⬇️ Baixar CSV"):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv, file_name=filename, mime="text/csv", use_container_width=True)

def show_table(df, cols, df_name, csv_path):
    if df is None or df.empty:
        st.info("Nenhum registro para exibir.")
        return

    col_widths = [1] * len(cols) + [0.5, 0.5]
    header_cols = st.columns(col_widths)
    for i, c in enumerate(cols):
        header_cols[i].markdown(f"<div class='parma-header'>{c}</div>", unsafe_allow_html=True)
    header_cols[-2].markdown("<div class='parma-header'>Editar</div>", unsafe_allow_html=True)
    header_cols[-1].markdown("<div class='parma-header'>Excluir</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    for _, row in df.iterrows():
        row_cols = st.columns(col_widths)
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

    # Confirmação de exclusão
    if st.session_state.confirm_delete["df_name"] == df_name:
        row_id = st.session_state.confirm_delete["row_id"]
        st.error(f"⚠️ Deseja realmente excluir o registro **ID {row_id}**? Esta ação é irreversível.")
        col_sp1, col_yes, col_no, col_sp2 = st.columns([2, 1, 1, 2])
        with col_yes:
            if st.button("✅ Sim, excluir", key=f"confirm_{df_name}_{row_id}", use_container_width=True):
                base = st.session_state[df_name].copy()
                st.session_state[df_name] = base[base["ID"] != row_id]
                save_csv(st.session_state[df_name], csv_path)
                registrar_log(df_name.replace("_df", "").capitalize(), "Excluir", item_id=row_id, detalhe=f"Registro {row_id} excluído.")
                st.success(f"✅ Registro {row_id} excluído com sucesso!")
                st.session_state.confirm_delete = {"df_name": None, "row_id": None}
                st.rerun()
        with col_no:
            if st.button("❌ Cancelar", key=f"cancel_{df_name}_{row_id}", use_container_width=True):
                st.session_state.confirm_delete = {"df_name": None, "row_id": None}
                st.rerun()
        st.divider()
# ==============================
# Função de edição
# ==============================
def show_edit_form(df_name, cols, csv_path):
    record = st.session_state.edit_record
    usuario = st.session_state.get("usuario", "")
    st.subheader(f"✏️ Editando {df_name.replace('_df','').capitalize()}")

    with st.form("edit_form", clear_on_submit=False):
        new_data = {}
        for c in cols:
            val = record.get(c, "")
            if c == "ID":
                new_data[c] = st.text_input(c, value=val, disabled=True)
            elif c == "Status" and df_name == "comercial_df":
                opcoes = ["Prospect", "Lead Qualificado", "Reunião", "Proposta Enviada", "Negócio Fechado", "Declinado"]
                idx = opcoes.index(val) if val in opcoes else 0
                new_data[c] = st.selectbox(c, options=opcoes, index=idx)
            elif c == "Data":
                new_data[c] = st.text_input(c, value=val, disabled=True)
            else:
                new_data[c] = st.text_input(c, value=val)
        submitted = st.form_submit_button("✅ Salvar Alterações", use_container_width=True)
        if submitted:
            df = st.session_state[df_name].copy()
            idx = df[df["ID"] == record["ID"]].index
            if not idx.empty:
                idx0 = idx[0]
                for c in cols:
                    if c in df.columns and c != "Data":
                        antigo = df.at[idx0, c]
                        novo = new_data.get(c, "")
                        if str(antigo) != str(novo):
                            registrar_log(
                                aba=df_name.replace('_df','').capitalize(),
                                acao="Editar",
                                item_id=record["ID"],
                                campo=c,
                                valor_anterior=antigo,
                                valor_novo=novo,
                                detalhe=f"Registro {record['ID']} alterado"
                            )
                            df.at[idx0, c] = novo
                st.session_state[df_name] = df
                save_csv(df, csv_path)
                st.success("✅ Registro atualizado com sucesso!")
                st.session_state.edit_mode = None
                st.session_state.edit_record = {}
                st.rerun()
            else:
                st.error("❌ Registro não encontrado para edição.")
    if st.button("❌ Cancelar Edição", use_container_width=True):
        st.session_state.edit_mode = None
        st.session_state.edit_record = {}
        st.rerun()

# ==============================
# Tela: Comercial
# ==============================
def tela_comercial():
    if st.session_state.edit_mode == "comercial_df":
        show_edit_form("comercial_df", COMERCIAL_COLS, COMERCIAL_CSV)
        return
    st.header("📞 Comercial")
    st.markdown("Gerencie as oportunidades comerciais.")

    with st.expander("➕ Novo Contato Comercial", expanded=False):
        data_hoje = date.today().strftime("%d/%m/%Y")
        with st.form("form_comercial", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                empresa = st.text_input("Empresa *")
                cidade = st.text_input("Cidade")
                nome = st.text_input("Nome")
                canal = st.text_input("Canal")
            with col2:
                uf = st.text_input("UF", max_chars=2)
                contato = st.text_input("Contato")
                email = st.text_input("E-mail")
            submitted = st.form_submit_button("✅ Salvar Contato", use_container_width=True)
            if submitted:
                if not empresa:
                    st.warning("⚠️ O campo 'Empresa' é obrigatório.")
                else:
                    prox_id = str(next_id(st.session_state.comercial_df, "ID"))
                    novo = pd.DataFrame([{
                        "ID": prox_id,
                        "Data": data_hoje,
                        "Empresa": empresa,
                        "Cidade": cidade,
                        "UF": uf.upper(),
                        "Nome": nome,
                        "Contato": contato,
                        "E-mail": email,
                        "Canal": canal,
                        "Status": "Prospect",
                    }])
                    st.session_state.comercial_df = pd.concat([st.session_state.comercial_df, novo], ignore_index=True)
                    save_csv(st.session_state.comercial_df, COMERCIAL_CSV)
                    registrar_log("Comercial", "Criar", item_id=prox_id, detalhe=f"Contato comercial criado (ID {prox_id}).")
                    st.success(f"✅ Contato comercial cadastrado com sucesso! ID: {prox_id}")
                    st.rerun()

    st.subheader("📋 Contatos Comerciais")
    df = st.session_state.comercial_df.copy()
    if df.empty:
        st.info("Nenhum registro comercial encontrado.")
    else:
        filtro = st.text_input("🔎 Buscar por Empresa")
        df_filtrado = df[df["Empresa"].str.contains(filtro, case=False, na=False)] if filtro else df
        download_button(df_filtrado, "comercial.csv", "⬇️ Baixar Contatos")
        show_table(df_filtrado, COMERCIAL_COLS, "comercial_df", COMERCIAL_CSV)
# ==============================
# Tela de login
# ==============================
def tela_login():
    st.image("https://parmaconsultoria.com.br/wp-content/uploads/2023/10/logo-parma-1.png", width=250)
    st.title("🔒 Login - Parma Consultoria")
    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar", use_container_width=True)
        if submitted:
            if usuario in USUARIOS and senha == USUARIOS[usuario]["senha"]:
                st.session_state.usuario = usuario
                st.session_state.logged_in = True
                st.session_state.page = "menu"
                st.session_state.permissoes = USUARIOS[usuario]["permissoes"]
                registrar_log("Login", "Login", detalhe=f"Usuário {usuario} entrou no sistema.")
                st.success("✅ Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos.")

# ==============================
# Página inicial
# ==============================
if st.session_state.logged_in:
    st.image("https://parmaconsultoria.com.br/wp-content/uploads/2023/10/logo-parma-1.png", width=180)
    st.caption(f"Usuário: {st.session_state.usuario}")

    page_label_map = {
        "menu": "Menu Principal",
        "clientes": "Clientes",
        "vagas": "Vagas",
        "candidatos": "Candidatos",
        "comercial": "Comercial",
        "logs": "Logs do Sistema"
    }

    perms = st.session_state.get("permissoes", [])
    if "menu" not in perms:
        perms = ["menu"] + perms

    ordered_page_keys = ["menu", "clientes", "vagas", "candidatos", "comercial", "logs"]
    allowed_pages = [p for p in ordered_page_keys if p in perms]
    labels = [page_label_map[p] for p in allowed_pages]

    try:
        index_initial = allowed_pages.index(st.session_state.page)
    except Exception:
        index_initial = 0

    menu_cols = st.columns([1] * (len(labels) + 2))
    for i, label in enumerate(labels):
        if menu_cols[i].button(label, use_container_width=True):
            st.session_state.page = allowed_pages[i]
            st.rerun()
    if menu_cols[-2].button("🔄 Refresh", use_container_width=True):
        refresh_data()
        st.rerun()
    if menu_cols[-1].button("Sair", use_container_width=True):
        registrar_log("Login", "Logout", detalhe=f"Usuário {st.session_state.usuario} saiu do sistema.")
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()

    current_page = st.session_state.page
    if current_page == "menu":
        tela_menu_interno()
    elif current_page == "clientes":
        if "clientes" in perms:
            tela_clientes()
        else:
            st.warning("⚠️ Você não tem permissão para acessar esta página.")
    elif current_page == "vagas":
        if "vagas" in perms:
            tela_vagas()
        else:
            st.warning("⚠️ Você não tem permissão para acessar esta página.")
    elif current_page == "candidatos":
        if "candidatos" in perms:
            tela_candidatos()
        else:
            st.warning("⚠️ Você não tem permissão para acessar esta página.")
    elif current_page == "comercial":
        if "comercial" in perms:
            tela_comercial()
        else:
            st.warning("⚠️ Você não tem permissão para acessar esta página.")
    elif current_page == "logs":
        if "logs" in perms:
            tela_logs()
        else:
            st.warning("⚠️ Você não tem permissão para acessar esta página.")
else:
    tela_login()


