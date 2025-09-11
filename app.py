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

# Carregar DataFrames na sessão
if "clientes_df" not in st.session_state:
    st.session_state.clientes_df = load_csv(CLIENTES_CSV, CLIENTES_COLS)
if "vagas_df" not in st.session_state:
    st.session_state.vagas_df = load_csv(VAGAS_CSV, VAGAS_COLS)
if "candidatos_df" not in st.session_state:
    st.session_state.candidatos_df = load_csv(CANDIDATOS_CSV, CANDIDATOS_COLS)

# ==============================
# Estilo
# ==============================
st.markdown("""
<style>
/* estilo dos botões e tabela omitido para não alongar */
</style>
""", unsafe_allow_html=True)

# ==============================
# UI helpers
# ==============================
def download_button(df, filename, label="⬇️ Baixar CSV"):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv, file_name=filename, mime="text/csv", use_container_width=True)

def show_table(df, cols, df_name, csv_path):
    # mesmo show_table do seu código original
    pass

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
                            registrar_log(aba=df_name.replace('_df','').capitalize(), acao="Editar", item_id=record["ID"], campo=c, valor_anterior=antigo, valor_novo=novo)
                        df.at[idx0, c] = novo

                # ======= AQUI INSERIMOS A VALIDAÇÃO DE DATA DE INÍCIO PARA ALTERAR STATUS =======
                if df_name == "candidatos_df":
                    status_candidato = new_data.get("Status")
                    data_inicio_candidato = new_data.get("Data de Início")
                    cliente_candidato = new_data.get("Cliente")
                    cargo_candidato = new_data.get("Cargo")
                    if status_candidato == "Validado" and data_inicio_candidato:
                        vagas_df = st.session_state["vagas_df"]
                        vaga_match = vagas_df[(vagas_df["Cliente"] == cliente_candidato) &
                                              (vagas_df["Cargo"] == cargo_candidato)]
                        if not vaga_match.empty:
                            v_idx = vaga_match.index[0]
                            if vagas_df.at[v_idx, "Status"] == "Aberta":
                                vagas_df.at[v_idx, "Status"] = "Ag. Inicio"
                                save_csv(vagas_df, VAGAS_CSV)
                                registrar_log(aba="Vagas", acao="Status Alterado", item_id=vagas_df.at[v_idx,"ID"], campo="Status", valor_anterior="Aberta", valor_novo="Ag. Inicio", detalhe=f"Candidato {new_data.get('Nome')} validado com Data de Início")

                st.session_state[df_name] = df
                save_csv(df, csv_path)
                st.success("✅ Alterações salvas com sucesso!")
                st.session_state.edit_mode = None
                st.session_state.edit_record = {}

# ==============================
# Tela de login
# ==============================
def login_page():
    st.title("Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user = USUARIOS.get(username)
        if user and user["senha"] == password:
            st.session_state.logged_in = True
            st.session_state.usuario = username
            st.session_state.permissoes = user["permissoes"]
            st.session_state.page = "menu"
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos")

# ==============================
# Menu principal
# ==============================
def main_menu():
    st.title("Menu Principal")
    if "menu" in st.session_state.permissoes:
        st.button("Clientes", on_click=lambda: st.session_state.update({"page":"clientes"}))
    if "vagas" in st.session_state.permissoes:
        st.button("Vagas", on_click=lambda: st.session_state.update({"page":"vagas"}))
    if "candidatos" in st.session_state.permissoes:
        st.button("Candidatos", on_click=lambda: st.session_state.update({"page":"candidatos"}))
    if "logs" in st.session_state.permissoes:
        st.button("Logs", on_click=lambda: st.session_state.update({"page":"logs"}))
    st.button("Sair", on_click=logout)

# ==============================
# Logout
# ==============================
def logout():
    st.session_state.logged_in = False
    st.session_state.usuario = ""
    st.session_state.permissoes = []
    st.session_state.page = "login"
    st.experimental_rerun()

# ==============================
# Main
# ==============================
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.page == "menu":
        main_menu()
    elif st.session_state.page == "clientes":
        show_table(st.session_state.clientes_df, CLIENTES_COLS, "clientes_df", CLIENTES_CSV)
    elif st.session_state.page == "vagas":
        show_table(st.session_state.vagas_df, VAGAS_COLS, "vagas_df", VAGAS_CSV)
    elif st.session_state.page == "candidatos":
        show_table(st.session_state.candidatos_df, CANDIDATOS_COLS, "candidatos_df", CANDIDATOS_CSV)
    elif st.session_state.page == "logs":
        show_table(carregar_logs(), LOGS_COLS, "logs_df", LOGS_CSV)
