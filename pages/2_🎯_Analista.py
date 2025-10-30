import streamlit as st
import sys
import os

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.analista import analisar_discrepancias_nfe

st.set_page_config(layout="wide", page_title="Analista Fiscal", page_icon="🎯")

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

st.title("Analista Fiscal")
st.write("Esta página executa o segundo agente de IA para analisar as discrepâncias e propor soluções.")
st.divider()

# Verifica se a análise do Validador foi executada
if 'resultado_validador' not in st.session_state:
    st.warning("Por favor, execute a análise do 'Validador' primeiro.")
    st.stop()

resultado_validador = st.session_state['resultado_validador']
discrepancias = resultado_validador.get('discrepancias', [])

# Se não houver discrepâncias, não há o que analisar
if not discrepancias:
    st.success("✅ Nenhuma discrepância foi encontrada pelo Validador. Não é necessária uma análise mais profunda.")
    st.stop()

# Se o resultado do analista já existir, mostra diretamente
if 'resultado_analista' in st.session_state:
    st.info("A análise do Analista já foi executada. Os resultados estão abaixo.")
    resultado_analista = st.session_state['resultado_analista']
else:
    st.warning(f"Foram encontradas {len(discrepancias)} discrepância(s) pelo Validador.")
    # Botão para executar a análise
    if st.button("Analisar Discrepâncias com IA", type="primary", width="stretch"):
        with st.spinner("Analisando discrepâncias com o Agente Analista... Isso pode levar um momento."):
            try:
                resultado_analista = analisar_discrepancias_nfe(
                    st.session_state['cabecalho_criptografado'],
                    st.session_state['produtos_criptografado'],
                    resultado_validador
                )
                st.session_state['resultado_analista'] = resultado_analista
                st.rerun() # Recarrega a página para mostrar os resultados
            except Exception as e:
                st.error(f"Ocorreu um erro ao executar o analista: {e}")
                st.stop()
    else:
        st.info("Clique no botão acima para que o Agente Analista investigue as discrepâncias e proponha soluções.")
        st.stop()

# --- Exibição dos Resultados ---
st.header("Relatório de Análise de Discrepâncias")

if resultado_analista.get('status') in ['sucesso', 'parcial']:
    st.success("Análise de discrepâncias concluída!")

    if resultado_analista.get('relatorio_final'):
        st.markdown(resultado_analista['relatorio_final'])
    
    st.info("Para um cálculo detalhado do impacto financeiro, navegue para a página **'🧮 Tributarista'**.")

else:
    st.error("Ocorreu um erro durante a análise do Analista.")
    if resultado_analista.get('relatorio_final'):
        st.write(resultado_analista['relatorio_final'])