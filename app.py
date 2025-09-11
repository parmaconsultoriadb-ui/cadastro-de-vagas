import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ==============================
# Configuração da página
# ==============================
st.set_page_config(page_title="Parma Consultoria", layout="wide")

# ==============================
# Arquivos CSV
# ==============================
CLIENTES_CSV = "clientes.csv"
VAGAS_CSV = "vagas.csv"
CANDIDATOS_CSV = "candidatos.csv"
USUARIOS_CSV = "usuarios.csv"

# ==============================
# Funções auxiliares
# ==============================
def load_csv(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    else:
        return pd.DataFrame(columns=columns)

def save_csv(df, file):
    df.to_csv(file, index=False)

def registrar_log(aba, acao, item_id, campo, valor_antigo, valor_novo, detalhe=""):
    log = f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] {aba} | {acao} | ID {item_id} | {campo}: {valor_antigo} -> {valor_novo} | {detalhe}"
    st.session_state.setdefault("logs", []).append(log)
    print(log)

# ==============================
# Carregamento de dados
# ==============================
st.session_state.clientes_df = load_csv(CLIENTES_CSV, ["ID", "Nome", "Contato"])
st.session_state.vagas_df = load_csv(VAGAS_CSV, ["ID", "Status", "Cliente", "Cargo", "Salario 1", "Salario 2", "Descrição / Observação"])
st.session_state.candidatos_df = load_csv(CANDIDATOS_CSV, ["ID", "Nome", "Status", "Cliente", "Cargo", "Data de Início"])
st.session_state.usuarios_df = load_csv(USUARIOS_CSV, ["Usuário", "Senha", "Páginas"])

# ==============================
# Função de edição de registros
# ==============================
def show_edit_form(df_name, record):
    st.subheader(f"Editar {df_name[:-3].capitalize()}")
    df = st.session_state[df_name]
    idx0 = df[df["ID"] == record["ID"]].index[0]
    
    new_data = {}
    for column in df.columns:
        if column == "ID":
            st.text(f"{column}: {df.at[idx0, column]}")
            new_data[column] = df.at[idx0, column]
        else:
            new_data[column] = st.text_input(column, value=str(df.at[idx0, column]))
    
    if st.button("Salvar Alterações"):
        for column, value in new_data.items():
            df.at[idx0, column] = value

        # Lógica para candidatos
        if df_name == "candidatos_df":
            candidato_id = record.get("ID")
            novo_status = new_data.get("Status")
            data_inicio_str = new_data.get("Data de Início")
            data_inicio = None
            if data_inicio_str:
                try:
                    data_inicio = datetime.strptime(data_inicio_str, "%d/%m/%Y").date()
                except:
                    pass
            vagas_df = st.session_state.vagas_df
            vaga_match = vagas_df[(vagas_df["Cliente"] == df.at[idx0, "Cliente"]) & (vagas_df["Cargo"] == df.at[idx0, "Cargo"])]
            if not vaga_match.empty:
                v_idx = vaga_match.index[0]
                if novo_status == "Validado" and data_inicio is not None:
                    if vagas_df.at[v_idx, "Status"] == "Aberta":
                        registrar_log(
                            aba="Vagas",
                            acao="Atualização Automática",
                            item_id=vagas_df.at[v_idx, "ID"],
                            campo="Status",
                            valor_antigo=vagas_df.at[v_idx, "Status"],
                            valor_novo="Ag. Inicio",
                            detalhe=f"Candidato {candidato_id} validado com Data de Início"
                        )
                        vagas_df.at[v_idx, "Status"] = "Ag. Inicio"
                        st.info("Status da vaga atualizado para 'Ag. Inicio'.")
        
        st.session_state[df_name] = df
        st.success(f"{df_name[:-3].capitalize()} atualizado com sucesso!")

# ==============================
# Login
# ==============================
def login():
    st.title("Login - Parma Consultoria")
    usuario_input = st.text_input("Usuário")
    senha_input = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user_row = st.session_state.usuarios_df[(st.session_state.usuarios_df["Usuário"] == usuario_input) &
                                                (st.session_state.usuarios_df["Senha"] == senha_input)]
        if not user_row.empty:
            st.session_state["usuario_logado"] = usuario_input
            st.session_state["paginas_permitidas"] = user_row.iloc[0]["Páginas"].split(",")
            st.success(f"Bem-vindo {usuario_input}!")
        else:
            st.error("Usuário ou senha incorretos.")

# ==============================
# App Principal
# ==============================
if "usuario_logado" not in st.session_state:
    login()
else:
    st.sidebar.title(f"Usuário: {st.session_state['usuario_logado']}")
    pagina = st.sidebar.radio("Navegar", ["Vagas", "Candidatos", "Usuários"])
    
    if pagina not in st.session_state["paginas_permitidas"]:
        st.warning("⚠️ Você não tem permissão para acessar esta página.")
    else:
        if pagina == "Vagas":
            st.header("Vagas")
            df = st.session_state.vagas_df
            for idx, row in df.iterrows():
                st.write(f"ID: {row['ID']} | Status: {row['Status']} | Cliente: {row['Cliente']} | Cargo: {row['Cargo']}")
                st.write(f"Descrição / Observação: {row['Descrição / Observação']}")
                if st.button(f"Editar Vaga {row['ID']}", key=f"vaga_{row['ID']}"):
                    show_edit_form("vagas_df", row)
            if st.button("Salvar Vagas CSV"):
                save_csv(st.session_state.vagas_df, VAGAS_CSV)
                st.success("Vagas salvas com sucesso!")

        elif pagina == "Candidatos":
            st.header("Candidatos")
            df = st.session_state.candidatos_df
            for idx, row in df.iterrows():
                st.write(f"ID: {row['ID']} | Nome: {row['Nome']} | Status: {row['Status']} | Cliente: {row['Cliente']} | Cargo: {row['Cargo']} | Data de Início: {row['Data de Início']}")
                if st.button(f"Editar Candidato {row['ID']}", key=f"cand_{row['ID']}"):
                    show_edit_form("candidatos_df", row)
            if st.button("Salvar Candidatos CSV"):
                save_csv(st.session_state.candidatos_df, CANDIDATOS_CSV)
                st.success("Candidatos salvos com sucesso!")

        elif pagina == "Usuários":
            st.header("Usuários")
            st.dataframe(st.session_state.usuarios_df)
            st.info("Para editar usuários, modifique diretamente o CSV ou implemente edição nesta interface.")
            if st.button("Salvar Usuários CSV"):
                save_csv(st.session_state.usuarios_df, USUARIOS_CSV)
                st.success("Usuários salvos com sucesso!")
