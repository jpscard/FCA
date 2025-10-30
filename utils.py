# --- Importações Essenciais ---
import streamlit as st
import pandas as pd
import re
import google.generativeai as genai
from google.api_core import exceptions
import os

# --- Funções de Validação e Obtenção de Modelos ---
def validate_gemini_api_key(api_key):
    try:
        genai.configure(api_key=api_key)
        genai.list_models()
        return True
    except exceptions.PermissionDenied:
        st.error("Chave de API do Gemini inválida ou sem permissão.")
        return False
    except Exception as e:
        st.error(f"Ocorreu um erro ao validar a chave de API: {e}")
        return False

def get_gemini_models():
    try:
        return [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except Exception as e:
        st.warning(f"Não foi possível buscar modelos Gemini. Verifique a API Key. Erro: {e}")
        return []

# --- Funções de Consulta à Base de Conhecimento (NCM) ---
@st.cache_data
def carregar_base_ncm():
    """Carrega a planilha de NCM para um DataFrame em cache."""
    caminho_planilha = os.path.join(os.path.dirname(__file__), 'referencias', 'Tabela_NCM_Vigente_20251024.xlsx')
    try:
        df = pd.read_excel(caminho_planilha, usecols=[0, 1], dtype={'Código NCM': str})
        df.columns = ['Código NCM', 'Descrição NCM']
        df['Código NCM'] = df['Código NCM'].str.replace('.', '', regex=False)
        return df
    except FileNotFoundError:
        st.error(f"A planilha de NCM não foi encontrada em '{caminho_planilha}'. Verifique o caminho e o nome do arquivo.")
        return None
    except Exception as e:
        st.error(f"Erro ao ler a planilha de NCM: {e}")
        return None

def consultar_ncm(ncm_codigo, base_ncm_df):
    """Consulta a descrição de um NCM na base de conhecimento."""
    if base_ncm_df is None:
        return "Base de NCM não carregada."
    
    try:
        # Limpa o código NCM para garantir a busca correta
        ncm_codigo_limpo = str(ncm_codigo).strip().replace('.', '')
        
        resultado = base_ncm_df[base_ncm_df['Código NCM'] == ncm_codigo_limpo]
        
        if not resultado.empty:
            return resultado['Descrição NCM'].iloc[0]
        else:
            return "NCM não encontrado na base de conhecimento."
    except Exception as e:
        return f"Erro ao consultar NCM: {e}"