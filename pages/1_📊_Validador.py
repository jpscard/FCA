import streamlit as st
import sys
import os

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.validador import buscar_regras_fiscais_nfe

st.set_page_config(layout="wide", page_title="Validador Fiscal", page_icon="📊")

# --- Barra Lateral Profissional ---
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

st.title("Validador Fiscal")
st.write("Esta página executa o primeiro agente de IA para validar a conformidade fiscal da NF-e.")
st.divider()

# Verifica se os dados da NF-e estão na sessão
if 'cabecalho_criptografado' not in st.session_state or 'produtos_criptografado' not in st.session_state:
    st.warning("Por favor, carregue um arquivo XML na página principal primeiro.")
    st.stop()

# Se o resultado do validador já existir, mostra diretamente
if 'resultado_validador' in st.session_state:
    st.info("A análise do Validador já foi executada. Os resultados estão abaixo.")
    resultado = st.session_state['resultado_validador']
else:
    # Botão para executar a análise
    if st.button("Executar Análise do Validador", type="primary", width="stretch"):
        with st.spinner("Analisando conformidade fiscal com o Agente Validador... Isso pode levar um momento."):
            try:
                resultado = buscar_regras_fiscais_nfe(
                    st.session_state['cabecalho_criptografado'], 
                    st.session_state['produtos_criptografado']
                )
                st.session_state['resultado_validador'] = resultado
                st.rerun() # Recarrega a página para mostrar os resultados
            except Exception as e:
                st.error(f"Ocorreu um erro ao executar o validador: {e}")
                st.stop()
    else:
        st.info("Clique no botão acima para iniciar a análise fiscal da NF-e carregada.")
        st.stop()

# --- Exibição dos Resultados ---
st.header("Resultado da Análise de Conformidade")

if resultado.get('status') == 'sucesso' or resultado.get('status') == 'parcial':
    st.success(f"Análise concluída! {resultado.get('produtos_analisados', 0)} produtos analisados.")

    if resultado.get('resumo_dropdown'):
        with st.expander("Ver Resumo da Análise", expanded=True):
            st.markdown(resultado['resumo_dropdown'])
    
    st.info("Para uma análise mais profunda das discrepâncias, navegue para a página **'🎯 Analista'**.")

else:
    st.error("Ocorreu um erro durante a análise do Validador.")
    if resultado.get('resumo_dropdown'):
        st.write(resultado['resumo_dropdown'])