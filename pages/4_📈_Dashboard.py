import streamlit as st
import sys
import os

# Adiciona o diretório raiz ao sys.path para garantir que as importações funcionem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.set_page_config(layout="wide", page_title="Dashboard Final", page_icon="📈")

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

st.title("Dashboard Final da Análise")
st.write("Esta página consolida os resultados de todos os agentes, fornecendo uma visão geral do diagnóstico fiscal.")
st.divider()

# Verifica se todas as análises foram concluídas
required_keys = ['resultado_validador', 'resultado_analista', 'resultado_tributarista']
if not all(key in st.session_state for key in required_keys):
    st.warning("Por favor, complete todas as etapas da análise (Validador, Analista e Tributarista) para ver o dashboard consolidado.")
    st.stop()

# Carrega os resultados da sessão
res_validador = st.session_state['resultado_validador']
res_analista = st.session_state['resultado_analista']
res_tributarista = st.session_state['resultado_tributarista']

# --- Exibição dos Resultados Consolidados ---
st.header("KPIs Principais da Análise Fiscal")

# Métricas
col1, col2, col3, col4 = st.columns(4)

with col1:
    num_discrepancias = len(res_validador.get('discrepancias', []))
    st.metric("Discrepâncias Encontradas", num_discrepancias)

with col2:
    num_oportunidades = len(res_validador.get('oportunidades', []))
    st.metric("Oportunidades Identificadas", num_oportunidades)

with col3:
    total_exposicao = res_tributarista.get('analise_riscos', {}).get('valor_total_exposicao') or 0
    st.metric("Valor Total em Risco", f"R$ {total_exposicao:,.2f}")

with col4:
    risco_autuacao = res_tributarista.get('analise_riscos', {}).get('risco_autuacao', 'N/A')
    st.metric("Nível de Risco", risco_autuacao)

st.divider()

# Resumos e Ações
col1, col2 = st.columns(2)

with col1:
    st.subheader("Resumo Executivo da Análise")
    if res_analista.get('resumo_executivo'):
        st.markdown(res_analista['resumo_executivo'])
    else:
        st.info("Nenhum resumo executivo gerado pelo Analista.")

with col2:
    st.subheader("Plano de Ação Imediato")
    plano_acao = res_analista.get('plano_acao_consolidado', {})
    if plano_acao.get('acoes_imediatas'):
        for acao in plano_acao['acoes_imediatas']:
            st.write(f"- {acao}")
    else:
        st.info("Nenhuma ação imediata foi recomendada.")

st.divider()

# Downloads
st.header("Downloads dos Relatórios e Arquivo Original")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if res_validador:
        validador_md = res_validador.get('resumo_dropdown', 'Nenhum relatório disponível.')
        st.download_button(
            label="Baixar Relatório do Validador",
            data=validador_md,
            file_name="relatorio_validador.md",
            mime="text/markdown",
            width="stretch"
        )

with col2:
    if res_analista:
        analista_md = res_analista.get('relatorio_final', 'Nenhum relatório disponível.')
        st.download_button(
            label="Baixar Relatório do Analista",
            data=analista_md,
            file_name="relatorio_analista.md",
            mime="text/markdown",
            width="stretch"
        )

with col3:
    if res_tributarista:
        tributarista_md = res_tributarista.get('relatorio_hibrido', 'Nenhum relatório disponível.')
        st.download_button(
            label="Baixar Relatório do Tributarista",
            data=tributarista_md,
            file_name="relatorio_tributarista.md",
            mime="text/markdown",
            width="stretch"
        )

with col4: 
    if 'uploaded_file_content' in st.session_state:
        xml_content = st.session_state['uploaded_file_content']
        st.download_button(
            label="Baixar XML Original",
            data=xml_content,
            file_name=st.session_state.get('original_filename', 'nfe_original.xml'),
            mime="application/xml",
            width="stretch"
        )