import streamlit as st
import os
import sys

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import validate_gemini_api_key

def login_page():
    st.set_page_config(layout="centered", page_title="Login")

    st.title("Login do Sistema")
    
    name = st.text_input("Seu Nome", key="login_name")
    password = st.text_input("Insira sua API Key do Gemini", type="password", key="login_password")
    
    if st.button("Login", width="stretch", type="primary"):
        if name and password:
            if validate_gemini_api_key(password):
                st.session_state["logged_in"] = True
                st.session_state["user_name"] = name
                os.environ["GOOGLE_API_KEY"] = password
                st.session_state['view'] = 'main_app'
                st.success("Login bem-sucedido!")
                st.rerun()
            else:
                st.error("API Key do Gemini inválida ou sem permissão.")
        else:
            st.error("Por favor, insira seu nome e a API Key.")
