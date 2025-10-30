import streamlit as st

def welcome_page():
    st.set_page_config(layout="centered", page_title="Bem-vindo")
    
    st.title("Bem-vindo ao Sistema Tributário IA")
    st.divider()
    st.subheader("Uma aplicação para análise fiscal inteligente de Notas Fiscais Eletrônicas.")
    st.write("Navegue pelas etapas de validação, análise e cálculo para obter um diagnóstico fiscal completo da sua NF-e.")
    st.divider()

    if st.button("Iniciar Análise", type="primary", width="stretch"):
        st.session_state['view'] = 'login'
        st.rerun()
