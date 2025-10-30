"""
Validador Fiscal com LangChain
Sistema de análise fiscal que usa LLM para comparar dados da NFe com banco de regras fiscal.
Utiliza LangChain para orquestração e análise inteligente de conformidade tributária.
"""

import os
import json
import pandas as pd
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from rag_system import RAGSystem

# Import do processador de criptografia e das novas funções de NCM
try:
    from criptografia import SecureDataProcessor
    from utils import carregar_base_ncm, consultar_ncm
except Exception:
    class SecureDataProcessor:
        def __init__(self):
            pass
        def decrypt_sensitive_data(self, df: pd.DataFrame, fields_to_decrypt=None) -> pd.DataFrame:
            return df
    def carregar_base_ncm():
        return None
    def consultar_ncm(ncm_codigo, base_ncm_df):
        return "Erro no import do utils."


class ValidadorFiscal:
    """
    Validador fiscal que usa LangChain e LLM para análise inteligente de conformidade.
    Compara dados da NFe com banco de regras fiscais usando AI.
    """

    def __init__(self):
        """Inicializa o validador fiscal com LangChain"""
        self.processor = SecureDataProcessor()
        self.base_ncm = carregar_base_ncm()  # Carrega a base de NCM na inicialização
        self.llm = None
        self.chain = None
        self.rag_system = RAGSystem() # Inicializa o sistema RAG
        self.rag_system.initialize_vectorstore() # Carrega o vectorstore
        
        # Modelos disponíveis para fallback
        self.modelos_disponiveis = [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro", 
            "gemini-pro",
            "gemini-1.0-pro"
        ]
        
        # Inicializar LLM
        self._inicializar_llm_chain()


    def _inicializar_llm_chain(self):
        """Inicializa a LLM e cria a chain do LangChain"""
        try:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise Exception("GOOGLE_API_KEY não configurada")

            # Garantir versão da API
            os.environ.setdefault("GOOGLE_API_VERSION", "v1")

            # Testar modelos disponíveis
            for modelo in self.modelos_disponiveis:
                try:
                    test_llm = ChatGoogleGenerativeAI(
                        model=modelo,
                        google_api_key=api_key,
                        temperature=0.1,
                        max_output_tokens=8192
                    )
                    
                    # Teste simples
                    response = test_llm.invoke("OK")
                    if response and hasattr(response, 'content') and response.content:
                        self.llm = test_llm
                        print(f"✅ LLM inicializada: {modelo}")
                        break
                        
                except Exception as e:
                    print(f"⚠️ Modelo {modelo} indisponível: {str(e)[:100]}")
                    continue

            if not self.llm:
                raise Exception("Nenhum modelo Gemini disponível")

            # Criar parser e chain
            self._criar_chain()
            
        except Exception as e:
            print(f"❌ Erro ao inicializar LLM: {e}")
            self.llm = None
            self.chain = None

    def _criar_chain(self):
        """Cria a chain do LangChain com prompt estruturado e enriquecido com NCM."""
        
        # Template do prompt para análise fiscal
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", '''Você é um especialista em análise fiscal brasileira com profundo conhecimento em tributação de NFe.

Sua tarefa é analisar os dados da Nota Fiscal Eletrônica (NFe) e identificar:
1. OPORTUNIDADES de otimização fiscal.
2. DISCREPÂNCIAS ou não conformidades.

Para isso, você deve comparar os dados da NFe com duas fontes de conhecimento:
- BANCO DE REGRAS FISCAIS: Contém alíquotas, CFOPs e regras gerais.
- BASE DE CONHECIMENTO NCM: Contém a descrição oficial para cada código NCM.

INSTRUÇÕES IMPORTANTES:
- Analise TODOS os produtos do DataFrame.
- **Validação de NCM**: Compare a 'Descrição do Produto' (da NFe) com a 'Descrição NCM (Oficial)' (da base de conhecimento). Se forem muito diferentes, aponte como uma discrepância de 'Classificação Fiscal Incorreta'.
- Compare as alíquotas aplicadas na NFe com as do banco de regras.
- Identifique produtos sujeitos à substituição tributária.
- Verifique a adequação de CFOPs (operação interna vs. interestadual).
- Foque em oportunidades de redução da carga tributária e destaque não conformidades críticas.

CONTEXTO RAG:
{contexto_rag}

FORMATO DE RESPOSTA (JSON estrito):
{{
  "status": "sucesso|erro|parcial",
  "produtos_analisados": <número>,
  "oportunidades": [
    {{
      "tipo": "Categoria da oportunidade",
      "produto": "Nome/NCM do produto",
      "descricao": "Descrição da oportunidade",
      "impacto": "Estimativa do impacto",
      "acao_recomendada": "O que fazer"
    }}
  ],
  "discrepancias": [
    {{
      "tipo": "Categoria da discrepância", 
      "produto": "Nome/NCM do produto",
      "problema": "Descrição do problema",
      "gravidade": "Alta|Média|Baixa",
      "correcao": "Como corrigir"
    }}
  ],
  "resumo_executivo": "Resumo executivo em texto markdown",
  "detalhes_tecnicos": "Detalhes técnicos em texto markdown"
}}'''),
            ("human", '''DADOS DA NOTA FISCAL PARA ANÁLISE:

CABEÇALHO DA NFe:
{dados_cabecalho}

PRODUTOS DA NFe (Enriquecidos com a Base de Conhecimento NCM):
{dados_produtos}

Analise estes dados contra as regras fiscais e a descrição oficial do NCM, e forneça o resultado no formato JSON especificado.''')
        ])

        # Parser JSON simples
        parser = JsonOutputParser()
        
        # Criar chain
        self.chain = prompt_template | self.llm | parser

    def analisar_nfe(self, cabecalho_df: pd.DataFrame, produtos_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Método principal que analisa a NFe usando LangChain, LLM e a base de NCM.
        """
        try:
            if not self.chain:
                return self._erro_chain_nao_inicializada()

            # Descriptografar dados para análise
            cabecalho = self.processor.decrypt_sensitive_data(cabecalho_df)
            produtos = self.processor.decrypt_sensitive_data(produtos_df)
            
            # Preparar dados para o prompt
            dados_cabecalho = self._formatar_cabecalho(cabecalho)
            # Formata os produtos e ENRIQUECE com a base de NCM
            dados_produtos = self._formatar_e_enriquecer_produtos(produtos)
            
            # Recuperar contexto relevante usando o sistema RAG
            query = f"Análise fiscal para NFe com CFOP {cabecalho.get('CFOP', 'N/A')} e produtos: {produtos['Descrição'].tolist()}"
            contexto_rag = "\n".join(self.rag_system.retrieve_context(query))
            
            # Executar análise via LangChain
            resultado = self.chain.invoke({
                "contexto_rag": contexto_rag,
                "dados_cabecalho": dados_cabecalho,
                "dados_produtos": dados_produtos
            })
            
            # Processar resultado
            if isinstance(resultado, dict):
                resultado['base_ncm_carregada'] = self.base_ncm is not None
                resultado['modelo_utilizado'] = getattr(self.llm, 'model_name', 'gemini')
                
                # Gerar dropdown formatado
                resultado['resumo_dropdown'] = self._gerar_dropdown(resultado)
                
                return resultado
            else:
                return self._erro_formato_resposta(str(resultado))
                
        except Exception as e:
            return self._erro_analise(str(e))

    def _formatar_cabecalho(self, cabecalho_df: pd.DataFrame) -> str:
        """Formata dados do cabeçalho para o prompt"""
        if cabecalho_df.empty:
            return "Cabeçalho não disponível"
            
        cabecalho = cabecalho_df.iloc[0] if len(cabecalho_df) > 0 else {}
        
        info_relevante = []
        campos_importantes = ['CNPJ', 'UF', 'Natureza da Operação', 'CFOP', 'Data', 'Valor Total']
        
        for campo in campos_importantes:
            if campo in cabecalho and pd.notna(cabecalho[campo]):
                info_relevante.append(f"{campo}: {cabecalho[campo]}")
                
        return "\n".join(info_relevante) if info_relevante else "Dados básicos do cabeçalho"

    def _formatar_e_enriquecer_produtos(self, produtos_df: pd.DataFrame) -> str:
        """Formata dados dos produtos e os enriquece com a descrição oficial do NCM."""
        if produtos_df.empty:
            return "Nenhum produto encontrado"
            
        produtos_enriquecidos = produtos_df.copy()
        
        # Adiciona a descrição oficial do NCM
        if 'NCM' in produtos_enriquecidos.columns and self.base_ncm is not None:
            produtos_enriquecidos['Descrição NCM (Oficial)'] = produtos_enriquecidos['NCM'].apply(
                lambda ncm: consultar_ncm(ncm, self.base_ncm)
            )

        # Selecionar e ordenar colunas para o prompt
        colunas_fiscais = [
            'Produto', 'Descrição NCM (Oficial)', 'NCM', 'CFOP', 'Quantidade', 'Valor Unitário', 'Valor Total',
            'Alíquota ICMS', 'Valor ICMS', 'Alíquota PIS', 'Valor PIS', 
            'Alíquota COFINS', 'Valor COFINS', 'Alíquota IPI', 'Valor IPI'
        ]
        
        colunas_existentes = [col for col in colunas_fiscais if col in produtos_enriquecidos.columns]
        
        # Limitar a 20 produtos para evitar prompt muito grande
        produtos_limitados = produtos_enriquecidos[colunas_existentes].head(20)
        
        # Converter para string formatada
        resultado = f"Total de produtos: {len(produtos_df)}\n\n"
        resultado += "Primeiros produtos para análise (enriquecidos com base NCM):\n"
        resultado += produtos_limitados.to_string(index=False)
        
        return resultado

    def _gerar_dropdown(self, resultado: Dict[str, Any]) -> str:
        """Gera relatório formatado para dropdown"""
        dropdown = "## Relatório da Análise Fiscal\n\n"
        
        # Resumo geral
        dropdown += f"**Status:** {resultado.get('status', 'Desconhecido')}\n"
        dropdown += f"**Produtos analisados:** {resultado.get('produtos_analisados', 0)}\n"
        dropdown += f"**Oportunidades:** {len(resultado.get('oportunidades', []))}\n"
        dropdown += f"**Discrepâncias:** {len(resultado.get('discrepancias', []))}\n\n"
        
        # Resumo executivo
        if resultado.get('resumo_executivo'):
            dropdown += "### Resumo Executivo\n\n"
            dropdown += resultado['resumo_executivo'] + "\n\n"
        
        # Oportunidades
        oportunidades = resultado.get('oportunidades', [])
        if oportunidades:
            dropdown += "### Oportunidades Identificadas\n\n"
            for i, oport in enumerate(oportunidades, 1):
                dropdown += f"**{i}. {oport.get('tipo', 'N/A')}**\n"
                dropdown += f"   - **Produto:** {oport.get('produto', 'N/A')}\n"
                dropdown += f"   - **Descrição:** {oport.get('descricao', 'N/A')}\n"
                dropdown += f"   - **Impacto:** {oport.get('impacto', 'N/A')}\n"
                dropdown += f"   - **Ação:** {oport.get('acao_recomendada', 'N/A')}\n\n"
        
        # Discrepâncias
        discrepancias = resultado.get('discrepancias', [])
        if discrepancias:
            dropdown += "### Discrepâncias Encontradas\n\n"
            for i, disc in enumerate(discrepancias, 1):
                dropdown += f"**{i}. {disc.get('tipo', 'N/A')}**\n"
                dropdown += f"   - **Produto:** {disc.get('produto', 'N/A')}\n"
                dropdown += f"   - **Problema:** {disc.get('problema', 'N/A')}\n"
                dropdown += f"   - **Gravidade:** {disc.get('gravidade', 'N/A')}\n"
                dropdown += f"   - **Correção:** {disc.get('correcao', 'N/A')}\n\n"
        
        # Detalhes técnicos
        if resultado.get('detalhes_tecnicos'):
            dropdown += "### Detalhes Técnicos\n\n"
            dropdown += resultado['detalhes_tecnicos'] + "\n\n"
        
        if not oportunidades and not discrepancias:
            dropdown += "### Conformidade Fiscal\n\n"
            dropdown += "Não foram identificadas oportunidades significativas ou discrepâncias críticas na análise realizada.\n"
        
        return dropdown

    def _erro_chain_nao_inicializada(self) -> Dict[str, Any]:
        """Retorna erro quando chain não foi inicializada"""
        return {
            'status': 'erro',
            'produtos_analisados': 0,
            'oportunidades': [],
            'discrepancias': [],
            'resumo_dropdown': "❌ **Erro:** LLM não inicializada. Verifique a configuração da GOOGLE_API_KEY.",
            'modelo_utilizado': 'N/A'
        }

    def _erro_formato_resposta(self, resposta: str) -> Dict[str, Any]:
        """Retorna erro de formato de resposta"""
        return {
            'status': 'erro',
            'produtos_analisados': 0,
            'oportunidades': [],
            'discrepancias': [],
            'resumo_dropdown': f"❌ **Erro de formato:** A LLM retornou resposta em formato inválido.\n\nResposta: {resposta[:500]}...",
            'modelo_utilizado': getattr(self.llm, 'model_name', 'gemini') if self.llm else 'N/A'
        }

    def _erro_analise(self, erro: str) -> Dict[str, Any]:
        """Retorna erro geral de análise"""
        return {
            'status': 'erro',
            'produtos_analisados': 0,
            'oportunidades': [],
            'discrepancias': [],
            'resumo_dropdown': f"❌ **Erro na análise:** {erro}",
            'modelo_utilizado': getattr(self.llm, 'model_name', 'gemini') if self.llm else 'N/A'
        }

    # Métodos de compatibilidade com código existente
    def buscar_regras_fiscais(self, cabecalho_df: pd.DataFrame, produtos_df: pd.DataFrame) -> Dict[str, Any]:
        """Alias para manter compatibilidade com código existente"""
        return self.analisar_nfe(cabecalho_df, produtos_df)




# Funções de conveniência para compatibilidade
def buscar_regras_fiscais_nfe(cabecalho_criptografado: pd.DataFrame, produtos_criptografados: pd.DataFrame) -> dict:
    """
    Função principal para análise fiscal usando LangChain
    
    Args:
        cabecalho_criptografado: DataFrame criptografado com cabeçalho
        produtos_criptografados: DataFrame criptografado com produtos
        
    Returns:
        dict: Resultado da análise fiscal
    """
    try:
        validador = ValidadorFiscal()
        return validador.analisar_nfe(cabecalho_criptografado, produtos_criptografados)
    except Exception as e:
        return {
            'status': 'erro',
            'produtos_analisados': 0,
            'oportunidades': [],
            'discrepancias': [],
            'resumo_dropdown': f"❌ **Erro crítico:** {str(e)}",
            'modelo_utilizado': 'N/A'
        }


# Alias para compatibilidade
verificar_regras_fiscais_nfe = buscar_regras_fiscais_nfe


if __name__ == "__main__":
    print("🚀 Validador Fiscal com LangChain - Teste Local\n")
    
    # Teste básico
    cabecalho_teste = pd.DataFrame({
        'CNPJ': ['12345678000199'],
        'UF': ['SP'],
        'Natureza da Operação': ['Venda'],
        'CFOP': ['6102']
    })
    
    produtos_teste = pd.DataFrame({
        'Produto': ['Notebook Dell Inspiron', 'Medicamento Genérico'],
        'NCM': ['84713012', '30049099'],
        'CFOP': ['6102', '5102'],
        'Quantidade': [1, 10],
        'Valor Unitário': [3500.00, 25.50],
        'Alíquota ICMS': ['12%', '0%'],
        'Alíquota PIS': ['1.65%', '0%'],
        'Alíquota COFINS': ['7.6%', '0%']
    })
    
    # Executar análise
    resultado = buscar_regras_fiscais_nfe(cabecalho_teste, produtos_teste)
    
    print(f"📊 Status: {resultado['status']}")
    print(f"📦 Produtos analisados: {resultado['produtos_analisados']}")
    print(f"🎯 Oportunidades: {len(resultado['oportunidades'])}")
    print(f"⚠️ Discrepâncias: {len(resultado['discrepancias'])}")
    print(f"🤖 Modelo: {resultado.get('modelo_utilizado', 'N/A')}")

    
    print("\n" + "="*50)
    print("RELATÓRIO COMPLETO:")
    print("="*50)
    print(resultado['resumo_dropdown'])
