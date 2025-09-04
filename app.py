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
if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = None  # armazena o registro pendente de exclusão

# Definição das colunas
CLIENTES_COLS = ["ID", "Data", "Nome", "Cliente", "Cidade", "UF", "Telefone", "E-mail"]
VAGAS_COLS = ["ID", "Status", "Data de Abertura", "Cliente", "Cargo", "Salário 1", "Salário 2", "Recrutador", "Data de Fechamento"]
CANDIDATOS_COLS = ["ID", "Cliente", "Cargo", "Nome", "Telefone", "Recrutador"]

# Carregar CSVs
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
    /* Botões customizados */
    .btn-editar {
        background-color: royalblue !important;
        color: white !important;
        border-radius: 6px;
        font-weight: bold;
    }
    .btn-excluir {
        background-color: crimson !important;
        color: white !important;
        border-radius: 6px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
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
                st.success("✅ Registro atualizado com sucesso!")
                st.session_state.edit_mode = None
                st.session_state.edit_record = {}
                st.rerun()

    if st.button("❌ Cancelar Edição", use_container_width=True):
        st.session_state.edit_mode = None
        st.session_state.edit_record = {}
        st.rerun()

def show_table(df, cols, df_name, csv_path):
    # Cabeçalho estilizado
    cols_ui = st.columns(len(cols) + 2)
    for i, c in enumerate(cols):
        cols_ui[i].markdown(
            f"<div style='background-color:#f0f0f0; padding:6px; font-weight:bold; color:black; border-radius:4px; text-align:center;'>{c}</div>",
            unsafe_allow_html=True
        )
    cols_ui[-2].markdown("<div style='background-color:#f0f0f0; padding:6px; font-weight:bold; color:black; text-align:center;'>Editar</div>", unsafe_allow_html=True)
    cols_ui[-1].markdown("<div style='background-color:#f0f0f0; padding:6px; font-weight:bold; color:black; text-align:center;'>Excluir</div>", unsafe_allow_html=True)

    # Linhas da tabela
    for idx, row in df.iterrows():
        bg_color = "#ffffff" if idx % 2 == 0 else "#f9f9f9"
        cols_ui = st.columns(len(cols) + 2)
        for i, c in enumerate(cols):
            cols_ui[i].markdown(f"<div style='background-color:{bg_color}; padding:6px; text-align:center; color:black;'>{row[c]}</div>", unsafe_allow_html=True)

        with cols_ui[-2]:
            btn = st.button("Editar", key=f"edit_{df_name}_{row['ID']}", use_container_width=True)
            if btn:
                st.session_state.edit_mode = df_name
                st.session_state.edit_record = row.to_dict()
                st.rerun()
            st.markdown(f"<script>document.querySelector('button[key=\"edit_{df_name}_{row['ID']}\"]').classList.add('btn-editar');</script>", unsafe_allow_html=True)

        with cols_ui[-1]:
            btn = st.button("Excluir", key=f"del_{df_name}_{row['ID']}", use_container_width=True)
            if btn:
                st.session_state.delete_confirm = {"df_name": df_name, "csv_path": csv_path, "id": row["ID"]}
                st.rerun()
            st.markdown(f"<script>document.querySelector('button[key=\"del_{df_name}_{row['ID']}\"]').classList.add('btn-excluir');</script>", unsafe_allow_html=True)

    st.divider()

    # Aviso de confirmação de exclusão (sem modal)
    if st.session_state.delete_confirm and st.session_state.delete_confirm["df_name"] == df_name:
        id_to_delete = st.session_state.delete_confirm["id"]
        st.warning(f"⚠️ Tem certeza que deseja excluir o registro **ID {id_to_delete}**?")
        colA, colB = st.columns(2)
        with colA:
            if st.button("✅ Confirmar Exclusão", key=f"confirm_{id_to_delete}", use_container_width=True):
                df2 = df[df["ID"] != id_to_delete]
                st.session_state[df_name] = df2
                save_csv(df2, csv_path)
                st.success(f"Registro {id_to_delete} excluído com sucesso!")
                st.session_state.delete_confirm = None
                st.rerun()
        with colB:
            if st.button("❌ Cancelar", key=f"cancel_{id_to_delete}", use_container_width=True):
                st.session_state.delete_confirm = None
                st.info("Exclusão cancelada.")
                st.rerun()

def download_button(df, filename, label="⬇️ Baixar CSV"):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv, file_name=filename, mime="text/csv", use_container_width=True)

# ==============================
# Telas (Clientes, Vagas, Candidatos)
# ==============================
def tela_clientes():
    if st.session_state.edit_mode == "clientes_df":
        st.markdown("### ✏️ Editar Cliente")
        show_edit_form("clientes_df", CLIENTES_COLS, CLIENTES_CSV)
        return
    if st.button("⬅️ Voltar ao Menu", use_container_width=True):
        st.session_state.page = "menu"; st.rerun()
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
                novo = pd.DataFrame([{"ID": str(prox_id), "Data": data_hoje, "Nome": nome, "Cliente": cliente, "Cidade": cidade, "UF": uf.upper(), "Telefone": telefone, "E-mail": email}])
                st.session_state.clientes_df = pd.concat([st.session_state.clientes_df, novo], ignore_index=True)
                save_csv(st.session_state.clientes_df, CLIENTES_CSV)
                st.success(f"✅ Cliente cadastrado com sucesso! ID: {prox_id}")
                st.rerun()
    st.subheader("📄 Clientes Cadastrados")
    df = st.session_state.clientes_df
    if df.empty: st.info("Nenhum cliente cadastrado.")
    else:
        filtro = st.text_input("🔎 Buscar por Cliente")
        df_filtrado = df[df["Cliente"].str.contains(filtro, case=False, na=False)] if filtro_
