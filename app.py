# ============================================================
# Sistema Parma Consultoria - CRM + Gestão
# ============================================================
# Inclui:
# - Login / Menu
# - Clientes
# - Vagas
# - Candidatos
# - Comercial (Kanban CRM) - AJUSTADO
# - Logs
#
# Autor: Agência Bravio
# ============================================================

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
COMERCIAL_CSV = "comercial.csv"  # Comercial

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

# Comercial (com 'Produto' e 'Telefone' na ordem definida)
COMERCIAL_COLS = [
    "ID",
    "Data",
    "Empresa",
    "Cidade",
    "UF",
    "Nome",
    "Telefone",
    "E-mail",
    "Produto",
    "Canal",
    "Status"
]

LOGS_COLS = ["DataHora", "Usuario", "Aba", "Acao", "ItemID", "Campo", "ValorAnterior", "ValorNovo", "Detalhe"]

# Opções de status da aba Comercial (ordem do funil)
COMERCIAL_STATUS_OPCOES = [
    "Prospect",
    "Lead Qualificado",
    "Reunião",
    "Proposta Enviada",
    "Negócio Fechado",
    "Declinado"
]

# ==============================
# Usuários e permissões
# ==============================
USUARIOS = {
    "admin":   {"senha": "Parma!123@", "permissoes": ["menu", "clientes", "vagas", "candidatos", "logs", "comercial"]},
    "andre":   {"senha": "And!123@",   "permissoes": ["clientes", "vagas", "candidatos", "comercial"]},
    "lorrayne":{"senha": "Lrn!123@",   "permissoes": ["vagas", "candidatos"]},
    "nikole":  {"senha": "Nkl!123@",   "permissoes": ["vagas", "candidatos"]},
    "julia":   {"senha": "Jla!123@",   "permissoes": ["vagas", "candidatos"]},
    "ricardo": {"senha": "Rcd!123@",   "permissoes": ["clientes", "vagas", "candidatos", "comercial"]},
}

# ==============================
# Recrutadores padrão
# ==============================
RECRUTADORES_PADRAO = ["Lorrayne", "Kaline", "Nikole", "Leila", "Julia"]

# ============================================================
# Funções utilitárias
# ============================================================

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

# ============================================================
# Estado inicial
# ============================================================

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

# ============================================================
# Carregamento inicial dos DataFrames
# ============================================================

for df_key, csv_path, cols in [
    ("clientes_df", CLIENTES_CSV, CLIENTES_COLS),
    ("vagas_df", VAGAS_CSV, VAGAS_COLS),
    ("candidatos_df", CANDIDATOS_CSV, CANDIDATOS_COLS),
    ("comercial_df", COMERCIAL_CSV, COMERCIAL_COLS),
]:
    if df_key not in st.session_state:
        st.session_state[df_key] = load_csv(csv_path, cols)

# ============================================================
# Estilos globais (CSS)
# ============================================================

st.markdown(
    """
    <style>
    :root {
        --parma-blue-dark: #004488;
        --parma-blue-medium: #0066AA;
        --parma-blue-light: #E0F2F7;
        --parma-text-dark: #333333;
        --kanban-bg: #f8fafc;
        --kanban-col-bg: #f1f5f9;
        --kanban-card-bg: #ffffff;
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
    </style>
    """,
    unsafe_allow_html=True,
)
# ============================================================
# Funções auxiliares de download e tabelas
# ============================================================

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

# ============================================================
# Tela de Clientes
# ============================================================

def tela_clientes():
    if st.session_state.edit_mode == "clientes_df":
        show_edit_form("clientes_df", CLIENTES_COLS, CLIENTES_CSV)
        return

    st.header("👥 Clientes")
    st.markdown("Gerencie o cadastro e as informações dos seus clientes.")

    # Cadastro de novo cliente
    with st.expander("➕ Cadastrar Novo Cliente", expanded=False):
        data_hoje = date.today().strftime("%d/%m/%Y")
        with st.form("form_clientes", enter_to_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                cliente = st.text_input("Cliente *")
                cidade = st.text_input("Cidade *")
                telefone = st.text_input("Telefone *")
            with col2:
                nome = st.text_input("Nome *")
                uf = st.text_input("UF *", max_chars=2)
                email = st.text_input("E-mail *")
            submitted = st.form_submit_button("✅ Salvar Cliente", use_container_width=True)

            if submitted:
                if not all([cliente, nome, cidade, uf, telefone, email]):
                    st.warning("⚠️ Preencha todos os campos obrigatórios.")
                else:
                    prox_id = str(next_id(st.session_state.clientes_df, "ID"))
                    novo = pd.DataFrame([{
                        "ID": prox_id,
                        "Data": data_hoje,
                        "Cliente": cliente,
                        "Nome": nome,
                        "Cidade": cidade,
                        "UF": uf.upper(),
                        "Telefone": telefone,
                        "E-mail": email,
                    }])
                    st.session_state.clientes_df = pd.concat([st.session_state.clientes_df, novo], ignore_index=True)
                    save_csv(st.session_state.clientes_df, CLIENTES_CSV)
                    registrar_log("Clientes", "Criar", item_id=prox_id, detalhe=f"Cliente criado (ID {prox_id}).")
                    st.success(f"✅ Cliente cadastrado com sucesso! ID: {prox_id}")
                    st.rerun()

    st.subheader("📋 Clientes Cadastrados")
    df = st.session_state.clientes_df.copy()
    if df.empty:
        st.info("Nenhum cliente cadastrado.")
    else:
        filtro = st.text_input("🔎 Buscar por Cliente")
        df_filtrado = df[df["Cliente"].str.contains(filtro, case=False, na=False)] if filtro else df
        download_button(df_filtrado, "clientes.csv", "⬇️ Baixar Lista de Clientes")
        show_table(df_filtrado, CLIENTES_COLS, "clientes_df", CLIENTES_CSV)

# ============================================================
# Tela de Vagas
# ============================================================

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

    st.subheader("📋 Vagas Cadastradas")
    if df.empty:
        st.info("Nenhuma vaga cadastrada.")
    else:
        VAGAS_COLS_VISUAL = [
            "ID", "Cliente", "Status", "Data de Abertura", "Cargo", "Recrutador", "Atualização"
        ]
        download_button(df[VAGAS_COLS], "vagas.csv", "⬇️ Baixar Lista de Vagas")
        show_table(df[VAGAS_COLS_VISUAL], VAGAS_COLS_VISUAL, "vagas_df", VAGAS_CSV)

# ============================================================
# Tela de Candidatos
# ============================================================

def tela_candidatos():
    if st.session_state.edit_mode == "candidatos_df":
        show_edit_form("candidatos_df", CANDIDATOS_COLS, CANDIDATOS_CSV)
        return

    st.header("🧑‍💼 Candidatos")
    st.markdown("Gerencie os candidatos inscritos nas vagas.")

    df_all = st.session_state.candidatos_df.copy()

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

    st.subheader("📋 Candidatos Cadastrados")
    df = st.session_state.candidatos_df.copy()
    if df.empty:
        st.info("Nenhum candidato cadastrado.")
    else:
        download_button(df, "candidatos.csv", "⬇️ Baixar Lista de Candidatos")
        show_table(df, CANDIDATOS_COLS, "candidatos_df", CANDIDATOS_CSV)
# ============================================================
# Comercial (Kanban ajustado)
# ============================================================

def _mover_status_comercial(item_id, direcao="+"):
    df = st.session_state.comercial_df.copy()
    idx = df[df["ID"] == str(item_id)].index
    if idx.empty:
        return False
    i = idx[0]
    atual = df.at[i, "Status"]
    if atual not in COMERCIAL_STATUS_OPCOES:
        return False

    pos = COMERCIAL_STATUS_OPCOES.index(atual)
    novo_pos = pos + (1 if direcao == "+" else -1)
    if 0 <= novo_pos < len(COMERCIAL_STATUS_OPCOES):
        novo = COMERCIAL_STATUS_OPCOES[novo_pos]
        df.at[i, "Status"] = novo
        st.session_state.comercial_df = df
        save_csv(df, COMERCIAL_CSV)
        registrar_log("Comercial", "Editar", item_id=df.at[i, "ID"], campo="Status", valor_anterior=atual, valor_novo=novo, detalhe=f"Movido no funil")
        return True
    return False

def _badge_status(status):
    cores = {
        "Prospect": "#ca8a04",
        "Lead Qualificado": "#0d9488",
        "Reunião": "#0284c7",
        "Proposta Enviada": "#db2777",
        "Negócio Fechado": "#16a34a",
        "Declinado": "#dc2626",
    }
    cor = cores.get(status, "#6b7280")
    return f"<span class='badge-status' style='background:{cor}'>{status}</span>"

def _card_comercial(reg):
    expand_key = f"expand_{reg['ID']}"
    expanded = st.session_state.get(expand_key, False)

    if st.button(
        f"▶ {reg['Empresa']} - {reg['Produto']} ({reg['Canal']})" if not expanded else f"▼ {reg['Empresa']} - {reg['Produto']} ({reg['Canal']})",
        key=f"title_{reg['ID']}",
        use_container_width=True
    ):
        st.session_state[expand_key] = not expanded
        st.rerun()

    if expanded:
        st.markdown(
            f"""
            <div class="kanban-card">
                <div class="kanban-meta">ID: {reg.get('ID','')} • {reg.get('Data','')}</div>
                <div><strong>{reg.get('Empresa','')}</strong></div>
                <div>{_badge_status(reg.get('Status',''))}</div>
                <div><strong>Contato:</strong> {reg.get('Nome','')} | <strong>Tel:</strong> {reg.get('Telefone','')}</div>
                <div><strong>E-mail:</strong> {reg.get('E-mail','')}</div>
                <div><strong>Produto:</strong> {reg.get('Produto','')}</div>
                <div><strong>Canal:</strong> {reg.get('Canal','')}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        c1, c2, c3, c4 = st.columns([0.5,0.5,0.5,0.5])
        with c1:
            if st.button("⮜", key=f"left_{reg['ID']}"):
                _mover_status_comercial(reg["ID"], "-")
                st.rerun()
        with c2:
            if st.button("⮞", key=f"right_{reg['ID']}"):
                _mover_status_comercial(reg["ID"], "+")
                st.rerun()
        with c3:
            if st.button("✏", key=f"edit_{reg['ID']}"):
                st.session_state.edit_mode = "comercial_df"
                st.session_state.edit_record = dict(reg)
                st.rerun()
        with c4:
            if st.button("🗑", key=f"del_{reg['ID']}"):
                st.session_state.confirm_delete = {"df_name":"comercial_df","row_id":reg["ID"]}
                st.rerun()

def tela_comercial():
    if st.session_state.edit_mode == "comercial_df":
        show_edit_form("comercial_df", COMERCIAL_COLS, COMERCIAL_CSV)
        return

    st.header("💼 Comercial (CRM)")
    st.markdown("Acompanhe o fluxo através do funil no formato **Kanban** ou visualize em **Lista**.")

    df_all = st.session_state.comercial_df.copy()
    tab_kanban, tab_lista = st.tabs(["🗂️ Kanban (Funil)", "📋 Lista"])

    with tab_kanban:
        cols = st.columns(len(COMERCIAL_STATUS_OPCOES))
        for i, status in enumerate(COMERCIAL_STATUS_OPCOES):
            with cols[i]:
                col_df = df_all[df_all["Status"] == status].copy()
                st.markdown(f"<div class='kanban-col' data-status='{status}'><div class='kanban-col-title'>{status} ({len(col_df)})</div>", unsafe_allow_html=True)
                if col_df.empty:
                    st.caption("—")
                else:
                    for _, reg in col_df.iterrows():
                        _card_comercial(reg)
                st.markdown("</div>", unsafe_allow_html=True)

    with tab_lista:
        st.subheader("📋 Oportunidades Comerciais (Lista)")
        df_list = df_all.copy()
        if df_list.empty:
            st.info("Nenhum registro comercial cadastrado.")
        else:
            download_button(df_list, "comercial.csv", "⬇️ Baixar Lista Comercial")
            show_table(df_list[COMERCIAL_COLS], COMERCIAL_COLS, "comercial_df", COMERCIAL_CSV)

# ============================================================
# Tela de Logs
# ============================================================

def tela_logs():
    st.header("📜 Logs do Sistema")
    st.markdown("Visualize todas as ações realizadas no sistema.")
    df_logs = carregar_logs()
    if df_logs.empty:
        st.info("Nenhum log registrado ainda.")
    else:
        st.dataframe(df_logs.sort_values("DataHora", ascending=False), use_container_width=True, height=480)
        csv = df_logs.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Baixar Logs", csv, "logs.csv", "text/csv", use_container_width=True)

# ============================================================
# Router principal
# ============================================================

if st.session_state.logged_in:
    current_page = st.session_state.page
    if current_page == "menu":
        tela_menu_interno()
    elif current_page == "clientes":
        tela_clientes()
    elif current_page == "vagas":
        tela_vagas()
    elif current_page == "candidatos":
        tela_candidatos()
    elif current_page == "comercial":
        tela_comercial()
    elif current_page == "logs":
        tela_logs()
else:
    tela_login()
