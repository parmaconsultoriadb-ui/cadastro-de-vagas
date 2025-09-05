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
            elif c == "Data de Fechamento" and df_name == "vagas_df":
                valor_atual = record.get(c, "")
                try:
                    valor_atual_date = datetime.strptime(valor_atual, "%d/%m/%Y").date() if valor_atual else None
                except:
                    valor_atual_date = None
                data_selecionada = st.date_input(c, value=valor_atual_date or date.today())
                new_data[c] = data_selecionada.strftime("%d/%m/%Y")
            else:
                new_data[c] = st.text_input(c, value=record.get(c, ""))

        submitted = st.form_submit_button("Salvar Alterações", use_container_width=True)
        if submitted:
            df = st.session_state[df_name].copy()
            idx = df[df["ID"] == record["ID"]].index
            if not idx.empty:
                for c in cols:
                    antigo = df.loc[idx[0], c]
                    novo = new_data[c]
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

            if df_name == "candidatos_df":
                vaga_id = record.get("VagaID")
                vagas_df = st.session_state.vagas_df.copy()
                idx_vaga = vagas_df[vagas_df["ID"] == vaga_id].index
                if not idx_vaga.empty:
                    if new_data.get("Status") == "Validado":
                        antigo_status_vaga = vagas_df.loc[idx_vaga[0], "Status"]
                        vagas_df.loc[idx_vaga, "Status"] = "Ag. Inicio"
                        st.success("🔄 Vaga atualizada para 'Ag. Inicio'!")
                        if antigo_status_vaga != "Ag. Inicio":
                            registrar_log(
                                aba="Vagas",
                                acao="Atualização Automática",
                                item_id=vaga_id,
                                campo="Status",
                                valor_anterior=antigo_status_vaga,
                                valor_novo="Ag. Inicio",
                                detalhe=f"Vaga alterada automaticamente ao validar candidato {record['ID']}."
                            )
                    elif record.get("Status") == "Validado" and new_data.get("Status") != "Validado":
                        antigo_status_vaga = vagas_df.loc[idx_vaga[0], "Status"]
                        vagas_df.loc[idx_vaga, "Status"] = "Aberta"
                        st.info("🔄 Vaga reaberta automaticamente!")
                        if antigo_status_vaga != "Aberta":
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

# (demais funções tela_clientes, tela_vagas, tela_candidatos, tela_logs, tela_menu permanecem iguais à sua versão atual,
# sem mudanças além do show_edit_form já atualizado acima)

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
