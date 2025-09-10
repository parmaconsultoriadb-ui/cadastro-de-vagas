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
VAGAS_COLS = ["ID", "Cliente", "Status", "Data de Abertura", "Cargo", "Recrutador", "Data de Início", "Descrição / Observação"]
CANDIDATOS_COLS = ["ID", "Cliente", "Cargo", "Nome", "Telefone", "Recrutador", "Status", "Data de Início"]
LOGS_COLS = ["DataHora", "Usuario", "Aba", "Acao", "ItemID", "Campo", "ValorAnterior", "ValorNovo", "Detalhe"]

# ==============================
# Helpers de persistência
# ==============================
def load_csv(path, expected_cols):
    """Carrega um CSV garantindo as colunas esperadas (retorna DataFrame com as colunas na ordem esperada)."""
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, dtype=str)
            # Garantir colunas
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            # Reordenar e preencher NaN
            df = df[expected_cols]
            df = df.fillna("")
            # Garantir ID como string
            if "ID" in df.columns:
                df["ID"] = df["ID"].astype(str)
            return df
        except Exception:
            return pd.DataFrame(columns=expected_cols)
    else:
        return pd.DataFrame(columns=expected_cols)


def save_csv(df, path):
    """Salva DataFrame em CSV com encoding utf-8."""
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
        atual = pd.read_csv(LOGS_CSV, dtype=str)
        atual = atual.fillna("")
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
# Estado inicial do Streamlit
# ==============================
if "page" not in st.session_state:
    st.session_state.page = "login"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = None
if "edit_record" not in st.session_state:
    st.session_state.edit_record = {}
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = {"df_name": None, "row_id": None}

# Carregar DataFrames
if "clientes_df" not in st.session_state:
    st.session_state.clientes_df = load_csv(CLIENTES_CSV, CLIENTES_COLS)
if "vagas_df" not in st.session_state:
    st.session_state.vagas_df = load_csv(VAGAS_CSV, VAGAS_COLS)
if "candidatos_df" not in st.session_state:
    st.session_state.candidatos_df = load_csv(CANDIDATOS_CSV, CANDIDATOS_COLS)

# ==============================
# Estilo (CSS)
# ==============================
st.markdown(
    """
    <style>
    :root {
        --parma-blue-dark: #004488;
        --parma-blue-medium: #0066AA;
        --parma-blue-light: #E0F2F7;
        --parma-green-success: #28A745;
        --parma-yellow-warning: #FFC107;
        --parma-red-error: #DC3545;
        --parma-text-dark: #333333;
        --parma-background-light: #F8F9FA;
    }
    div.stButton > button {
        background-color: var(--parma-blue-dark) !important;
        color: white !important;
        border-radius: 8px;
        height: 2.5em;
        font-size: 15px;
        font-weight: bold;
        border: none;
        transition: background-color 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: var(--parma-blue-medium) !important;
        color: white !important;
    }
    .st-emotion-cache-1r6r0jr { background-color: var(--parma-blue-light); border-radius: 8px; padding: 10px; border: 1px solid var(--parma-blue-medium);}    
    h1, h2, h3, h4, h5, h6 { color: var(--parma-blue-dark); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================
# Funções UI auxiliares
# ==============================
def download_button(df, filename, label="⬇️ Baixar CSV"):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv, file_name=filename, mime="text/csv", use_container_width=True)


def show_table(df, cols, df_name, csv_path):
    """Exibe tabela com botões de editar e excluir."""
    if df is None or df.empty:
        st.info("Nenhum registro para exibir.")
        return

    header_cols = st.columns(len(cols) + 2)
    for i, c in enumerate(cols):
        header_cols[i].markdown(
            f"<div style='background-color:var(--parma-blue-light); padding:8px; font-weight:bold; color:var(--parma-text-dark); border-radius:4px; text-align:center;'>{c}</div>",
            unsafe_allow_html=True,
        )
    header_cols[-2].markdown("<div style='background-color:var(--parma-blue-light); padding:8px; font-weight:bold; color:var(--parma-text-dark); border-radius:4px; text-align:center;'>Editar</div>", unsafe_allow_html=True)
    header_cols[-1].markdown("<div style='background-color:var(--parma-blue-light); padding:8px; font-weight:bold; color:var(--parma-text-dark); border-radius:4px; text-align:center;'>Excluir</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    for _, row in df.iterrows():
        bg_color = "white"
        row_cols = st.columns(len(cols) + 2)
        for i, c in enumerate(cols):
            value = row.get(c, "")
            row_cols[i].markdown(f"<div style='background-color:{bg_color}; padding:6px; text-align:center; color:var(--parma-text-dark); border-radius:4px;'>{value}</div>", unsafe_allow_html=True)

        with row_cols[-2]:
            if st.button("✏️", key=f"edit_{df_name}_{row['ID']}", use_container_width=True):
                st.session_state.edit_mode = df_name
                st.session_state.edit_record = row.to_dict()
                st.rerun()
        with row_cols[-1]:
            if st.button("🗑️", key=f"del_{df_name}_{row['ID']}", use_container_width=True):
                st.session_state.confirm_delete = {"df_name": df_name, "row_id": row['ID']}
                st.rerun()

    # Confirmação de exclusão
    if st.session_state.confirm_delete["df_name"] == df_name:
        row_id = st.session_state.confirm_delete["row_id"]
        st.error(f"⚠️ Deseja realmente excluir o registro **ID {row_id}**? Esta ação é irreversível.")
        col_spacer1, col1, col2, col_spacer2 = st.columns([2, 1, 1, 2])
        with col1:
            if st.button("✅ Sim, excluir", key=f"confirm_{df_name}_{row_id}", use_container_width=True):
                # Executar exclusão e ações em cascata quando necessário
                if df_name == "clientes_df":
                    base_df = st.session_state.clientes_df.copy()
                    cliente_row = base_df[base_df["ID"] == row_id]
                    if not cliente_row.empty:
                        cliente_nome = cliente_row.iloc[0]["Cliente"]
                    else:
                        cliente_nome = None

                    st.session_state.clientes_df = base_df[base_df["ID"] != row_id]
                    save_csv(st.session_state.clientes_df, CLIENTES_CSV)

                    # Excluir vagas e candidatos relacionados
                    vagas_rel = st.session_state.vagas_df[st.session_state.vagas_df["Cliente"] == cliente_nome]["ID"].tolist() if cliente_nome else []
                    st.session_state.vagas_df = st.session_state.vagas_df[st.session_state.vagas_df["Cliente"] != cliente_nome]
                    save_csv(st.session_state.vagas_df, VAGAS_CSV)

                    st.session_state.candidatos_df = st.session_state.candidatos_df[st.session_state.candidatos_df["Cliente"] != cliente_nome]
                    save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)

                    registrar_log(aba="Clientes", acao="Excluir", item_id=row_id, detalhe=f"Cliente {row_id} excluído. Vagas removidas: {vagas_rel}")
                    registrar_log(aba="Vagas", acao="Excluir em Cascata", detalhe=f"Cliente {row_id} excluído. Vagas removidas: {vagas_rel}")
                    registrar_log(aba="Candidatos", acao="Excluir em Cascata", detalhe=f"Cliente {row_id} excluído. Candidatos relacionados excluídos.")

                elif df_name == "vagas_df":
                    base_df = st.session_state.vagas_df.copy()
                    vaga_row = base_df[base_df["ID"] == row_id]
                    if not vaga_row.empty:
                        vaga_cliente = vaga_row.iloc[0]["Cliente"]
                        vaga_cargo = vaga_row.iloc[0]["Cargo"]
                    else:
                        vaga_cliente = None
                        vaga_cargo = None

                    st.session_state.vagas_df = base_df[base_df["ID"] != row_id]
                    save_csv(st.session_state.vagas_df, VAGAS_CSV)

                    # Excluir candidatos relacionados (por Cliente+Cargo)
                    if vaga_cliente is not None and vaga_cargo is not None:
                        candidatos_rel = st.session_state.candidatos_df[(st.session_state.candidatos_df["Cliente"] == vaga_cliente) & (st.session_state.candidatos_df["Cargo"] == vaga_cargo)]["ID"].tolist()
                        st.session_state.candidatos_df = st.session_state.candidatos_df[~((st.session_state.candidatos_df["Cliente"] == vaga_cliente) & (st.session_state.candidatos_df["Cargo"] == vaga_cargo))]
                        save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)
                    else:
                        candidatos_rel = []

                    registrar_log(aba="Vagas", acao="Excluir", item_id=row_id, detalhe=f"Vaga {row_id} excluída. Candidatos removidos: {candidatos_rel}")
                    registrar_log(aba="Candidatos", acao="Excluir em Cascata", detalhe=f"Vaga {row_id} excluída. Candidatos removidos: {candidatos_rel}")

                elif df_name == "candidatos_df":
                    base_df = st.session_state.candidatos_df.copy()
                    st.session_state.candidatos_df = base_df[base_df["ID"] != row_id]
                    save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)
                    registrar_log(aba="Candidatos", acao="Excluir", item_id=row_id, detalhe=f"Candidato {row_id} excluído.")

                st.success(f"✅ Registro {row_id} excluído com sucesso!")
                st.session_state.confirm_delete = {"df_name": None, "row_id": None}
                st.rerun()
        with col2:
            if st.button("❌ Cancelar", key=f"cancel_{df_name}_{row_id}", use_container_width=True):
                st.session_state.confirm_delete = {"df_name": None, "row_id": None}
                st.rerun()

    st.divider()


def show_edit_form(df_name, cols, csv_path):
    """Formulário de edição para Clientes, Vagas e Candidatos."""
    record = st.session_state.edit_record
    st.subheader(f"✏️ Editando {df_name.replace('_df', '').capitalize()}")

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
                    di = datetime.strptime(data_inicio_str, "%d/%m/%Y").date()
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
                            registrar_log(aba=df_name.replace('_df', '').capitalize(), acao="Editar", item_id=record["ID"], campo=c, valor_anterior=antigo, valor_novo=novo, detalhe=f"Registro {record['ID']} alterado em {c}.")
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

                        if novo_status == "Validado":
                            if antigo_status_vaga == "Aberta":
                                vagas_df.at[v_idx, "Status"] = "Ag. Inicio"
                                registrar_log(aba="Vagas", acao="Atualização Automática", item_id=vagas_df.at[v_idx, "ID"], campo="Status", valor_anterior=antigo_status_vaga, valor_novo="Ag. Inicio", detalhe=f"Vaga alterada automaticamente ao validar candidato {candidato_id}.")
                                st.info("🔄 Status da vaga alterado para 'Ag. Inicio' (candidato validado).")

                            if nova_data_inicio and nova_data_inicio <= date.today() and antigo_status_vaga != "Fechada":
                                vagas_df.at[v_idx, "Status"] = "Fechada"
                                registrar_log(aba="Vagas", acao="Atualização Automática", item_id=vagas_df.at[v_idx, "ID"], campo="Status", valor_anterior=antigo_status_vaga, valor_novo="Fechada", detalhe=f"Vaga fechada automaticamente (data de início do candidato {candidato_id} já passou).")
                                st.success("✅ Status da vaga alterado para 'Fechada' (data de início já passou).")

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

    if st.button("❌ Cancelar Edição", use_container_width=True, type="secondary"):
        st.session_state.edit_mode = None
        st.session_state.edit_record = {}
        st.rerun()

# ==============================
# Telas
# ==============================
def tela_login():
    st.image("https://github.com/parmaconsultoriadb-ui/cadastro-de-vagas/blob/main/Parma%20Consultoria.png?raw=true", width=350)
    st.title("🔒 Login - Parma Consultoria")

    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar", use_container_width=True)

        if submitted:
            if (usuario == "admin" and senha == "Parma!123@") or (usuario == "andre" and senha == "And!123@"):
                st.session_state.usuario = usuario
                st.session_state.logged_in = True
                st.session_state.page = "menu"
                registrar_log("Login", "Login", detalhe=f"Usuário {usuario} entrou no sistema.")
                st.success("✅ Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos.")


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
                    # Evitar IDs duplicados: preferir manter os existentes do sistema
                    base = st.session_state.clientes_df.copy()
                    combined = pd.concat([base, df_upload], ignore_index=True)
                    # Remover duplicatas por ID
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
        show_table(df_filtrado, CLIENTES_COLS, "clientes_df", CLIENTES_CSV)


def tela_vagas():
    if st.session_state.edit_mode == "vagas_df":
        show_edit_form("vagas_df", VAGAS_COLS, VAGAS_CSV)
        return

    st.header("📋 Vagas")
    st.markdown("Gerencie as vagas de emprego da consultoria.")

    # Upload de vagas
    with st.expander("📤 Importar Vagas (CSV/XLSX)", expanded=False):
        arquivo = st.file_uploader("Selecione um arquivo com as colunas: ID, Cliente, Status, Data de Abertura, Cargo, Recrutador, Data de Início, Descrição / Observação", type=["csv", "xlsx"], key="upload_vagas")
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

    with st.expander("➕ Cadastrar Nova Vaga", expanded=False):
        data_abertura = date.today().strftime("%d/%m/%Y")
        with st.form("form_vaga", enter_to_submit=False):
            clientes = st.session_state.clientes_df
            if clientes.empty:
                st.warning("⚠️ Cadastre um Cliente antes de cadastrar Vagas.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    cliente_sel = st.selectbox("Cliente *", options=clientes.apply(lambda x: f"{x['ID']} - {x['Cliente']}", axis=1))
                    cliente_id = cliente_sel.split(" - ")[0]
                    cliente_nome = clientes[clientes['ID'] == cliente_id]['Cliente'].iloc[0]
                    cargo = st.text_input("Cargo *")
                    descricao = st.text_area("Descrição / Observação")
                with col2:
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
                            "Descrição / Observação": descricao
                        }])
                        st.session_state.vagas_df = pd.concat([st.session_state.vagas_df, nova], ignore_index=True)
                        save_csv(st.session_state.vagas_df, VAGAS_CSV)
                        registrar_log("Vagas", "Criar", item_id=prox_id, detalhe=f"Vaga criada (ID {prox_id}).")
                        st.success(f"✅ Vaga cadastrada com sucesso! ID: {prox_id}")
                        st.rerun()

    st.subheader("📋 Vagas Cadastradas")
    df = st.session_state.vagas_df.copy()
    if df.empty:
        st.info("Nenhuma vaga cadastrada.")
    else:
        filtro = st.text_input("🔎 Buscar por Cargo/Cliente")
        mask = df['Cargo'].str.contains(filtro, case=False, na=False) | df['Cliente'].str.contains(filtro, case=False, na=False) if filtro else pd.Series([True]*len(df))
        df_filtrado = df[mask]
        # Não incluímos a coluna de descrição na listagem principal para manter visual limpo,
        # mas ela está persistida no CSV e aparece na edição/seleção.
        cols_show = [c for c in VAGAS_COLS if c != "Descrição / Observação"]
        download_button(df_filtrado[cols_show], "vagas.csv", "⬇️ Baixar Lista de Vagas")
        show_table(df_filtrado[cols_show], cols_show, "vagas_df", VAGAS_CSV)


def tela_candidatos():
    if st.session_state.edit_mode == "candidatos_df":
        show_edit_form("candidatos_df", CANDIDATOS_COLS, CANDIDATOS_CSV)
        return

    st.header("🧑‍💼 Candidatos")
    st.markdown("Gerencie os candidatos inscritos nas vagas.")

    # Prepara lista de vagas disponíveis (status não em Ag. Inicio ou Fechada)
    vagas_disponiveis = st.session_state.vagas_df[~st.session_state.vagas_df['Status'].isin(['Ag. Inicio', 'Fechada'])].copy()
    vaga_id = None
    if vagas_disponiveis.empty:
        st.warning("⚠️ Não há vagas disponíveis para cadastrar candidatos. Cadastre ou reabra vagas.")
    else:
        vagas_disponiveis['Opcao'] = vagas_disponiveis.apply(lambda x: f"{x['ID']} - {x['Cliente']} - {x['Cargo']}", axis=1)

    # Upload de candidatos
    with st.expander("📤 Importar Candidatos (CSV/XLSX)", expanded=False):
        arquivo = st.file_uploader("Selecione um arquivo com as colunas: ID, Cliente, Cargo, Nome, Telefone, Recrutador, Status, Data de Início", type=["csv", "xlsx"], key="upload_candidatos")
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
                vaga_sel = st.selectbox("Vaga *", options=vagas_disponiveis['Opcao'].tolist(), key="vaga_sel")
                try:
                    vaga_id = vaga_sel.split(' - ')[0].strip()
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
                            vaga_row = st.session_state.vagas_df[st.session_state.vagas_df['ID'] == vaga_id].iloc[0]
                            cliente_nome = vaga_row['Cliente']
                            cargo_nome = vaga_row['Cargo']
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
            if vaga_id:
                try:
                    vaga_row = st.session_state.vagas_df[st.session_state.vagas_df['ID'] == vaga_id].iloc[0]
                    st.markdown(f"- **Status:** {vaga_row['Status']}\n- **Cliente:** {vaga_row['Cliente']}\n- **Cargo:** {vaga_row['Cargo']}\n- **Recrutador:** {vaga_row['Recrutador']}\n- **Data de Abertura:** {vaga_row['Data de Abertura']}\n- **Data de Início:** {vaga_row.get('Data de Início', '')}\n- **Descrição / Observação:** {vaga_row.get('Descrição / Observação', '')}")
                except Exception:
                    st.info("Nenhuma vaga selecionada ou encontrada.")
            else:
                st.info("Selecione uma vaga para ver as informações.")

    st.subheader("📋 Candidatos Cadastrados")
    df = st.session_state.candidatos_df.copy()
    if df.empty:
        st.info("Nenhum candidato cadastrado.")
    else:
        filtro = st.text_input("🔎 Buscar por Nome/Cliente/Cargo")
        mask = (
            df['Nome'].str.contains(filtro, case=False, na=False) |
            df['Cliente'].str.contains(filtro, case=False, na=False) |
            df['Cargo'].str.contains(filtro, case=False, na=False)
        ) if filtro else pd.Series([True]*len(df))
        df_filtrado = df[mask]
        download_button(df_filtrado, "candidatos.csv", "⬇️ Baixar Lista de Candidatos")
        show_table(df_filtrado, CANDIDATOS_COLS, "candidatos_df", CANDIDATOS_CSV)


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


def tela_menu():
    st.image("https://github.com/parmaconsultoriadb-ui/cadastro-de-vagas/blob/main/Parma%20Consultoria.png?raw=true", width=350)
    st.title("📊 Sistema Parma Consultoria")
    st.subheader("Bem-vindo! Escolha uma opção para começar.")
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👥 Clientes", use_container_width=True):
            st.session_state.page = "clientes"
            st.rerun()
    with col2:
        if st.button("📋 Vagas", use_container_width=True):
            st.session_state.page = "vagas"
            st.rerun()
    with col3:
        if st.button("🧑‍💼 Candidatos", use_container_width=True):
            st.session_state.page = "candidatos"
            st.rerun()

    st.divider()

    if st.button("📜 Logs do Sistema", use_container_width=True):
        st.session_state.page = "logs"
        st.rerun()

# ==============================
# Lógica principal
# ==============================
if st.session_state.logged_in:
    st.sidebar.image("https://github.com/parmaconsultoriadb-ui/cadastro-de-vagas/blob/main/Parma%20Consultoria.png?raw=true", width=200)
    st.sidebar.title("Navegação")

    menu_options = {
        "Menu Principal": "menu",
        "Clientes": "clientes",
        "Vagas": "vagas",
        "Candidatos": "candidatos",
        "Logs do Sistema": "logs"
    }

    # determinar índice inicial de seleção (fallback seguro)
    try:
        index_initial = list(menu_options.values()).index(st.session_state.page)
    except Exception:
        index_initial = 0

    selected_page_label = st.sidebar.radio(
        "Selecione uma página",
        list(menu_options.keys()),
        index=index_initial,
        key="sidebar_radio_menu"
    )

    if st.sidebar.button("Sair", use_container_width=True):
        registrar_log("Login", "Logout", detalhe=f"Usuário {st.session_state.usuario} saiu do sistema.")
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()

    current_page = menu_options[selected_page_label]

    if current_page == "menu":
        tela_menu()
    elif current_page == "clientes":
        tela_clientes()
    elif current_page == "vagas":
        tela_vagas()
    elif current_page == "candidatos":
        tela_candidatos()
    elif current_page == "logs":
        tela_logs()

else:
    tela_login()
