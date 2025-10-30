"""
Analista Fiscal - Tratamento de Discrepâncias com LLM
Sistema especializado em analisar e propor soluções para discrepâncias fiscais identificadas
pelo validador, utilizando conhecimento da nuvem via LLM e regime de Lucro Real.
"""

import os
import json
import pandas as pd
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from rag_system import RAGSystem

# Import do processador de criptografia
try:
    from criptografia import SecureDataProcessor
except Exception:
    class SecureDataProcessor:
        def __init__(self):
            pass
        def decrypt_sensitive_data(self, df: pd.DataFrame, fields_to_decrypt=None) -> pd.DataFrame:
            return df


class AnalistaFiscal:
    """
    Analista fiscal especializado em tratamento de discrepâncias com LLM.
    Usa conhecimento da nuvem para propor soluções específicas para LUCRO REAL.
    """

    def __init__(self):
        """Inicializa o analista fiscal com LangChain"""
        self.processor = SecureDataProcessor()
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
                        print(f"✅ LLM Analista inicializada: {modelo}")
                        break
                        
                except Exception as e:
                    print(f"⚠️ Modelo {modelo} indisponível: {str(e)[:100]}")
                    continue

            if not self.llm:
                raise Exception("Nenhum modelo Gemini disponível")

            # Criar parser e chain
            self._criar_chain()
            
        except Exception as e:
            print(f"❌ Erro ao inicializar LLM Analista: {e}")
            self.llm = None
            self.chain = None

    def _criar_chain(self):
        """Cria a chain do LangChain com prompt especializado em análise de discrepâncias"""
        
        # Template do prompt para análise de discrepâncias
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """Você é um ANALISTA FISCAL ESPECIALISTA em regime de LUCRO REAL com profundo conhecimento da legislação tributária brasileira. Sua missão é analisar as discrepâncias fiscais identificadas e propor SOLUÇÕES PRÁTICAS, além de identificar oportunidades e riscos, seguindo a estrutura de um relatório detalhado. 

CONTEXTO IMPORTANTE:
- REGIME: LUCRO REAL (sempre considerar este regime)
- FOCO: Análise de discrepâncias, oportunidades, riscos e soluções.
- FONTE: Conhecimento da nuvem/legislação atualizada.
- DADOS: Dados sensíveis como CNPJ e nomes não devem ser divulgados ou utilizados pela LLM.
- FORMATAÇÃO: Evite emojis e mantenha uma resposta com teor corporativo.

IMPORTANTE SOBRE DADOS CRIPTOGRAFADOS:
- Os dados sensíveis (CNPJs, nomes, etc.) estão criptografados. Use padrões e estruturas dos dados criptografados para análise.
- Foque nos aspectos fiscais e tributários que podem ser identificados. Considere valores, alíquotas e classificações fiscais para análise.
- Se não houver percentagens das alíquotas, utilize os valores de tributos e impostos para o cálculo das mesmas e avaliação se estão corretas.
- Não tente descriptografar os dados - trabalhe com eles como estão.

ATENÇÃO ESPECIAL PARA UFs (UNIDADES FEDERATIVAS):
- As UFs são apresentadas de forma destacada no cabeçalho. Podem aparecer como códigos numéricos (ex: 35 = SP, 33 = RJ, 31 = MG).
- UF do Emitente: Estado de origem da operação.
- UF do Destinatário: Estado de destino da operação (CRÍTICO para análise ICMS).
- A diferença entre UF origem e destino é fundamental para: Alíquotas de ICMS interestadual, Aplicação de Substituição Tributária, Regras de DIFAL (Diferencial de Alíquota), Benefícios fiscais estaduais.

INSTRUÇÕES CRÍTICAS:
1. Para cada discrepância, busque na legislação atual a forma CORRETA de proceder.
2. Considere SEMPRE o regime de Lucro Real.
3. Identifique se há falta de dados críticos que impedem a correção.
4. Proponha ações específicas e práticas.
5. Indique quando é necessário consultar contador/advogado.
6. Cite base legal quando relevante.
7. Trabalhe com dados criptografados sem tentar revelá-los.

CONTEXTO RAG:
{contexto_rag}

FORMATO DE RESPOSTA (JSON estrito):
{{
  "status": "sucesso|erro|parcial",
  "regime_tributario": "LUCRO REAL",
  "resumo_nfe": {{
    "numero_nf": "Número da NF-e",
    "data_emissao": "Data de Emissão",
    "tipo_operacao": "Tipo de Operação (ex: VENDA DE MERCADORIA)",
    "emitente": {{
      "nome": "Nome do Emitente",
      "cnpj": "CNPJ do Emitente",
      "regime_tributario_emitente": "Regime Tributário do Emitente (ex: CRT 3 - Simples Nacional)"
    }},
    "destinatario": {{
      "nome": "Nome do Destinatário",
      "cnpj": "CNPJ do Destinatário",
      "tipo_entidade": "Tipo de Entidade (ex: entidade pública)"
    }},
    "valor_total_nfe": "Valor Total da NF-e",
    "produtos_vendidos": [
      {{
        "nome": "Nome do Produto",
        "ncm": "NCM do Produto",
        "caracteristicas": "Características do produto (ex: gêneros alimentícios frescos)"
      }}
    ],
    "informacoes_complementares_cruciais": "Informações adicionais relevantes da NF-e",
    "tributacao_declarada": {{
      "icms": {{
        "status": "Status do ICMS (ex: Isento)",
        "cst": "CST do ICMS",
        "justificativa": "Justificativa da tributação (se houver)"
      }},
      "ipi": {{
        "status": "Status do IPI (ex: Não tributado)",
        "cst": "CST do IPI"
      }},
      "pis": {{
        "valor": "Valor do PIS",
        "aliquota": "Alíquota do PIS",
        "cst": "CST do PIS"
      }},
      "cofins": {{
        "valor": "Valor do COFINS",
        "aliquota": "Alíquota do COFINS",
        "cst": "CST do COFINS"
      }},
      "irrf": {{
        "valor": "Valor do IRRF",
        "retencao": "Percentual de Retenção"
      }}
    }}
  }},
  "relevancia_legal": {{
    "introducao": "Introdução sobre a relevância legal da análise",
    "documentos_altamente_relevantes": [
      {{
        "titulo": "Título do Documento",
        "rank": "Rank de Relevância (se disponível)",
        "descricao": "Descrição da relevância do documento para a análise da NF-e"
      }}
    ],
    "documentos_relevancia_limitada_ou_nula": [
      {{
        "titulo": "Título do Documento",
        "rank": "Rank de Relevância (se disponível)",
        "descricao": "Descrição do porquê a relevância é limitada ou nula"
      }}
    ]
  }},
  "trecho_lei_chave": {{
    "texto": "Trecho mais crítico da lei",
    "fonte": "Fonte do trecho (ex: RESPOSTA À CONSULTA TRIBUTÁRIA 23097/2021)",
    "preocupacao_validade_isencao": "Análise da preocupação sobre a validade da isenção (se houver)"
  }},
  "oportunidade_economia_beneficio": {{
    "descricao_geral": "Descrição geral da principal oportunidade de economia/benefício",
    "detalhamento_oportunidade": {{
      "titulo": "Título da Oportunidade (ex: Alíquota Zero de PIS e COFINS para Produtos Agrícolas)",
      "base_legal": "Base legal (ex: Art. 1º da Lei nº 10.925/2004)",
      "produtos_beneficiados": "Produtos da NF-e beneficiados",
      "ncms_beneficiados": "NCMs dos produtos beneficiados",
      "situacao_nfe": "Situação atual na NF-e (ex: PIS/COFINS declarado com alíquotas incorretas)",
      "cst_correto": "CST correto (se aplicável)"
    }},
    "mensuracao_economia": {{
      "valor_total_produtos_nfe": "Valor Total dos Produtos na NF-e",
      "valor_pis_recolhido": "Valor de PIS calculado e recolhido na NF-e",
      "valor_cofins_recolhido": "Valor de COFINS calculado e recolhido na NF-e",
      "total_indevidamente_recolhido": "Total de PIS/COFINS indevidamente recolhido nesta NF-e"
    }}
  }},
  "dicas_aplicacao_mensuracao": {{
    "acao_imediata": "Ação imediata recomendada",
    "correcao_emissoes_futuras": {{
      "descricao": "Descrição da correção para emissões futuras",
      "exemplo_economia_mensal_anual": "Exemplo de economia mensal/anual"
    }},
    "recuperacao_creditos_passados": "Recomendação sobre recuperação de créditos passados"
  }},
  "alerta_conformidade": {{
    "icms": {{
      "alerta": "Alerta de conformidade para ICMS",
      "base_legal_reavaliacao": "Base legal para reavaliação da isenção",
      "consulta_tributaria_relevante": "Resposta à Consulta Tributária relevante",
      "risco_nao_conformidade": "Risco de não conformidade fiscal"
    }}
  }},
  "plano_acao_consolidado": {{
    "acoes_imediatas": ["Lista de ações urgentes"],
    "acoes_medio_prazo": ["Lista de ações para implementar"],
    "consultoria_necessaria": ["Pontos que necessitam consultoria"],
    "documentos_necessarios": ["Documentos a providenciar"],
    "riscos_identificados": ["Riscos se não corrigir"]
  }},
  "limitacoes_analise": "Limitações encontradas por falta de dados",
  "resumo_executivo": "Resumo executivo em texto markdown com foco em ações",
  "detalhes_tecnicos": "Detalhes técnicos específicos em texto markdown"
}}
""")
            ,
            ("human", """DADOS PARA ANÁLISE DE DISCREPÂNCIAS (CRIPTOGRAFADOS):

IMPORTANTE: Os dados abaixo estão criptografados por segurança. Analise os padrões, estruturas e valores não sensíveis.

CABEÇALHO DA NFe (CRIPTOGRAFADO):
{dados_cabecalho}

PRODUTOS DA NFe (CRIPTOGRAFADOS):
{dados_produtos}

DISCREPÂNCIAS IDENTIFICADAS PELO VALIDADOR:
{discrepancias_validador}

OPORTUNIDADES IDENTIFICADAS PELO VALIDADOR:
{oportunidades_validador}

CONTEXTO DO RESULTADO DO VALIDADOR:
{contexto_validador}

INSTRUÇÕES ESPECÍFICAS PARA ANÁLISE DE UFs:
1. Identifique claramente a UF de ORIGEM (Emitente) e UF de DESTINO (Destinatário)
2. Se as UFs forem diferentes, considere operação INTERESTADUAL
3. Se as UFs forem iguais, considere operação INTERNA
4. Para operações interestaduais, verifique:
   - Alíquotas de ICMS interestaduais (4%, 7% ou 12%)
   - Aplicação de DIFAL quando destinatário for consumidor final
   - Substituição Tributária entre estados
   - Benefícios fiscais específicos

Analise essas discrepâncias considerando o regime de LUCRO REAL e forneça soluções práticas baseadas na legislação atual. Trabalhe com os dados criptografados como estão, focando nos aspectos fiscais identificáveis.""")
        ])

        # Parser JSON
        parser = JsonOutputParser()
        
        # Criar chain
        self.chain = prompt_template | self.llm | parser

    def analisar_discrepancias(self, 
                             cabecalho_df: pd.DataFrame, 
                             produtos_df: pd.DataFrame, 
                             resultado_validador: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método principal que analisa discrepâncias usando LLM e conhecimento da nuvem
        
        Args:
            cabecalho_df: DataFrame criptografado com dados do cabeçalho (mantido criptografado)
            produtos_df: DataFrame criptografado com dados dos produtos (mantido criptografado)
            resultado_validador: Resultado completo do validador com discrepâncias
            
        Returns:
            dict: Resultado da análise com soluções propostas
            
        IMPORTANTE: Este método trabalha com dados CRIPTOGRAFADOS por segurança.
        A LLM analisa padrões e estruturas dos dados sem descriptografá-los.
        """
        try:
            if not self.chain:
                return self._erro_chain_nao_inicializada()

            # Verificar se há discrepâncias para analisar
            discrepancias = resultado_validador.get('discrepancias', [])
            if not discrepancias:
                return self._sem_discrepancias()

            # Usar dados CRIPTOGRAFADOS para análise (não descriptografar)
            # A LLM trabalhará com dados anonimizados/criptografados
            cabecalho = cabecalho_df
            produtos = produtos_df
            
            print(f"🔒 Analista - Usando dados CRIPTOGRAFADOS para análise na nuvem")
            print(f"   Cabecalho shape: {cabecalho.shape if not cabecalho.empty else 'Vazio'}")
            print(f"   Produtos shape: {produtos.shape if not produtos.empty else 'Vazio'}")
            
            # Preparar dados criptografados para o prompt
            dados_cabecalho = self._formatar_cabecalho_criptografado(cabecalho)
            dados_produtos = self._formatar_produtos_criptografados(produtos)
            discrepancias_formatadas = self._formatar_discrepancias(discrepancias)
            oportunidades_formatadas = self._formatar_oportunidades(resultado_validador.get('oportunidades', []))
            contexto_formatado = self._formatar_contexto_validador(resultado_validador)
            
            # Recuperar contexto relevante usando o sistema RAG
            query = f"Análise de discrepâncias para NFe com UF de origem {cabecalho.get('Emitente UF', 'N/A')} e UF de destino {cabecalho.get('Destinatário UF', 'N/A')}. Discrepâncias: {discrepancias_formatadas}"
            contexto_rag = "\n".join(self.rag_system.retrieve_context(query))
            
            # Executar análise via LangChain
            resultado = self.chain.invoke({
                "dados_cabecalho": dados_cabecalho,
                "dados_produtos": dados_produtos,
                "discrepancias_validador": discrepancias_formatadas,
                "oportunidades_validador": oportunidades_formatadas,
                "contexto_validador": contexto_formatado,
                "contexto_rag": contexto_rag
            })
            
            # Processar resultado
            if isinstance(resultado, dict):
                resultado['modelo_utilizado'] = getattr(self.llm, 'model_name', 'gemini')
                resultado['timestamp_analise'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Gerar relatório formatado
                resultado['relatorio_final'] = self._gerar_relatorio_final(resultado)
                
                return resultado
            else:
                return self._erro_formato_resposta(str(resultado))
                
        except Exception as e:
            return self._erro_analise(str(e))

    def _formatar_cabecalho(self, cabecalho_df: pd.DataFrame) -> str:
        """Formata dados do cabeçalho para o prompt (MÉTODO LEGADO - NÃO USADO)"""
        # Mantido para compatibilidade, mas não é usado
        pass

    def _formatar_cabecalho_criptografado(self, cabecalho_df: pd.DataFrame) -> str:
        """Formata dados CRIPTOGRAFADOS do cabeçalho para análise na nuvem"""
        if cabecalho_df.empty:
            return "Cabeçalho não disponível"
            
        cabecalho = cabecalho_df.iloc[0] if len(cabecalho_df) > 0 else {}
        
        info_relevante = []
        
        # SEÇÃO ESPECÍFICA PARA UFs - DESTACAR PARA MELHOR IDENTIFICAÇÃO
        info_relevante.append("=== INFORMAÇÕES DE LOCALIZAÇÃO (UFs) ===")
        
        # Mapear códigos de UF para siglas se necessário
        codigo_uf_map = {
            '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',
            '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL', '28': 'SE', '29': 'BA',
            '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
            '41': 'PR', '42': 'SC', '43': 'RS',
            '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF'
        }
        
        # Campos relacionados a UF com prioridade
        campos_uf = ['UF', 'Emitente UF', 'Destinatário UF', 'Transportadora UF']
        
        for campo in campos_uf:
            if campo in cabecalho and pd.notna(cabecalho[campo]):
                valor = str(cabecalho[campo]).strip()
                # Converter código para sigla se necessário
                if valor in codigo_uf_map:
                    valor_formatado = f"{valor} ({codigo_uf_map[valor]})"
                else:
                    valor_formatado = valor
                info_relevante.append(f"🗺️ {campo}: {valor_formatado}")
        
        info_relevante.append("=== OUTROS DADOS DO CABEÇALHO ===")
        
        # Campos fiscais importantes
        campos_fiscais = ['CFOP', 'Natureza Operação', 'Valor Total', 'Data Emissão', 'Número NF']
        
        for campo in campos_fiscais:
            if campo in cabecalho and pd.notna(cabecalho[campo]):
                info_relevante.append(f"📋 {campo}: {cabecalho[campo]}")
        
        # Outros campos (criptografados)
        for campo, valor in cabecalho.items():
            if campo not in campos_uf + campos_fiscais and pd.notna(valor) and str(valor).strip():
                info_relevante.append(f"🔒 {campo}: {valor}")
                
        return "\n".join(info_relevante) if info_relevante else "Dados básicos do cabeçalho (criptografados)"

    def _formatar_produtos(self, produtos_df: pd.DataFrame) -> str:
        """Formata dados dos produtos para o prompt (MÉTODO LEGADO - NÃO USADO)"""
        # Mantido para compatibilidade, mas não é usado
        pass

    def _formatar_produtos_criptografados(self, produtos_df: pd.DataFrame) -> str:
        """Formata dados CRIPTOGRAFADOS dos produtos para análise na nuvem"""
        if produtos_df.empty:
            return "Nenhum produto encontrado"
            
        # Limitar a 15 produtos para evitar prompt muito grande (dados criptografados podem ser maiores)
        produtos_limitados = produtos_df.head(15)
        
        resultado = f"Total de produtos: {len(produtos_df)}\n\n"
        resultado += "Produtos para análise de discrepâncias (DADOS CRIPTOGRAFADOS):\n"
        resultado += "IMPORTANTE: Os dados sensíveis abaixo estão criptografados para proteção.\n\n"
        
        # Usar todas as colunas disponíveis (dados criptografados)
        try:
            resultado += produtos_limitados.to_string(index=True, max_cols=None, max_colwidth=50)
        except Exception as e:
            # Fallback em caso de erro
            resultado += f"Erro ao formatar produtos criptografados: {str(e)}\n"
            resultado += f"Colunas disponíveis: {list(produtos_df.columns)}"
        
        return resultado

    def _formatar_discrepancias(self, discrepancias: List[Dict]) -> str:
        """Formata discrepâncias do validador para análise"""
        if not discrepancias:
            return "Nenhuma discrepância identificada"
        
        resultado = f"Total de discrepâncias: {len(discrepancias)}\n\n"
        
        for i, disc in enumerate(discrepancias, 1):
            resultado += f"DISCREPÂNCIA {i}:\n"
            resultado += f"  Tipo: {disc.get('tipo', 'N/A')}\n"
            resultado += f"  Produto: {disc.get('produto', 'N/A')}\n"
            resultado += f"  Problema: {disc.get('problema', 'N/A')}\n"
            resultado += f"  Gravidade: {disc.get('gravidade', 'N/A')}\n"
            resultado += f"  Correção sugerida: {disc.get('correcao', 'N/A')}\n\n"
        
        return resultado

    def _formatar_oportunidades(self, oportunidades: List[Dict]) -> str:
        """Formata oportunidades do validador"""
        if not oportunidades:
            return "Nenhuma oportunidade identificada"
        
        resultado = f"Total de oportunidades: {len(oportunidades)}\n\n"
        
        for i, oport in enumerate(oportunidades, 1):
            resultado += f"OPORTUNIDADE {i}:\n"
            resultado += f"  Tipo: {oport.get('tipo', 'N/A')}\n"
            resultado += f"  Produto: {oport.get('produto', 'N/A')}\n"
            resultado += f"  Descrição: {oport.get('descricao', 'N/A')}\n"
            resultado += f"  Impacto: {oport.get('impacto', 'N/A')}\n"
            resultado += f"  Ação recomendada: {oport.get('acao_recomendada', 'N/A')}\n\n"
        
        return resultado

    def _formatar_contexto_validador(self, resultado_validador: Dict[str, Any]) -> str:
        """Formata contexto geral do validador"""
        contexto = f"Status da validação: {resultado_validador.get('status', 'N/A')}\n"
        contexto += f"Produtos analisados: {resultado_validador.get('produtos_analisados', 0)}\n"
        contexto += f"Total de oportunidades: {len(resultado_validador.get('oportunidades', []))}\n"
        contexto += f"Total de discrepâncias: {len(resultado_validador.get('discrepancias', []))}\n"
        
        if resultado_validador.get('resumo_executivo'):
            contexto += f"\nResumo do validador:\n{resultado_validador['resumo_executivo']}"
        
        return contexto

    def _gerar_relatorio_final(self, resultado: Dict[str, Any]) -> str:
        """Gera relatório final formatado com base no novo esquema JSON."""
        relatorio = "# Análise Detalhada da Nota Fiscal Eletrônica (NF-e) e Relevância Legal\n\n"

        # 1. Resumo da NF-e
        relatorio += "## 1. Resumo da NF-e\n\n"
        resumo_nfe = resultado.get("resumo_nfe", {})
        if resumo_nfe:
            relatorio += f'A Nota Fiscal Eletrônica (NF-e) em análise, com número {resumo_nfe.get('numero_nf', 'N/A')} e emitida em {resumo_nfe.get('data_emissao', 'N/A')}, descreve uma operação de "{resumo_nfe.get('tipo_operacao', 'N/A')}".\n\n'
            relatorio += "### Detalhes da Operação\n\n"
            relatorio += f"- **Emissor**: {resumo_nfe.get('emitente', {}).get('nome', 'N/A')}, CNPJ {resumo_nfe.get('emitente', {}).get('cnpj', 'N/A')}, enquadrada no Regime {resumo_nfe.get('emitente', {}).get('regime_tributario_emitente', 'N/A')}.\n"
            relatorio += f"- **Destinatário**: {resumo_nfe.get('destinatario', {}).get('nome', 'N/A')}, CNPJ {resumo_nfe.get('destinatario', {}).get('cnpj', 'N/A')}, uma {resumo_nfe.get('destinatario', {}).get('tipo_entidade', 'N/A')}.\n"
            relatorio += f"- **Valor Total da NF-e**: R$ {resumo_nfe.get('valor_total_nfe', '0.00')}.\n"
            
            produtos_vendidos = resumo_nfe.get("produtos_vendidos", [])
            if produtos_vendidos:
                relatorio += "- **Produtos Vendidos**:\n"
                for prod in produtos_vendidos:
                    relatorio += f"    - {prod.get('nome', 'N/A')} (NCM {prod.get('ncm', 'N/A')}) {prod.get('caracteristicas', '')}\n"
            
            if resumo_nfe.get('informacoes_complementares_cruciais'):
                relatorio += f"- **Informações Complementares Cruciais**: {resumo_nfe['informacoes_complementares_cruciais']}\n"
            
            tributacao_declarada = resumo_nfe.get("tributacao_declarada", {})
            if tributacao_declarada:
                relatorio += "- **Tributação Declarada**:\n"
                if tributacao_declarada.get('icms'):
                    icms = tributacao_declarada['icms']
                    relatorio += f"    - ICMS: {icms.get('status', 'N/A')} (CST {icms.get('cst', 'N/A')}), com a justificativa em infCpl: \"{icms.get('justificativa', 'N/A')}\".\n"
                if tributacao_declarada.get('ipi'):
                    ipi = tributacao_declarada['ipi']
                    relatorio += f"    - IPI: {ipi.get('status', 'N/A')} (CST {ipi.get('cst', 'N/A')}).\n"
                if tributacao_declarada.get('pis'):
                    pis = tributacao_declarada['pis']
                    relatorio += f"    - PIS: R$ {pis.get('valor', '0.00')} (calculado com alíquota de {pis.get('aliquota', 'N/A')}% sobre o valor dos produtos) - CST {pis.get('cst', 'N/A')}.\n"
                if tributacao_declarada.get('cofins'):
                    cofins = tributacao_declarada['cofins']
                    relatorio += f"    - COFINS: R$ {cofins.get('valor', '0.00')} (calculado com alíquota de {cofins.get('aliquota', 'N/A')}% sobre o valor dos produtos) - CST {cofins.get('cst', 'N/A')}.\n"
                if tributacao_declarada.get('irrf'):
                    irrf = tributacao_declarada['irrf']
                    relatorio += f"    - IRRF: R$ {irrf.get('valor', '0.00')} (retenção de {irrf.get('retencao', 'N/A')}% sobre o valor total), conforme infCpl.\n"
        relatorio += "\n"

        # 2. Relevância Legal
        relatorio += "## 2. Relevância Legal\n\n"
        relevancia_legal = resultado.get("relevancia_legal", {})
        if relevancia_legal:
            relatorio += f"{relevancia_legal.get('introducao', '')}\n\n"
            
            documentos_altamente_relevantes = relevancia_legal.get("documentos_altamente_relevantes", [])
            if documentos_altamente_relevantes:
                relatorio += "### Documentos Altamente Relevantes\n\n"
                for doc in documentos_altamente_relevantes:
                    relatorio += f"- **{doc.get('titulo', 'N/A')}** (Documento Rank {doc.get('rank', '')}): {doc.get('descricao', 'N/A')}\n"
            
            documentos_limitada_nula = relevancia_legal.get("documentos_relevancia_limitada_ou_nula", [])
            if documentos_limitada_nula:
                relatorio += "### Documentos de Relevância Limitada ou Nula\n\n"
                for doc in documentos_limitada_nula:
                    relatorio += f"- **{doc.get('titulo', 'N/A')}** (Documento Rank {doc.get('rank', '')}): {doc.get('descricao', 'N/A')}\n"
        relatorio += "\n"

        # 3. Trecho de Lei Chave
        relatorio += "## 3. Trecho de Lei Chave\n\n"
        trecho_lei_chave = resultado.get("trecho_lei_chave", {})
        if trecho_lei_chave:
            relatorio += f"{trecho_lei_chave.get('texto', 'N/A')}\n"
            if trecho_lei_chave.get('fonte'):
                relatorio += f"Fonte: {trecho_lei_chave['fonte']}\n"
            if trecho_lei_chave.get('preocupacao_validade_isencao'):
                relatorio += f"\n{trecho_lei_chave['preocupacao_validade_isencao']}\n"
        relatorio += "\n"

        # 4. Oportunidade de Economia/Benefício
        relatorio += "## 4. Oportunidade de Economia/Benefício\n\n"
        oportunidade_economia_beneficio = resultado.get("oportunidade_economia_beneficio", {})
        if oportunidade_economia_beneficio:
            relatorio += f"{oportunidade_economia_beneficio.get('descricao_geral', 'N/A')}\n\n"
            
            detalhamento = oportunidade_economia_beneficio.get("detalhamento_oportunidade", {})
            if detalhamento:
                relatorio += "### Detalhamento da Oportunidade\n\n"
                relatorio += f"1. **{detalhamento.get('titulo', 'N/A')}**:\n"
                if detalhamento.get('base_legal'):
                    relatorio += f"-   Conforme {detalhamento['base_legal']}\n"
                if detalhamento.get('produtos_beneficiados'):
                    relatorio += f"-   Produtos da NF-e beneficiados: {detalhamento['produtos_beneficiados']}\n"
                if detalhamento.get('ncms_beneficiados'):
                    relatorio += f"-   NCMs beneficiados: {detalhamento['ncms_beneficiados']}\n"
                if detalhamento.get('situacao_nfe'):
                    relatorio += f"-   Situação na NF-e: {detalhamento['situacao_nfe']}\n"
                if detalhamento.get('cst_correto'):
                    relatorio += f"-   CST Correto: {detalhamento['cst_correto']}\n"
            
            mensuracao = oportunidade_economia_beneficio.get("mensuracao_economia", {})
            if mensuracao:
                relatorio += "\n### Mensuração da Economia/Benefício\n\n"
                relatorio += f"-   Valor Total dos Produtos na NF-e: R$ {mensuracao.get('valor_total_produtos_nfe', '0.00')}\n"
                relatorio += f"-   Valor de PIS calculado e recolhido na NF-e: R$ {mensuracao.get('valor_pis_recolhido', '0.00')}\n"
                relatorio += f"-   Valor de COFINS calculado e recolhido na NF-e: R$ {mensuracao.get('valor_cofins_recolhido', '0.00')}\n"
                relatorio += f"-   Total de PIS/COFINS indevidamente recolhido nesta NF-e: R$ {mensuracao.get('total_indevidamente_recolhido', '0.00')}\n"
        relatorio += "\n"

        # 5. Dicas para Aplicação e Mensuração (em R$)
        relatorio += "## 5. Dicas para Aplicação e Mensuração (em R$)\n\n"
        dicas_aplicacao_mensuracao = resultado.get("dicas_aplicacao_mensuracao", {})
        if dicas_aplicacao_mensuracao:
            if dicas_aplicacao_mensuracao.get('acao_imediata'):
                relatorio += f"-   **Ação Imediata**: {dicas_aplicacao_mensuracao['acao_imediata']}\n"
            
            correcao_emissoes_futuras = dicas_aplicacao_mensuracao.get("correcao_emissoes_futuras", {})
            if correcao_emissoes_futuras:
                relatorio += f"-   **Correção em Emissões Futuras**: {correcao_emissoes_futuras.get('descricao', 'N/A')}\n"
                if correcao_emissoes_futuras.get('exemplo_economia_mensal_anual'):
                    relatorio += f"    -   {correcao_emissoes_futuras['exemplo_economia_mensal_anual']}\n"
            
            if dicas_aplicacao_mensuracao.get('recuperacao_creditos_passados'):
                relatorio += f"-   **Recuperação de Créditos Passados**: {dicas_aplicacao_mensuracao['recuperacao_creditos_passados']}\n"
        relatorio += "\n"

        # 6. Alerta de Conformidade (ICMS)
        relatorio += "## 6. Alerta de Conformidade (ICMS)\n\n"
        alerta_conformidade = resultado.get("alerta_conformidade", {})
        if alerta_conformidade and alerta_conformidade.get('icms'):
            icms_alerta = alerta_conformidade['icms']
            if icms_alerta.get('alerta'):
                relatorio += f"-   **Alerta**: {icms_alerta['alerta']}\n"
            if icms_alerta.get('base_legal_reavaliacao'):
                relatorio += f"-   **Base Legal para Reavaliação**: {icms_alerta['base_legal_reavaliacao']}\n"
            if icms_alerta.get('consulta_tributaria_relevante'):
                relatorio += f"-   **Consulta Tributária Relevante**: {icms_alerta['consulta_tributaria_relevante']}\n"
            if icms_alerta.get('risco_nao_conformidade'):
                relatorio += f"-   **Risco de Não Conformidade**: {icms_alerta['risco_nao_conformidade']}\n"
        relatorio += "\n"

        # Plano de ação consolidado (mantido do original, mas pode ser integrado melhor)
        plano = resultado.get('plano_acao_consolidado', {})
        if plano:
            relatorio += "## Plano de Ação Consolidado\n\n"
            if plano.get('acoes_imediatas'):
                relatorio += "### Ações Imediatas\n"
                for acao in plano['acoes_imediatas']:
                    relatorio += f"- {acao}\n"
                relatorio += "\n"
            if plano.get('acoes_medio_prazo'):
                relatorio += "### Ações a Médio Prazo\n"
                for acao in plano['acoes_medio_prazo']:
                    relatorio += f"- {acao}\n"
                relatorio += "\n"
            if plano.get('consultoria_necessaria'):
                relatorio += "### Consultoria Necessária\n"
                for item in plano['consultoria_necessaria']:
                    relatorio += f"- {item}\n"
                relatorio += "\n"
            if plano.get('documentos_necessarios'):
                relatorio += "### Documentos a Providenciar\n"
                for doc in plano['documentos_necessarios']:
                    relatorio += f"- {doc}\n"
                relatorio += "\n"
            if plano.get('riscos_identificados'):
                relatorio += "### Riscos Identificados (se não corrigir)\n"
                for risco in plano['riscos_identificados']:
                    relatorio += f"- {risco}\n"
                relatorio += "\n"
        
        # Limitações
        if resultado.get('limitacoes_analise'):
            relatorio += "## Limitações da Análise\n\n"
            relatorio += resultado['limitacoes_analise'] + "\n\n"
        
        # Detalhes técnicos
        if resultado.get('detalhes_tecnicos'):
            relatorio += "## Detalhes Técnicos\n\n"
            relatorio += resultado['detalhes_tecnicos'] + "\n\n"
        
        # Rodapé
        relatorio += "---\n"
        relatorio += f"*Análise gerada pelo Analista Fiscal IA - Modelo: {resultado.get('modelo_utilizado', 'N/A')}*\n"
        relatorio += "*Regime: LUCRO REAL - Sempre consulte um profissional contábil para casos complexos*"
        
        return relatorio

    def _sem_discrepancias(self) -> Dict[str, Any]:
        """Retorna resultado quando não há discrepâncias para analisar"""
        return {
            'status': 'sucesso',
            'regime_tributario': 'LUCRO REAL',
            'discrepancias_analisadas': 0,
            'analises_detalhadas': [],
            'oportunidades_adicionais': [],
            'plano_acao_consolidado': {},
            'limitacoes_analise': '',
            'relatorio_final': "# Análise Concluída\n\n**Nenhuma discrepância identificada para tratamento.**\n\nTodas as verificações do validador foram aprovadas. A nota fiscal está em conformidade com as regras analisadas.",
            'modelo_utilizado': getattr(self.llm, 'model_name', 'gemini') if self.llm else 'N/A',
            'timestamp_analise': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _erro_chain_nao_inicializada(self) -> Dict[str, Any]:
        """Retorna erro quando chain não foi inicializada"""
        return {
            'status': 'erro',
            'regime_tributario': 'LUCRO REAL',
            'discrepancias_analisadas': 0,
            'analises_detalhadas': [],
            'oportunidades_adicionais': [],
            'plano_acao_consolidado': {},
            'limitacoes_analise': 'LLM não inicializada',
            'relatorio_final': "**Erro:** LLM não inicializada. Verifique a configuração da GOOGLE_API_KEY.",
            'modelo_utilizado': 'N/A',
            'timestamp_analise': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _erro_formato_resposta(self, resposta: str) -> Dict[str, Any]:
        """Retorna erro de formato de resposta"""
        return {
            'status': 'erro',
            'regime_tributario': 'LUCRO REAL',
            'discrepancias_analisadas': 0,
            'analises_detalhadas': [],
            'oportunidades_adicionais': [],
            'plano_acao_consolidado': {},
            'limitacoes_analise': 'Erro de formato na resposta da LLM',
            'relatorio_final': f"**Erro de formato:** A LLM retornou resposta em formato inválido.\n\nResposta: {resposta[:500]}...",
            'modelo_utilizado': getattr(self.llm, 'model_name', 'gemini') if self.llm else 'N/A',
            'timestamp_analise': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _erro_analise(self, erro: str) -> Dict[str, Any]:
        """Retorna erro geral de análise"""
        return {
            'status': 'erro',
            'regime_tributario': 'LUCRO REAL',
            'discrepancias_analisadas': 0,
            'analises_detalhadas': [],
            'oportunidades_adicionais': [],
            'plano_acao_consolidado': {},
            'limitacoes_analise': f'Erro durante análise: {erro}',
            'relatorio_final': f"**Erro na análise:** {erro}",
            'modelo_utilizado': getattr(self.llm, 'model_name', 'gemini') if self.llm else 'N/A',
            'timestamp_analise': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }


# Função de conveniência para uso na interface
def analisar_discrepancias_nfe(cabecalho_criptografado: pd.DataFrame, 
                              produtos_criptografados: pd.DataFrame, 
                              resultado_validador: Dict[str, Any]) -> Dict[str, Any]:
    """
    Função principal para análise de discrepâncias usando LangChain
    
    Args:
        cabecalho_criptografado: DataFrame criptografado com cabeçalho (MANTIDO CRIPTOGRAFADO)
        produtos_criptografados: DataFrame criptografado com produtos (MANTIDO CRIPTOGRAFADO)
        resultado_validador: Resultado completo da análise do validador
        
    Returns:
        dict: Resultado da análise com soluções propostas
        
    IMPORTANTE: Esta função trabalha com dados CRIPTOGRAFADOS por segurança.
    Os dados não são descriptografados antes de serem enviados para a LLM.
    """
    try:
        analista = AnalistaFiscal()
        return analista.analisar_discrepancias(cabecalho_criptografado, produtos_criptografados, resultado_validador)
    except Exception as e:
        return {
            'status': 'erro',
            'regime_tributario': 'LUCRO REAL',
            'discrepancias_analisadas': 0,
            'analises_detalhadas': [],
            'oportunidades_adicionais': [],
            'plano_acao_consolidado': {},
            'limitacoes_analise': f'Erro crítico: {str(e)}',
            'relatorio_final': f"**Erro crítico:** {str(e)}",
            'modelo_utilizado': 'N/A',
            'timestamp_analise': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }


if __name__ == "__main__":
    print("🎯 Analista Fiscal - Tratamento de Discrepâncias - Teste Local\n")
    
    # Teste básico com discrepâncias simuladas
    cabecalho_teste = pd.DataFrame({
        'CNPJ': ['12345678000199'],
        'UF': ['SP'],
        'Natureza da Operação': ['Venda'],
        'CFOP': ['6102']
    })
    
    produtos_teste = pd.DataFrame({
        'Produto': ['Notebook Dell Inspiron'],
        'NCM': ['84713012'],
        'CFOP': ['6102'],
        'Quantidade': [1],
        'Valor Unitário': [3500.00],
        'Alíquota ICMS': ['12%'],
        'Alíquota PIS': ['1.65%'],
        'Alíquota COFINS': ['7.6%']
    })
    
    # Resultado simulado do validador
    resultado_validador_teste = {
        'status': 'parcial',
        'produtos_analisados': 1,
        'oportunidades': [
            {
                'tipo': 'Substituição Tributária',
                'produto': 'Notebook Dell Inspiron',
                'descricao': 'Produto pode estar sujeito à ST',
                'impacto': 'Redução de 5% na carga tributária',
                'acao_recomendada': 'Verificar enquadramento na ST'
            }
        ],
        'discrepancias': [
            {
                'tipo': 'Alíquota ICMS',
                'produto': 'Notebook Dell Inspiron',
                'problema': 'Alíquota aplicada pode estar incorreta',
                'gravidade': 'Média',
                'correcao': 'Verificar alíquota correta para NCM'
            }
        ],
        'resumo_executivo': 'Análise identificou discrepâncias na alíquota ICMS'
    }
    
    # Executar análise
    resultado = analisar_discrepancias_nfe(cabecalho_teste, produtos_teste, resultado_validador_teste)
    
    print(f"🎯 Status: {resultado['status']}")
    print(f"📊 Regime: {resultado['regime_tributario']}")
    print(f"🔍 Discrepâncias analisadas: {resultado['discrepancias_analisadas']}")
    print(f"💡 Análises detalhadas: {len(resultado['analises_detalhadas'])}")
    print(f"🤖 Modelo: {resultado.get('modelo_utilizado', 'N/A')}")
    
    print("\n" + "="*70)
    print("RELATÓRIO FINAL:")
    print("="*70)
    print(resultado['relatorio_final'])