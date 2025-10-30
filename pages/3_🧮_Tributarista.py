import streamlit as st
import sys
import os

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.tributarista import calcular_delta_tributario

st.set_page_config(layout="wide", page_title="Tributarista Fiscal", page_icon="🧮")

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

st.title("Tributarista Fiscal")
st.write("Esta página executa o terceiro agente de IA para calcular o impacto financeiro das discrepâncias.")
st.divider()

# Verifica se a análise do Analista foi executada
if 'resultado_analista' not in st.session_state:
    st.warning("Por favor, execute a análise do 'Analista' primeiro.")
    st.stop()

# Se o resultado do tributarista já existir, mostra diretamente
if 'resultado_tributarista' in st.session_state:
    st.info("A análise do Tributarista já foi executada. Os resultados estão abaixo.")
    resultado_tributarista = st.session_state['resultado_tributarista']
else:
    st.info("A análise de discrepâncias foi concluída. Agora, vamos calcular o impacto financeiro.")
    # Botão para executar a análise
    if st.button("Calcular Delta Tributário e Multas", type="primary", width="stretch"):
        with st.spinner("Calculando impacto financeiro com o Agente Tributarista... Isso pode levar um momento."):
            try:
                resultado_tributarista = calcular_delta_tributario(
                    st.session_state['cabecalho_criptografado'],
                    st.session_state['produtos_criptografado'],
                    st.session_state['resultado_analista'],
                    st.session_state['resultado_validador']
                )
                st.session_state['resultado_tributarista'] = resultado_tributarista
                st.rerun() # Recarrega a página para mostrar os resultados
            except Exception as e:
                st.error(f"Ocorreu um erro ao executar o tributarista: {e}")
                st.stop()
    else:
        st.info("Clique no botão acima para que o Agente Tributarista calcule as diferenças de impostos e multas potenciais.")
        st.stop()

# --- Exibição dos Resultados ---
st.header("Relatório de Cálculo Tributário")

if resultado_tributarista.get('status') in ['sucesso', 'parcial']:
    st.success("Cálculo de impacto financeiro concluído!")

    if resultado_tributarista.get('relatorio_hibrido'):
        st.markdown(resultado_tributarista['relatorio_hibrido'])
    
    st.info("Para um resumo de toda a análise, navegue para a página **'📈 Dashboard'**.")

else:
    st.error("Ocorreu um erro durante a análise do Tributarista.")
    if resultado_tributarista.get('relatorio_hibrido'):
        st.write(resultado_tributarista['relatorio_hibrido'])