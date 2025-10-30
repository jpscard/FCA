import streamlit as st
import os
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from utils import validate_gemini_api_key
from view.main import extrair_dados_xml
from criptografia import SecureDataProcessor
from view.welcome import welcome_page
from view.login import login_page

st.set_page_config(layout="wide", page_title="Extrator de NF-e", page_icon="🧮")

# --- Barra Lateral Profissional (para a main_app) ---
def render_sidebar():
    st.sidebar.title("Análise Fiscal IA")
    st.sidebar.divider()

    # Painel de Status Dinâmico
with st.sidebar.expander("Status da Análise"):
    status_validador = "Concluído ✔️" if 'resultado_validador' in st.session_state else "Pendente"
    status_analista = "Concluído ✔️" if 'resultado_analista' in st.session_state else "Pendente"
    status_tributarista = "Concluído ✔️" if 'resultado_tributarista' in st.session_state else "Pendente"

    st.write(f"1. Validação: {status_validador}")
    st.write(f"2. Análise: {status_analista}")
    st.write(f"3. Cálculo: {status_tributarista}")
st.sidebar.divider()

# --- Página Principal (Upload e Extração) ---
def upload_page():
    render_sidebar() # Renderiza a sidebar apenas na main_app

    st.title("Extrator de Nota Fiscal Eletrônica (NF-e XML)")
    st.write(f"Bem-vindo, {st.session_state.get('user_name', '')}!")
    st.divider()

    st.header("1. Carregue a Nota Fiscal")
    uploaded_file = st.file_uploader("Selecione o arquivo XML da NF-e", type=["xml"])

    if uploaded_file is not None:
        # Limpa o estado de análises anteriores ao carregar um novo arquivo
        for key in ['resultado_validador', 'resultado_analista', 'resultado_tributarista']:
            if key in st.session_state:
                del st.session_state[key]

        xml_content = uploaded_file.read().decode("utf-8")
        st.session_state['uploaded_file_content'] = xml_content
        st.session_state['original_filename'] = uploaded_file.name

        cabecalho_df, produtos_df = extrair_dados_xml(xml_content)

        processor = SecureDataProcessor()
        cabecalho_criptografado = processor.encrypt_sensitive_data(cabecalho_df)
        produtos_criptografado = processor.encrypt_sensitive_data(produtos_df)
        
        # Armazena os dados na sessão para as outras páginas usarem
        st.session_state['cabecalho_df'] = cabecalho_df
        st.session_state['produtos_df'] = produtos_df
        st.session_state['cabecalho_criptografado'] = cabecalho_criptografado
        st.session_state['produtos_criptografado'] = produtos_criptografado

        st.success("Arquivo XML carregado e processado com sucesso!")
        st.info("Navegue para a página **'📊 Validador'** no menu à esquerda para iniciar a análise.")

        st.header("2. Visualize os Dados Extraídos")
        with st.expander("Dados Gerais da NF-e (Cabeçalho)", expanded=True):
            df_display = cabecalho_df.T.reset_index()
            df_display.columns = ["Campo", "Valor"]
            gb = GridOptionsBuilder.from_dataframe(df_display)
            grid_options = gb.build()
            AgGrid(df_display, gridOptions=grid_options, theme="streamlit", height=400)

        with st.expander("Produtos e Impostos Detalhados", expanded=True):
            gb = GridOptionsBuilder.from_dataframe(produtos_df)
            gb.configure_pagination(paginationPageSize=20)
            grid_options = gb.build()
            AgGrid(produtos_df, gridOptions=grid_options, theme="streamlit")

# --- Roteador Principal ---
if 'view' not in st.session_state:
    st.session_state['view'] = 'welcome'

if st.session_state['view'] == 'welcome':
    welcome_page()
elif st.session_state['view'] == 'login':
    login_page()
elif st.session_state['view'] == 'main_app':
    upload_page()