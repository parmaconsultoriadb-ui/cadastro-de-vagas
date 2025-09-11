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
    # lorrayne: apenas Vagas e Candidatos (menu incluso)
    "lorrayne": {"senha": "Lrn!123@", "permissoes": ["menu", "vagas", "candidatos"]},
}

# ==============================
# Helpers de persistência
# ==============================
def load_csv(path, expected_cols):
    """Carrega CSV garantindo as colunas esperadas e a ordem."""
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
    """Gera próximo ID sequencial baseado na coluna ID (assume inteiros)."""
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

# Carregar DataFrames na sessão (somente na primeira carga; use Refresh na sidebar para recarregar)
if "clientes_df" not in st.session_state:
    st.session_state.clientes_df = load_csv(CLIENTES_CSV, CLIENTES_COLS)
if "vagas_df" not in st.session_state:
    st.session_state.vagas_df = load_csv(VAGAS_CSV, VAGAS_COLS)
if "candidatos_df" not in st.session_state:
    st.session_state.candidatos_df = load_csv(CANDIDATOS_CSV, CANDIDATOS_COLS)

# ==============================
# Estilo (fonte 13px e linha horizontal contínua entre registros)
# ==============================
st.markdown(
    """
    <style>
    :root {
        --parma-blue-dark: #004488;
        --parma-blue-medium: #0066AA;
        --parma-blue-light: #E0F2F7;
        --parma-text-dark: #333333;
    }

    /* Botões padrão */
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

    /* Parâmetros para show_table (headers/cells sem bordas verticais) */
    .parma-header {
        background-color: var(--parma-blue-light);
        padding:6px;
        font-weight:bold;
        color:var(--parma-text-dark);
        border-radius:4px;
        text-align:center;
        font-size:13px;
        /* separador abaixo do header, contínuo */
        border-bottom: 1px solid #cfcfcf;
    }
    .parma-cell {
        padding:6px;
        text-align:center;
        color:var(--parma-text-dark);
        font-size:13px;
        background-color: white;
        /* sem bordas individuais: a linha entre registros será um <hr> full-width */
        border: none;
    }

    /* Ajuste para st.dataframe (tabela padrão do Streamlit): fonte 10px, sem bordas verticais */
    .stDataFrame div[data-testid="stStyledTable"] table {
        font-size: 13px !important;
        border-collapse: collapse !important;
    }
    .stDataFrame div[data-testid="stStyledTable"] thead th {
        font-size: 13px !important;
        background-color: #f6f9fb !important;
        padding: 6px !important;
        border-bottom: 1px solid #cfcfcf !important; /* separador header -> linhas */
        border-left: none !important;
        border-right: none !important;
    }
    .stDataFrame div[data-testid="stStyledTable"] tbody tr {
        /* não colocamos bordas nas células; a linha de separação é um <hr> inserido entre as linhas */
    }
    .stDataFrame div[data-testid="stStyledTable"] td {
        padding: 6px !important;
        border: none !important;
    }

    /* estilo do <hr> que usamos entre linhas */
    hr.parma-hr {
        border: none;
        border-bottom: 1px solid #e0e0e0;
        margin: 0;
    }

    /* Ajustes para componentes menores */
    .streamlit-expanderHeader, .stMarkdown, .stText {
        font-size:13px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================
# UI helpers
# ==============================
def download_button(df, filename, label="⬇️ Baixar CSV"):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv, file_name=filename, mime="text/csv", use_container_width=True)

def show_table(df, cols, df_name, csv_path):
    """
    Exibe tabela com botões de editar e excluir.
    A separação entre registros é feita por uma linha horizontal contínua (<hr>) full-width,
    para que a linha vá de ID até Excluir.
    """
    if df is None or df.empty:
        st.info("Nenhum registro para exibir.")
        return

    # Cabeçalho (colunas + Editar + Excluir)
    header_cols = st.columns(len(cols) + 2)
    for i, c in enumerate(cols):
        header_cols[i].markdown(f"<div class='parma-header'>{c}</div>", unsafe_allow_html=True)
    header_cols[-2].markdown("<div class='parma-header'>Editar</div>", unsafe_allow_html=True)
    header_cols[-1].markdown("<div class='parma-header'>Excluir</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Linhas
    for _, row in df.iterrows():
        row_cols = st.columns(len(cols) + 2)
        for i, c in enumerate(cols):
            value = row.get(c, "")
            if pd.isna(value):
                value = ""
            # renderizamos o conteúdo da célula com css sem bordas; a linha contínua vem em seguida (hr)
            row_cols[i].markdown(f"<div class='parma-cell'>{value}</div>", unsafe_allow_html=True)

        # Botões Editar / Excluir
        with row_cols[-2]:
            if st.button("✏️", key=f"edit_{df_name}_{str(row.get('ID',''))}", use_container_width=True):
                st.session_state.edit_mode = df_name
                st.session_state.edit_record = row.to_dict()
                st.rerun()
        with row_cols[-1]:
            if st.button("🗑️", key=f"del_{df_name}_{str(row.get('ID',''))}", use_container_width=True):
                st.session_state.confirm_delete = {"df_name": df_name, "row_id": row["ID"]}
                st.rerun()

        # Linha horizontal contínua full-width (separa este registro do próximo)
        st.markdown("<hr class='parma-hr' />", unsafe_allow_html=True)

    # Confirmação de exclusão (fora do loop)
    if st.session_state.confirm_delete["df_name"] == df_name:
        row_id = st.session_state.confirm_delete["row_id"]
        st.error(f"⚠️ Deseja realmente excluir o registro **ID {row_id}**? Esta ação é irreversível.")
        col_sp1, col_yes, col_no, col_sp2 = st.columns([2, 1, 1, 2])
        with col_yes:
            if st.button("✅ Sim, excluir", key=f"confirm_{df_name}_{row_id}", use_container_width=True):
                # exclusão com cascata quando necessário
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

# ==============================
# Formulário de edição (Clientes / Vagas / Candidatos)
# ==============================
def show_edit_form(df_name, cols, csv_path):
    record = st.session_state.edit_record
    st.subheader(f"✏️ Editando {df_name.replace('_df','').capitalize()}")

    with st.form("edit_form", clear_on_submit=False):
        new_data = {}
        for c in cols:
            val = record.get(c, "")
            if c == "ID":
                new_data[c] = st.text_input(c, value=val, disabled=True)
            elif c == "Status" and df_name == "candidatos_df":
                opcoes = ["Enviado", "Não entrevistado", "Validado", "Não validado", "Desistência"]
                idx = opcoes.index(val) if val in opcoes else 0
                new_data[c] = st.selectbox(c, options=opcoes, index=idx)
            elif c == "Status" and df_name == "vagas_df":
                opcoes = ["Aberta", "Ag. Inicio", "Cancelada", "Fechada", "Reaberta", "Pausada"]
                idx = opcoes.index(val) if val in opcoes else 0
                new_data[c] = st.selectbox(c, options=opcoes, index=idx)
            elif c == "Data de Início":
                new_data[c] = st.text_input(c, value=val, help="Formato: DD/MM/YYYY")
            elif c in ["Salário 1", "Salário 2"]:
                new_data[c] = st.text_input(c, value=val)
            elif c == "Descrição / Observação":
                new_data[c] = st.text_area(c, value=val)
            else:
                new_data[c] = st.text_input(c, value=val)

        submitted = st.form_submit_button("✅ Salvar Alterações", use_container_width=True)
        if submitted:
            # Validações básicas de data
            data_inicio_str = new_data.get("Data de Início")
            if data_inicio_str:
                try:
                    datetime.strptime(data_inicio_str, "%d/%m/%Y")
                except ValueError:
                    st.error("❌ Formato de data inválido. Use DD/MM/YYYY.")
                    return

            df = st.session_state[df_name].copy()
            idx = df[df["ID"] == record["ID"]].index
            if not idx.empty:
                idx0 = idx[0]
                for c in cols:
                    if c in df.columns:
                        antigo = df.at[idx0, c]
                        novo = new_data.get(c, "")
                        if str(antigo) != str(novo):
                            registrar_log(aba=df_name.replace('_df','').capitalize(), acao="Editar", item_id=record["ID"], campo=c, valor_anterior=antigo, valor_novo=novo, detalhe=f"Registro {record['ID']} alterado em {c}.")
                            df.at[idx0, c] = novo

                st.session_state[df_name] = df
                save_csv(df, csv_path)

                # Se editou candidato, aplicar lógica de atualização automática na vaga correspondente
                if df_name == "candidatos_df":
                    candidato_id = record.get("ID")
                    antigo_status = record.get("Status")
                    novo_status = new_data.get("Status")
                    nova_data_inicio = None
                    if new_data.get("Data de Início"):
                        try:
                            nova_data_inicio = datetime.strptime(new_data.get("Data de Início"), "%d/%m/%Y").date()
                        except Exception:
                            nova_data_inicio = None

                    # Encontrar vaga correspondente (primeira coincidência por Cliente+Cargo)
                    vagas_df = st.session_state.vagas_df.copy()
                    vaga_match = vagas_df[(vagas_df["Cliente"] == df.at[idx0, "Cliente"]) & (vagas_df["Cargo"] == df.at[idx0, "Cargo"])]
                    if not vaga_match.empty:
                        v_idx = vaga_match.index[0]
                        antigo_status_vaga = vagas_df.at[v_idx, "Status"]

                        if novo_status == "Validado" and nova_data_inicio not in (None, "", pd.NaT):
                                vagas_df.at[v_idx, "Status"] = "Ag. Inicio"
                                registrar_log(aba="Vagas", acao="Atualização Automática", item_id=vagas_df.at[v_idx, "ID"], campo="Status", valor_anterior=antigo_status_vaga, valor_novo="Ag. Inicio", detalhe=f"Vaga alterada automaticamente ao validar candidato {candidato_id}.")
                                st.info("🔄 Status da vaga alterado para 'Ag. Inicio' (candidato validado).")

                        # Se o candidato era validado e agora desistiu, reabrir vaga
                        if antigo_status == "Validado" and novo_status == "Desistência":
                            if vagas_df.at[v_idx, "Status"] in ["Ag. Inicio", "Fechada"]:
                                vagas_df.at[v_idx, "Status"] = "Reaberta"
                                registrar_log(aba="Vagas", acao="Atualização Automática", item_id=vagas_df.at[v_idx, "ID"], campo="Status", valor_anterior=antigo_status_vaga, valor_novo="Reaberta", detalhe=f"Vaga reaberta automaticamente por desistência do candidato {candidato_id}.")
                                st.info("🔄 Vaga reaberta automaticamente!")

                        st.session_state.vagas_df = vagas_df
                        save_csv(vagas_df, VAGAS_CSV)

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
# Telas principais (login/menu/clientes/vagas/candidatos/logs)
# ==============================
def tela_login():
    st.image("https://github.com/parmaconsultoriadb-ui/cadastro-de-vagas/blob/main/Parma%20Consultoria.png?raw=true", width=350)
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

def tela_menu_interno():
    st.image("https://github.com/parmaconsultoriadb-ui/cadastro-de-vagas/blob/main/Parma%20Consultoria.png?raw=true", width=350)
    st.title("📊 Sistema Parma Consultoria")
    st.subheader("Bem-vindo! Escolha uma opção para começar.")
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        if "clientes" in st.session_state.permissoes:
            if st.button("👥 Clientes", use_container_width=True):
                st.session_state.page = "clientes"
                st.rerun()
    with col2:
        if "vagas" in st.session_state.permissoes:
            if st.button("📋 Vagas", use_container_width=True):
                st.session_state.page = "vagas"
                st.rerun()
    with col3:
        if "candidatos" in st.session_state.permissoes:
            if st.button("🧑‍💼 Candidatos", use_container_width=True):
                st.session_state.page = "candidatos"
                st.rerun()

    st.divider()
    if "logs" in st.session_state.permissoes:
        if st.button("📜 Logs do Sistema", use_container_width=True):
            st.session_state.page = "logs"
            st.rerun()

def tela_clientes():
    if st.session_state.edit_mode == "clientes_df":
        show_edit_form("clientes_df", CLIENTES_COLS, CLIENTES_CSV)
        return

    st.header("👥 Clientes")
    st.markdown("Gerencie o cadastro e as informações dos seus clientes.")

    # Upload de arquivo (CSV/XLSX)
    with st.expander("📤 Importar Clientes (CSV/XLSX)", expanded=False):
        arquivo = st.file_uploader("Selecione um arquivo com as colunas: ID, Data, Cliente, Nome, Cidade, UF, Telefone, E-mail", type=["csv", "xlsx"], key="upload_clientes")
        if arquivo is not None:
            try:
                if arquivo.name.lower().endswith('.csv'):
                    df_upload = pd.read_csv(arquivo, dtype=str)
                else:
                    df_upload = pd.read_excel(arquivo, dtype=str)

                missing = [c for c in CLIENTES_COLS if c not in df_upload.columns]
                if missing:
                    st.error(f"Colunas faltando: {missing}")
                else:
                    df_upload = df_upload[CLIENTES_COLS].fillna("")
                    base = st.session_state.clientes_df.copy()
                    combined = pd.concat([base, df_upload], ignore_index=True)
                    combined = combined.drop_duplicates(subset=["ID"], keep="first")
                    st.session_state.clientes_df = combined
                    save_csv(combined, CLIENTES_CSV)
                    registrar_log("Clientes", "Importar", detalhe=f"Importação de clientes via upload ({arquivo.name}).")
                    st.success("✅ Clientes importados com sucesso!")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {e}")

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
        cols_show = [c for c in CLIENTES_COLS if c != "ID"]
        show_table(df_filtrado, cols_show, "clientes_df", CLIENTES_CSV)

def tela_vagas():
    if st.session_state.edit_mode == "vagas_df":
        show_edit_form("vagas_df", VAGAS_COLS, VAGAS_CSV)
        return

    st.header("📋 Vagas")
    st.markdown("Gerencie as vagas de emprego da consultoria.")

    df_all = st.session_state.vagas_df.copy()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        status_opts = ["(todos)"] + sorted(df_all["Status"].dropna().unique().tolist())
        status_filter = st.selectbox("Filtrar por Status", status_opts, index=0)
    with col2:
        cliente_opts = ["(todos)"] + sorted(df_all["Cliente"].dropna().unique().tolist())
        cliente_filter = st.selectbox("Filtrar por Cliente", cliente_opts, index=0)
    with col3:
        cargo_opts = ["(todos)"] + sorted(df_all["Cargo"].dropna().unique().tolist())
        cargo_filter = st.selectbox("Filtrar por Cargo", cargo_opts, index=0)

    df = df_all.copy()
    if status_filter != "(todos)":
        df = df[df["Status"] == status_filter]
    if cliente_filter != "(todos)":
        df = df[df["Cliente"] == cliente_filter]
    if cargo_filter != "(todos)":
        df = df[df["Cargo"] == cargo_filter]

    # Upload de vagas
    with st.expander("📤 Importar Vagas (CSV/XLSX)", expanded=False):
        arquivo = st.file_uploader("Selecione um arquivo com as colunas: " + ", ".join(VAGAS_COLS), type=["csv", "xlsx"], key="upload_vagas")
        if arquivo is not None:
            try:
                if arquivo.name.lower().endswith('.csv'):
                    df_upload = pd.read_csv(arquivo, dtype=str)
                else:
                    df_upload = pd.read_excel(arquivo, dtype=str)

                missing = [c for c in VAGAS_COLS if c not in df_upload.columns]
                if missing:
                    st.error(f"Colunas faltando: {missing}")
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

    # Cadastro de nova vaga
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
                    recrutador = st.text_input("Recrutador *")
                    status = st.selectbox("Status", options=["Aberta", "Ag. Inicio", "Cancelada", "Fechada", "Reaberta", "Pausada"], index=0)
                    data_inicio = st.text_input("Data de Início", value="", help="Formato: DD/MM/YYYY")

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
                            "Data de Início": data_inicio,
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
    cols_show = [c for c in VAGAS_COLS if c not in ["ID", "Salário 1", "Salário 2", "Descrição / Observação"]]
    if df.empty:
    st.info("Nenhuma vaga cadastrada.")
    if df.empty:
        st.info("Nenhuma vaga cadastrada.")
    else:
        download_button(df[cols_show], "vagas.csv", "⬇️ Baixar Lista de Vagas")
    show_table(df[cols_show], cols_show, "vagas_df", VAGAS_CSV)

def tela_candidatos():
    if st.session_state.edit_mode == "candidatos_df":
        show_edit_form("candidatos_df", CANDIDATOS_COLS, CANDIDATOS_CSV)
        return

    st.header("🧑‍💼 Candidatos")
    st.markdown("Gerencie os candidatos inscritos nas vagas.")

    df_all = st.session_state.candidatos_df.copy()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        status_opts = ["(todos)"] + sorted(df_all["Status"].dropna().unique().tolist())
        status_filter = st.selectbox("Filtrar por Status", status_opts, index=0)
    with col2:
        cliente_opts = ["(todos)"] + sorted(df_all["Cliente"].dropna().unique().tolist())
        cliente_filter = st.selectbox("Filtrar por Cliente", cliente_opts, index=0)
    with col3:
        cargo_opts = ["(todos)"] + sorted(df_all["Cargo"].dropna().unique().tolist())
        cargo_filter = st.selectbox("Filtrar por Cargo", cargo_opts, index=0)

    df = df_all.copy()
    if status_filter != "(todos)":
        df = df[df["Status"] == status_filter]
    if cliente_filter != "(todos)":
        df = df[df["Cliente"] == cliente_filter]
    if cargo_filter != "(todos)":
        df = df[df["Cargo"] == cargo_filter]

    # Prepara lista de vagas disponíveis (status não em Ag. Inicio ou Fechada)
    vagas_disponiveis = st.session_state.vagas_df[~st.session_state.vagas_df["Status"].isin(["Ag. Inicio", "Fechada"])].copy()
    if not vagas_disponiveis.empty:
        vagas_disponiveis["Opcao"] = vagas_disponiveis.apply(lambda x: f"{x['ID']} - {x['Cliente']} - {x['Cargo']}", axis=1)

    # Upload de candidatos
    with st.expander("📤 Importar Candidatos (CSV/XLSX)", expanded=False):
        arquivo = st.file_uploader("Selecione um arquivo com as colunas: " + ", ".join(CANDIDATOS_COLS), type=["csv", "xlsx"], key="upload_candidatos")
        if arquivo is not None:
            try:
                if arquivo.name.lower().endswith('.csv'):
                    df_upload = pd.read_csv(arquivo, dtype=str)
                else:
                    df_upload = pd.read_excel(arquivo, dtype=str)

                missing = [c for c in CANDIDATOS_COLS if c not in df_upload.columns]
                if missing:
                    st.error(f"Colunas faltando: {missing}")
                else:
                    df_upload = df_upload[CANDIDATOS_COLS].fillna("")
                    base = st.session_state.candidatos_df.copy()
                    combined = pd.concat([base, df_upload], ignore_index=True)
                    combined = combined.drop_duplicates(subset=["ID"], keep="first")
                    st.session_state.candidatos_df = combined
                    save_csv(combined, CANDIDATOS_CSV)
                    registrar_log("Candidatos", "Importar", detalhe=f"Importação de candidatos via upload ({arquivo.name}).")
                    st.success("✅ Candidatos importados com sucesso!")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {e}")

    with st.expander("➕ Cadastrar Novo Candidato", expanded=False):
        col_form, col_info = st.columns([2, 1])
        with col_form:
            if vagas_disponiveis.empty:
                st.info("Cadastre uma vaga disponível primeiro.")
            else:
                vaga_sel = st.selectbox("Vaga *", options=vagas_disponiveis["Opcao"].tolist(), key="vaga_sel")
                try:
                    vaga_id = vaga_sel.split(" - ")[0].strip()
                except Exception:
                    vaga_id = None

                with st.form("form_candidato", enter_to_submit=False):
                    nome = st.text_input("Nome *")
                    telefone = st.text_input("Telefone *")
                    recrutador = st.text_input("Recrutador *")

                    submitted = st.form_submit_button("✅ Salvar Candidato", use_container_width=True)
                    if submitted:
                        if not nome or not telefone or not recrutador or not vaga_id:
                            st.warning("⚠️ Preencha todos os campos obrigatórios e selecione uma vaga.")
                        else:
                            vaga_row = st.session_state.vagas_df[st.session_state.vagas_df["ID"] == vaga_id].iloc[0]
                            cliente_nome = vaga_row["Cliente"]
                            cargo_nome = vaga_row["Cargo"]
                            prox_id = str(next_id(st.session_state.candidatos_df, "ID"))
                            novo = pd.DataFrame([{
                                "ID": prox_id,
                                "Cliente": cliente_nome,
                                "Cargo": cargo_nome,
                                "Nome": nome,
                                "Telefone": telefone,
                                "Recrutador": recrutador,
                                "Status": "Enviado",
                                "Data de Início": "",
                            }])
                            st.session_state.candidatos_df = pd.concat([st.session_state.candidatos_df, novo], ignore_index=True)
                            save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)
                            registrar_log("Candidatos", "Criar", item_id=prox_id, detalhe=f"Candidato criado (ID {prox_id}).")
                            st.success(f"✅ Candidato cadastrado com sucesso! ID: {prox_id}")
                            st.rerun()

        with col_info:
            st.subheader("Vaga Selecionada")
            if 'vaga_id' in locals() and vaga_id:
                try:
                    vaga_row = st.session_state.vagas_df[st.session_state.vagas_df["ID"] == vaga_id].iloc[0]
                    st.markdown(
                        f"- **Status:** {vaga_row['Status']}\n"
                        f"- **Cliente:** {vaga_row['Cliente']}\n"
                        f"- **Cargo:** {vaga_row['Cargo']}\n"
                        f"- **Recrutador:** {vaga_row['Recrutador']}\n"
                        f"- **Data de Abertura:** {vaga_row['Data de Abertura']}\n"
                        f"- **Data de Início:** {vaga_row.get('Data de Início', '')}\n"
                        f"- **Salário 1:** {vaga_row.get('Salário 1', '')}\n"
                        f"- **Salário 2:** {vaga_row.get('Salário 2', '')}\n"
                        f"- **Descrição / Observação:** {vaga_row.get('Descrição / Observação', '')}"
                    )
                except Exception:
                    st.info("Nenhuma vaga selecionada ou encontrada.")
            else:
                st.info("Selecione uma vaga para ver as informações.")

    st.subheader("📋 Candidatos Cadastrados")
    if df.empty:
        st.info("Nenhum candidato cadastrado.")
    else:
        download_button(df, "candidatos.csv", "⬇️ Baixar Lista de Candidatos")
        show_table(df, CANDIDATOS_COLS, "candidatos_df", CANDIDATOS_CSV)

def tela_logs():
    st.header("📜 Logs do Sistema")
    st.markdown("Visualize todas as ações realizadas no sistema.")
    df_logs = carregar_logs()

    if df_logs.empty:
        st.info("Nenhum log registrado ainda.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            aba_f = st.selectbox("Filtrar por Aba", options=["(todas)"] + sorted(df_logs["Aba"].dropna().unique().tolist()))
        with col2:
            acao_f = st.selectbox("Filtrar por Ação", options=["(todas)"] + sorted(df_logs["Acao"].dropna().unique().tolist()))
        with col3:
            usuario_f = st.selectbox("Filtrar por Usuário", options=["(todos)"] + sorted(df_logs["Usuario"].dropna().unique().tolist()))

        busca = st.text_input("🔎 Buscar (Campo/Detalhe/ItemID)")

        dfv = df_logs.copy()
        if aba_f != "(todas)":
            dfv = dfv[dfv["Aba"] == aba_f]
        if acao_f != "(todas)":
            dfv = dfv[dfv["Acao"] == acao_f]
        if usuario_f != "(todos)":
            dfv = dfv[dfv["Usuario"] == usuario_f]
        if busca:
            mask = (
                dfv["Campo"].fillna("").str.contains(busca, case=False) |
                dfv["Detalhe"].fillna("").str.contains(busca, case=False) |
                dfv["ItemID"].fillna("").str.contains(busca, case=False)
            )
            dfv = dfv[mask]

        st.dataframe(dfv.sort_values("DataHora", ascending=False), use_container_width=True, height=480)
        csv = dfv.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Baixar Logs Filtrados", csv, "logs.csv", "text/csv", use_container_width=True)

    st.divider()

# ==============================
# Refresh (recarrega CSVs na sessão)
# ==============================
def refresh_data():
    st.session_state.clientes_df = load_csv(CLIENTES_CSV, CLIENTES_COLS)
    st.session_state.vagas_df = load_csv(VAGAS_CSV, VAGAS_COLS)
    st.session_state.candidatos_df = load_csv(CANDIDATOS_CSV, CANDIDATOS_COLS)
    registrar_log("Sistema", "Refresh", detalhe="Dados recarregados via botão Refresh na sidebar.")

# ==============================
# Lógica principal (menu lateral com refresh apenas na sidebar)
# ==============================
if st.session_state.logged_in:
    st.sidebar.image("https://github.com/parmaconsultoriadb-ui/cadastro-de-vagas/blob/main/Parma%20Consultoria.png?raw=true", width=200)
    st.sidebar.title("Navegação")
    st.sidebar.caption(f"Usuário: {st.session_state.usuario}")

    # Botão de refresh somente na sidebar
    if st.sidebar.button("🔄 Refresh dados"):
        refresh_data()
        st.rerun()

    # map page key -> label
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

    selected_label = st.sidebar.radio("Selecione uma página", labels, index=index_initial, key="sidebar_radio_menu")

    # logout
    if st.sidebar.button("Sair", use_container_width=True):
        registrar_log("Login", "Logout", detalhe=f"Usuário {st.session_state.usuario} saiu do sistema.")
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()

    # map label -> page key
    try:
        selected_idx = labels.index(selected_label)
        current_page = allowed_pages[selected_idx]
    except Exception:
        current_page = "menu"

    # renderizar página com checagem de permissão
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
