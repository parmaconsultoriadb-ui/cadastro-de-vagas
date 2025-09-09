import streamlit as st
import pandas as pd
from datetime import date, datetime
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
LOGS_CSV = "logs.csv"

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
# Logs
# ==============================
LOGS_COLS = ["DataHora", "Usuario", "Aba", "Acao", "ItemID", "Campo", "ValorAnterior", "ValorNovo", "Detalhe"]

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
        log_df = pd.concat([atual, log_df], ignore_index=True)
    save_csv(log_df, LOGS_CSV)

def carregar_logs():
    ensure_logs_file()
    return pd.read_csv(LOGS_CSV, dtype=str)

# ==============================
# Inicialização do estado
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
    "Data de Início",
]
CANDIDATOS_COLS = [
    "ID",
    "VagaID",
    "Status",
    "Nome",
    "Telefone",
    "Recrutador",
    "Data de Início",  # Nova coluna para Candidatos
]

ABA_MAP = {
    "clientes_df": "Clientes",
    "vagas_df": "Vagas",
    "candidatos_df": "Candidatos",
}

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
clientes_ids = set(st.session_state.clientes_df["ID"])
st.session_state.vagas_df = st.session_state.vagas_df[
    st.session_state.vagas_df["ClienteID"].isin(clientes_ids)
]

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
                new_data[c] = st.text_input(c, value=record.get(c, ""), disabled=True)
            elif c == "Status" and df_name == "candidatos_df":
                opcoes_candidatos = ["Enviado", "Não entrevistado", "Validado", "Não validado", "Desistência"]
                new_data[c] = st.selectbox(
                    c,
                    options=opcoes_candidatos,
                    index=opcoes_candidatos.index(record.get(c, "")) if record.get(c, "") in opcoes_candidatos else 0,
                )
            elif c == "Status" and df_name == "vagas_df":
                opcoes_vagas = ["Aberta", "Ag. Inicio", "Cancelada", "Fechada", "Reaberta", "Pausada"]
                new_data[c] = st.selectbox(
                    c,
                    options=opcoes_vagas,
                    index=opcoes_vagas.index(record.get(c, "")) if record.get(c, "") in opcoes_vagas else 0,
                )
            elif (c == "Data de Início" and df_name == "vagas_df") or \
                 (c == "Data de Início" and df_name == "candidatos_df"):
                new_data[c] = st.text_input(c, value=record.get(c, ""), help="Formato: DD/MM/YYYY")
            else:
                new_data[c] = st.text_input(c, value=record.get(c, ""))

        submitted = st.form_submit_button("Salvar Alterações", use_container_width=True)
        if submitted:
            # Validação para 'Data de Início' em ambas as abas
            if "Data de Início" in new_data and new_data["Data de Início"]:
                try:
                    datetime.strptime(new_data["Data de Início"], "%d/%m/%Y")
                except ValueError:
                    st.error("❌ Formato de data inválido. Use DD/MM/YYYY.")
                    return

            df = st.session_state[df_name].copy()
            idx = df[df["ID"] == record["ID"]].index
            if not idx.empty:
                # Verificação se o campo 'Data de Início' existe na tabela de destino
                if (df_name == "vagas_df" or df_name == "candidatos_df") and "Data de Início" in new_data and new_data["Data de Início"]:
                    pass
                else:
                    if "Data de Início" in new_data:
                        new_data["Data de Início"] = ""

                for c in cols:
                    if c in df.columns: # Adicionado para garantir que a coluna existe
                        antigo = df.loc[idx[0], c]
                        novo = new_data.get(c, '') # Usar .get para evitar KeyError
                        if str(antigo) != str(novo):
                            registrar_log(
                                aba=ABA_MAP[df_name],
                                acao="Editar",
                                item_id=record["ID"],
                                campo=c,
                                valor_anterior=antigo,
                                valor_novo=novo,
                                detalhe=f"Registro {record['ID']} alterado em {c}."
                            )
                            df.loc[idx, c] = novo

            st.session_state[df_name] = df
            save_csv(df, csv_path)

            # --- Lógica de atualização de Vagas com base em Candidatos (Modificada) ---
            if df_name == "candidatos_df":
                vaga_id = record.get("VagaID")
                vagas_df = st.session_state.vagas_df.copy()
                idx_vaga = vagas_df[vagas_df["ID"] == vaga_id].index
                if not idx_vaga.empty:
                    antigo_status_vaga = vagas_df.loc[idx_vaga[0], "Status"]
                    novo_status_candidato = new_data.get("Status")
                    nova_data_inicio = new_data.get("Data de Início")

                    # Regra 1: Candidato Validado sem Data de Início -> Vaga Ag. Inicio
                    if novo_status_candidato == "Validado" and not nova_data_inicio:
                        if antigo_status_vaga != "Ag. Inicio":
                            vagas_df.loc[idx_vaga, "Status"] = "Ag. Inicio"
                            st.info("🔄 Status da vaga alterado para 'Ag. Inicio' (candidato validado).")
                            registrar_log(
                                aba="Vagas",
                                acao="Atualização Automática",
                                item_id=vaga_id,
                                campo="Status",
                                valor_anterior=antigo_status_vaga,
                                valor_novo="Ag. Inicio",
                                detalhe=f"Vaga alterada automaticamente ao validar candidato {record['ID']}."
                            )
                    # Regra 2: Candidato Validado com Data de Início -> Vaga Fechada
                    elif novo_status_candidato == "Validado" and nova_data_inicio:
                        if antigo_status_vaga != "Fechada":
                            vagas_df.loc[idx_vaga, "Status"] = "Fechada"
                            st.success("✅ Status da vaga alterado para 'Fechada' (candidato contratado).")
                            registrar_log(
                                aba="Vagas",
                                acao="Atualização Automática",
                                item_id=vaga_id,
                                campo="Status",
                                valor_anterior=antigo_status_vaga,
                                valor_novo="Fechada",
                                detalhe=f"Vaga fechada automaticamente ao validar e preencher a data de início do candidato {record['ID']}."
                            )
                    # Regra 3: Se o status do candidato mudar para algo diferente de "Validado" e a vaga estava fechada ou ag. inicio
                    elif antigo_status_vaga in ["Ag. Inicio", "Fechada"] and novo_status_candidato != "Validado":
                        vagas_df.loc[idx_vaga, "Status"] = "Aberta"
                        st.info("🔄 Vaga reaberta automaticamente!")
                        registrar_log(
                            aba="Vagas",
                            acao="Atualização Automática",
                            item_id=vaga_id,
                            campo="Status",
                            valor_anterior=antigo_status_vaga,
                            valor_novo="Aberta",
                            detalhe=f"Vaga reaberta automaticamente ao reverter validação do candidato {record['ID']}."
                        )
                    
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
    # Cabeçalho
    cols_ui = st.columns(len(cols) + 2)
    for i, c in enumerate(cols):
        cols_ui[i].markdown(
            f"<div style='background-color:#f0f0f0; padding:6px; font-weight:bold; color:black; border-radius:4px; text-align:center;'>{c}</div>",
            unsafe_allow_html=True,
        )
    cols_ui[-2].markdown("<div style='background-color:#f0f0f0; padding:6px; font-weight:bold; color:black; border-radius:4px; text-align:center;'>Editar</div>", unsafe_allow_html=True)
    cols_ui[-1].markdown("<div style='background-color:#f0f0f0; padding:6px; font-weight:bold; color:black; border-radius:4px; text-align:center;'>Excluir</div>", unsafe_allow_html=True)

    # Linhas
    for idx, row in df.iterrows():
        bg_color = "#ffffff" if idx % 2 == 0 else "#f9f9f9"
        cols_ui = st.columns(len(cols) + 2)
        for i, c in enumerate(cols):
            cols_ui[i].markdown(f"<div style='background-color:{bg_color}; padding:6px; text-align:center; color:black;'>{row.get(c, '')}</div>", unsafe_allow_html=True)

        with cols_ui[-2]:
            if st.button("Editar", key=f"edit_{df_name}_{row['ID']}", use_container_width=True):
                st.session_state.edit_mode = df_name
                st.session_state.edit_record = row.to_dict()
                st.rerun()
        with cols_ui[-1]:
            if st.button("Excluir", key=f"del_{df_name}_{row['ID']}", use_container_width=True):
                st.session_state.confirm_delete = {"df_name": df_name, "row_id": row["ID"]}
                st.rerun()

    # Confirmação de exclusão
    if st.session_state.confirm_delete["df_name"] == df_name:
        row_id = st.session_state.confirm_delete["row_id"]
        st.warning(f"Deseja realmente excluir o registro **ID {row_id}**?")
        col_spacer1, col1, col2, col_spacer2 = st.columns([2, 1, 1, 2])
        with col1:
            if st.button("✅ Sim, quero excluir", key=f"confirm_{df_name}_{row_id}"):
                # Trabalhar SEMPRE no DF base do estado (sem colunas calculadas)
                base_df = st.session_state[df_name].copy()
                row_to_delete = base_df[base_df["ID"] == row_id].copy()
                base_df2 = base_df[base_df["ID"] != row_id]
                st.session_state[df_name] = base_df2
                save_csv(base_df2, csv_path)

                # Logs de exclusão
                registrar_log(
                    aba=ABA_MAP[df_name],
                    acao="Excluir",
                    item_id=row_id,
                    detalhe=f"Registro {row_id} excluído na aba {ABA_MAP[df_name]}."
                )

                # Exclusões em cascata + logs
                if df_name == "clientes_df":
                    vagas_rel = st.session_state.vagas_df[st.session_state.vagas_df["ClienteID"] == row_id]["ID"].tolist()
                    cand_rel = st.session_state.candidatos_df[st.session_state.candidatos_df["VagaID"].isin(vagas_rel)]["ID"].tolist()

                    st.session_state.vagas_df = st.session_state.vagas_df[st.session_state.vagas_df["ClienteID"] != row_id]
                    st.session_state.candidatos_df = st.session_state.candidatos_df[~st.session_state.candidatos_df["VagaID"].isin(vagas_rel)]
                    save_csv(st.session_state.vagas_df, VAGAS_CSV)
                    save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)

                    registrar_log(
                        aba="Vagas", acao="Excluir em Cascata",
                        detalhe=f"Cliente {row_id} removido. Vagas removidas: {vagas_rel}"
                    )
                    registrar_log(
                        aba="Candidatos", acao="Excluir em Cascata",
                        detalhe=f"Cliente {row_id} removido. Candidatos removidos: {cand_rel}"
                    )

                elif df_name == "vagas_df":
                    cand_rel = st.session_state.candidatos_df[st.session_state.candidatos_df["VagaID"] == row_id]["ID"].tolist()
                    st.session_state.candidatos_df = st.session_state.candidatos_df[st.session_state.candidatos_df["VagaID"] != row_id]
                    save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)
                    registrar_log(
                        aba="Candidatos", acao="Excluir em Cascata",
                        detalhe=f"Vaga {row_id} removida. Candidatos removidos: {cand_rel}"
                    )

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
def tela_login():
    st.title("🔒 Login - Parma Consultoria")

    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            if usuario == "admin" and senha == "Parma!123@":
                st.session_state.usuario = usuario
                st.session_state.logged_in = True
                st.session_state.page = "menu"
                registrar_log("Login", "Login", detalhe=f"Usuário {usuario} entrou no sistema.")
                st.success("✅ Login realizado com sucesso!")
                st.rerun()
            elif usuario == "andre" and senha == "And!123@":
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

                for campo, valor in novo.iloc[0].items():
                    if campo == "ID":
                        registrar_log("Clientes", "Criar", item_id=prox_id, campo=campo, valor_novo=valor, detalhe=f"Cliente criado (ID {prox_id}).")
                    else:
                        registrar_log("Clientes", "Criar", item_id=prox_id, campo=campo, valor_novo=valor, detalhe=f"Cliente criado (ID {prox_id}).")

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
                    "Data de Início": "",
                }])
                st.session_state.vagas_df = pd.concat([st.session_state.vagas_df, nova], ignore_index=True)
                save_csv(st.session_state.vagas_df, VAGAS_CSV)

                for campo, valor in nova.iloc[0].items():
                    registrar_log("Vagas", "Criar", item_id=prox_id, campo=campo, valor_novo=valor, detalhe=f"Vaga criada (ID {prox_id}).")

                st.success(f"✅ Vaga cadastrada com sucesso! ID: {prox_id}")
                st.rerun()

    st.subheader("📄 Vagas Cadastradas")
    df = st.session_state.vagas_df.copy()
    if df.empty:
        st.info("Nenhuma vaga cadastrada.")
    else:
        clientes_map = st.session_state.clientes_df.set_index("ID")["Cliente"].to_dict()
        df["Cliente"] = df["ClienteID"].map(lambda cid: clientes_map.get(cid, "Cliente não encontrado"))
        cols_show = ["ID", "Cliente", "Status", "Data de Abertura", "Cargo", "Salário 1", "Salário 2", "Recrutador", "Data de Início"]
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

    with st.form("form_candidato", enter_to_submit=False):
        vagas = st.session_state.vagas_df
        if vagas.empty:
            st.warning("⚠️ Cadastre uma Vaga antes de cadastrar Candidatos.")
            return
        vagas = vagas.merge(st.session_state.clientes_df[["ID", "Cliente"]], left_on="ClienteID", right_on="ID", suffixes=("", "_cliente"))
        vagas["Opcao"] = vagas.apply(lambda x: f"{x['ID']} - {x['Cliente']} - {x['Cargo']}", axis=1)
        vaga_sel = st.selectbox("Vaga *", options=vagas["Opcao"].tolist())
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
                    "Data de Início": "",
                }])
                st.session_state.candidatos_df = pd.concat([st.session_state.candidatos_df, novo], ignore_index=True)
                save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)

                for campo, valor in novo.iloc[0].items():
                    registrar_log("Candidatos", "Criar", item_id=prox_id, campo=campo, valor_novo=valor, detalhe=f"Candidato criado (ID {prox_id}).")

                # Lógica para atualizar a vaga para 'Ag. Inicio' ao cadastrar um candidato
                vagas_df = st.session_state.vagas_df.copy()
                idx_vaga = vagas_df[vagas_df["ID"] == vaga_id].index
                if not idx_vaga.empty:
                    antigo_status_vaga = vagas_df.loc[idx_vaga[0], "Status"]
                    if antigo_status_vaga != "Ag. Inicio" and antigo_status_vaga != "Fechada":
                        vagas_df.loc[idx_vaga, "Status"] = "Ag. Inicio"
                        st.info("🔄 Status da vaga alterado para 'Ag. Inicio' (novo candidato cadastrado).")
                        registrar_log(
                            aba="Vagas",
                            acao="Atualização Automática",
                            item_id=vaga_id,
                            campo="Status",
                            valor_anterior=antigo_status_vaga,
                            valor_novo="Ag. Inicio",
                            detalhe=f"Vaga alterada automaticamente ao cadastrar o candidato {prox_id}."
                        )
                    st.session_state.vagas_df = vagas_df
                    save_csv(vagas_df, VAGAS_CSV)
                
                st.success(f"✅ Candidato cadastrado com sucesso! ID: {prox_id}")
                st.rerun()

    st.subheader("📄 Candidatos Cadastrados")
    df = st.session_state.candidatos_df.copy()
    if df.empty:
        st.info("Nenhum candidato cadastrado.")
    else:
        vagas_df = st.session_state.vagas_df.merge(
            st.session_state.clientes_df[["ID", "Cliente"]], left_on="ClienteID", right_on="ID", suffixes=("", "_cliente")
        )
        vagas_map = vagas_df.set_index("ID")[["Cliente", "Cargo"]].to_dict(orient="index")

        df["Cliente"] = df["VagaID"].map(lambda vid: vagas_map.get(vid, {}).get("Cliente", "Cliente não encontrado"))
        df["Cargo"] = df["VagaID"].map(lambda vid: vagas_map.get(vid, {}).get("Cargo", "Cargo não encontrado"))

        cols_show = ["ID", "Cliente", "Cargo", "Nome", "Telefone", "Recrutador", "Status", "Data de Início"]
        download_button(df[cols_show], "candidatos.csv", "⬇️ Baixar Candidatos")
        show_table(df, cols_show, "candidatos_df", CANDIDATOS_CSV)

def tela_logs():
    st.header("📜 Logs do Sistema")
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
    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"
        st.rerun()

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

    if st.button("📜 Logs", use_container_width=True):
        st.session_state.page = "logs"
        st.rerun()

    st.divider()
    if st.button("🚪 Sair", use_container_width=True):
        registrar_log("Logout", "Logout", detalhe=f"Usuário {st.session_state.get('usuario','')} saiu do sistema.")
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()

# ==============================
# Roteamento
# ==============================
if st.session_state.page == "login":
    tela_login()
elif not st.session_state.logged_in:
    tela_login()
elif st.session_state.page == "menu":
    tela_menu()
elif st.session_state.page == "clientes":
    tela_clientes()
elif st.session_state.page == "vagas":
    tela_vagas()
elif st.session_state.page == "candidatos":
    tela_candidatos()
elif st.session_state.page == "logs":
    tela_logs()
