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
    "Atualização",
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
# Recrutadores padrão
# ==============================
RECRUTADORES_PADRAO = ["Lorrayne", "Kaline", "Nikole", "Leila", "Julia"]

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

def carregar_logs():
    ensure_logs_file()
    try:
        df = pd.read_csv(LOGS_CSV, dtype=str)
        return df.fillna("")
    except Exception:
        return pd.DataFrame(columns=LOGS_COLS)

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

for df_key, csv_path, cols in [
    ("clientes_df", CLIENTES_CSV, CLIENTES_COLS),
    ("vagas_df", VAGAS_CSV, VAGAS_COLS),
    ("candidatos_df", CANDIDATOS_CSV, CANDIDATOS_COLS),
]:
    if df_key not in st.session_state:
        st.session_state[df_key] = load_csv(csv_path, cols)

st.markdown(
    """
    <style>
    :root {
        --parma-blue-dark: #004488;
        --parma-blue-medium: #0066AA;
        --parma-blue-light: #E0F2F7;
        --parma-text-dark: #333333;
    }
    div.stButton > button {
        background-color: var(--parma-blue-dark) !important;
        color: white !important;
        border-radius: 8px;
        height: 2.5em;
        font-size: 14px;
        font-weight: bold;
        border: none;
    }
    div.stButton > button:hover {
        background-color: var(--parma-blue-medium) !important;
    }
    .parma-header {
        background-color: var(--parma-blue-light);
        padding:6px;
        font-weight:bold;
        color:var(--parma-text-dark);
        border-radius:4px;
        text-align:center;
        font-size:13px;
        border-bottom: 1px solid #cfcfcf;
    }
    .parma-cell {
        padding:6px;
        text-align:center;
        color:var(--parma-text-dark);
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

    if st.session_state.confirm_delete["df_name"] == df_name:
        row_id = st.session_state.confirm_delete["row_id"]
        st.error(f"⚠️ Deseja realmente excluir o registro **ID {row_id}**? Esta ação é irreversível.")
        col_sp1, col_yes, col_no, col_sp2 = st.columns([2, 1, 1, 2])
        with col_yes:
            if st.button("✅ Sim, excluir", key=f"confirm_{df_name}_{row_id}", use_container_width=True):
                if df_name == "clientes_df":
                    base = st.session_state.clientes_df.copy()
                    cliente_row = base[base["ID"] == row_id]
                    cliente_nome = cliente_row.iloc[0]["Cliente"] if not cliente_row.empty else None
                    st.session_state.clientes_df = base[base["ID"] != row_id]
                    save_csv(st.session_state.clientes_df, CLIENTES_CSV)
                    vagas_rel = st.session_state.vagas_df[st.session_state.vagas_df["Cliente"] == cliente_nome]["ID"].tolist() if cliente_nome else []
                    st.session_state.vagas_df = st.session_state.vagas_df[st.session_state.vagas_df["Cliente"] != cliente_nome]
                    save_csv(st.session_state.vagas_df, VAGAS_CSV)
                    st.session_state.candidatos_df = st.session_state.candidatos_df[st.session_state.candidatos_df["Cliente"] != cliente_nome]
                    save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)
                    registrar_log("Clientes", "Excluir", item_id=row_id, detalhe=f"Cliente {row_id} excluído. Vagas removidas: {vagas_rel}")
                    registrar_log("Vagas", "Excluir em Cascata", detalhe=f"Cliente {row_id} excluído. Vagas removidas: {vagas_rel}")
                    registrar_log("Candidatos", "Excluir em Cascata", detalhe=f"Cliente {row_id} excluído. Candidatos removidos.")
                elif df_name == "vagas_df":
                    base = st.session_state.vagas_df.copy()
                    vaga_row = base[base["ID"] == row_id]
                    vaga_cliente = vaga_row.iloc[0]["Cliente"] if not vaga_row.empty else None
                    vaga_cargo = vaga_row.iloc[0]["Cargo"] if not vaga_row.empty else None
                    st.session_state.vagas_df = base[base["ID"] != row_id]
                    save_csv(st.session_state.vagas_df, VAGAS_CSV)
                    if vaga_cliente is not None and vaga_cargo is not None:
                        candidatos_rel = st.session_state.candidatos_df[(st.session_state.candidatos_df["Cliente"] == vaga_cliente) & (st.session_state.candidatos_df["Cargo"] == vaga_cargo)]["ID"].tolist()
                        st.session_state.candidatos_df = st.session_state.candidatos_df[~((st.session_state.candidatos_df["Cliente"] == vaga_cliente) & (st.session_state.candidatos_df["Cargo"] == vaga_cargo))]
                        save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)
                    else:
                        candidatos_rel = []
                    registrar_log("Vagas", "Excluir", item_id=row_id, detalhe=f"Vaga {row_id} excluída. Candidatos removidos: {candidatos_rel}")
                    registrar_log("Candidatos", "Excluir em Cascata", detalhe=f"Vaga {row_id} excluída. Candidatos removidos: {candidatos_rel}")
                elif df_name == "candidatos_df":
                    base = st.session_state.candidatos_df.copy()
                    st.session_state.candidatos_df = base[base["ID"] != row_id]
                    save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)
                    registrar_log("Candidatos", "Excluir", item_id=row_id, detalhe=f"Candidato {row_id} excluído.")
                st.success(f"✅ Registro {row_id} excluído com sucesso!")
                st.session_state.confirm_delete = {"df_name": None, "row_id": None}
                st.rerun()
        with col_no:
            if st.button("❌ Cancelar", key=f"cancel_{df_name}_{row_id}", use_container_width=True):
                st.session_state.confirm_delete = {"df_name": None, "row_id": None}
                st.rerun()
    st.divider()

def atualizar_vaga_data_atualizacao(cliente, cargo):
    vagas_df = st.session_state.vagas_df.copy()
    vaga_match = vagas_df[(vagas_df["Cliente"] == cliente) & (vagas_df["Cargo"] == cargo)]
    if not vaga_match.empty:
        idx = vaga_match.index[0]
        hoje = datetime.now().strftime("%d/%m/%Y")
        antigo = vagas_df.at[idx, "Atualização"]
        vagas_df.at[idx, "Atualização"] = hoje
        st.session_state.vagas_df = vagas_df
        save_csv(vagas_df, VAGAS_CSV)
        registrar_log("Vagas", "Atualização", item_id=vagas_df.at[idx, "ID"], campo="Atualização", valor_anterior=antigo, valor_novo=hoje, detalhe=f"Atualização de status de candidato atrelado à vaga.")

def show_edit_form(df_name, cols, csv_path):
    # [sem mudanças de lógica]
    # ... [código igual]

def tela_login():
    # [sem mudanças de lógica]
    # ... [código igual]

def tela_menu_interno():
    # [sem mudanças de lógica]
    # ... [código igual]

def tela_clientes():
    # [sem mudanças de lógica]
    # ... [código igual]

def tela_vagas():
    if st.session_state.edit_mode == "vagas_df":
        show_edit_form("vagas_df", VAGAS_COLS, VAGAS_CSV)
        return
    st.header("📋 Vagas")
    st.markdown("Gerencie as vagas de emprego da consultoria.")
    df_all = st.session_state.vagas_df.copy()
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        cliente_opts = ["(todos)"] + sorted(df_all["Cliente"].dropna().unique().tolist())
        cliente_filter = st.selectbox("Filtrar por Cliente", cliente_opts, index=0)
    if cliente_filter != "(todos)":
        cargos_do_cliente = df_all[df_all["Cliente"] == cliente_filter]["Cargo"].dropna().unique().tolist()
        cargo_opts = ["(todos)"] + sorted(cargos_do_cliente)
    else:
        cargo_opts = ["(todos)"] + sorted(df_all["Cargo"].dropna().unique().tolist())
    with col2:
        cargo_filter = st.selectbox("Filtrar por Cargo", cargo_opts, index=0)
    with col3:
        recrutador_opts = ["(todos)"] + sorted(df_all["Recrutador"].dropna().unique().tolist())
        recrutador_filter = st.selectbox("Filtrar por Recrutador", recrutador_opts, index=0)
    with col4:
        status_opts = ["(todos)"] + sorted(df_all["Status"].dropna().unique().tolist())
        status_filter = st.selectbox("Filtrar por Status", status_opts, index=0)

    df = df_all.copy()
    if cliente_filter != "(todos)":
        df = df[df["Cliente"] == cliente_filter]
    if cargo_filter != "(todos)":
        df = df[df["Cargo"] == cargo_filter]
    if recrutador_filter != "(todos)":
        df = df[df["Recrutador"] == recrutador_filter]
    if status_filter != "(todos)":
        df = df[df["Status"] == status_filter]

    if st.session_state.usuario == "admin":
        with st.expander("📤 Importar Vagas (CSV/XLSX)", expanded=False):
            arquivo = st.file_uploader("Selecione um arquivo com as colunas exatas: " + ", ".join(VAGAS_COLS), type=["csv", "xlsx"], key="upload_vagas")
            if arquivo is not None:
                try:
                    if arquivo.name.lower().endswith('.csv'):
                        df_upload = pd.read_csv(arquivo, dtype=str)
                    else:
                        df_upload = pd.read_excel(arquivo, dtype=str)
                    # Verifica se as colunas são exatamente as esperadas
                    if set(df_upload.columns) != set(VAGAS_COLS) or len(df_upload.columns) != len(VAGAS_COLS):
                        st.error(f"Colunas do arquivo devem ser **exatamente**: {VAGAS_COLS}")
                    else:
                        df_upload = df_upload[VAGAS_COLS].fillna("")
                        base = st.session_state.vagas_df.copy()
                        combined = pd.concat([base, df_upload], ignore_index=True)
                        combined = combined.drop_duplicates(subset=["ID"], keep="first")
                        st.session_state.vagas_df = combined
                        save_csv(combined, VAGAS_CSV)
                        registrar_log("Vagas", "Importar", detalhe=f"Importação de vagas via upload ({arquivo.name}).")
                        st.success("✅ Vagas importadas com sucesso!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao processar o arquivo: {e}")
    with st.expander("➕ Cadastrar Nova Vaga", expanded=False):
        data_abertura = date.today().strftime("%d/%m/%Y")
        with st.form("form_vaga", enter_to_submit=False):
            clientes = st.session_state.clientes_df
            if clientes.empty:
                st.warning("⚠️ Cadastre um Cliente antes de cadastrar Vagas.")
            else:
                col1f, col2f = st.columns(2)
                with col1f:
                    cliente_sel = st.selectbox("Cliente *", options=clientes.apply(lambda x: f"{x['ID']} - {x['Cliente']}", axis=1))
                    cliente_id = cliente_sel.split(" - ")[0]
                    cliente_nome = clientes[clientes['ID'] == cliente_id]['Cliente'].iloc[0]
                    cargo = st.text_input("Cargo *")
                    salario1 = st.text_input("Salário 1 (R$)")
                    salario2 = st.text_input("Salário 2 (R$)")
                    descricao = st.text_area("Descrição / Observação")
                with col2f:
                    recrutador = st.selectbox("Recrutador *", options=RECRUTADORES_PADRAO)
                    status = st.selectbox("Status", options=["Aberta", "Ag. Inicio", "Cancelada", "Fechada", "Reaberta", "Pausada"], index=0)
                    atualizacao = ""  # Preenche vazio
                submitted = st.form_submit_button("✅ Salvar Vaga", use_container_width=True)
                if submitted:
                    if not cargo or not recrutador:
                        st.warning("⚠️ Preencha todos os campos obrigatórios.")
                    else:
                        prox_id = str(next_id(st.session_state.vagas_df, "ID"))
                        nova = pd.DataFrame([{
                            "ID": prox_id,
                            "Cliente": cliente_nome,
                            "Status": status,
                            "Data de Abertura": data_abertura,
                            "Cargo": cargo,
                            "Recrutador": recrutador,
                            "Atualização": atualizacao,
                            "Salário 1": salario1,
                            "Salário 2": salario2,
                            "Descrição / Observação": descricao
                        }])
                        st.session_state.vagas_df = pd.concat([st.session_state.vagas_df, nova], ignore_index=True)
                        save_csv(st.session_state.vagas_df, VAGAS_CSV)
                        registrar_log("Vagas", "Criar", item_id=prox_id, detalhe=f"Vaga criada (ID {prox_id}).")
                        st.success(f"✅ Vaga cadastrada com sucesso! ID: {prox_id}")
                        st.rerun()
    st.subheader("📋 Vagas Cadastradas")
    if df.empty:
        st.info("Nenhuma vaga cadastrada.")
    else:
        download_button(df[VAGAS_COLS], "vagas.csv", "⬇️ Baixar Lista de Vagas")
        show_table(df[VAGAS_COLS], VAGAS_COLS, "vagas_df", VAGAS_CSV)

def tela_candidatos():
    # [sem mudanças de lógica]
    # ... [código igual]

def tela_logs():
    # [sem mudanças de lógica]
    # ... [código igual]

def refresh_data():
    st.session_state.clientes_df = load_csv(CLIENTES_CSV, CLIENTES_COLS)
    st.session_state.vagas_df = load_csv(VAGAS_CSV, VAGAS_COLS)
    st.session_state.candidatos_df = load_csv(CANDIDATOS_CSV, CANDIDATOS_COLS)
    registrar_log("Sistema", "Refresh", detalhe="Dados recarregados via botão Refresh.")

if st.session_state.logged_in:
    st.image("https://parmaconsultoria.com.br/wp-content/uploads/2023/10/logo-parma-1.png", width=180)
    st.caption(f"Usuário: {st.session_state.usuario}")
    page_label_map = {
        "menu": "Menu Principal",
        "clientes": "Clientes",
        "vagas": "Vagas",
        "candidatos": "Candidatos",
        "logs": "Logs do Sistema"
    }
    perms = st.session_state.get("permissoes", [])
    if "menu" not in perms:
        perms = ["menu"] + perms
    ordered_page_keys = ["menu", "clientes", "vagas", "candidatos", "logs"]
    allowed_pages = [p for p in ordered_page_keys if p in perms]
    labels = [page_label_map[p] for p in allowed_pages]
    try:
        index_initial = allowed_pages.index(st.session_state.page)
    except Exception:
        index_initial = 0

    total_buttons = len(labels) + 2
    menu_cols = st.columns([1] * total_buttons)
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
    elif current_page == "logs":
        if "logs" in perms:
            tela_logs()
        else:
            st.warning("⚠️ Você não tem permissão para acessar esta página.")
else:
    tela_login()
