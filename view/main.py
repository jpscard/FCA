import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
from criptografia import SecureDataProcessor
from agents.validador import buscar_regras_fiscais_nfe
from agents.analista import analisar_discrepancias_nfe
from agents.tributarista import calcular_delta_tributario



def extrair_dados_xml(xml_content):
    ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
    root = ET.fromstring(xml_content)
    infNFe = root.find(".//nfe:infNFe", ns)

    def get_text(tag, parent=infNFe, default="0"):
        return parent.findtext(tag, default=default, namespaces=ns)
    
    def converter_codigo_uf(codigo_uf):
        """Converte código numérico da UF para sigla"""
        mapa_uf = {
            '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',
            '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL', '28': 'SE', '29': 'BA',
            '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
            '41': 'PR', '42': 'SC', '43': 'RS',
            '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF'
        }
        return mapa_uf.get(str(codigo_uf), codigo_uf)

    dados = {}

    # --- IDE (Identificação da Nota) ---
    ide = infNFe.find("nfe:ide", ns)
    if ide is not None:
        dados["Número NF"] = get_text("nfe:nNF", ide)
        dados["Série"] = get_text("nfe:serie", ide)
        dados["Data Emissão"] = get_text("nfe:dhEmi", ide)
        dados["Data Saída/Entrada"] = get_text("nfe:dhSaiEnt", ide)
        dados["Natureza Operação"] = get_text("nfe:natOp", ide)
        dados["Tipo NF"] = get_text("nfe:tpNF", ide)
        dados["Modelo"] = get_text("nfe:mod", ide)
        # Converter código UF para sigla
        codigo_uf = get_text("nfe:cUF", ide)
        dados["UF"] = converter_codigo_uf(codigo_uf)
        dados["UF Código"] = codigo_uf  # Manter código original também
        dados["Finalidade"] = get_text("nfe:finNFe", ide)

    # --- EMITENTE ---
    emit = infNFe.find("nfe:emit", ns)
    if emit is not None:
        dados["Emitente CNPJ"] = get_text("nfe:CNPJ", emit)
        dados["Emitente Nome"] = get_text("nfe:xNome", emit)
        dados["Emitente Fantasia"] = get_text("nfe:xFant", emit)
        dados["Emitente IE"] = get_text("nfe:IE", emit)
        # UF do emitente com conversão
        uf_emit = get_text("nfe:enderEmit/nfe:UF", emit)
        dados["Emitente UF"] = converter_codigo_uf(uf_emit) if uf_emit != "0" else uf_emit
        dados["Emitente Município"] = get_text("nfe:enderEmit/nfe:xMun", emit)
        dados["Emitente CEP"] = get_text("nfe:enderEmit/nfe:CEP", emit)

    # --- DESTINATÁRIO ---
    dest = infNFe.find("nfe:dest", ns)
    if dest is not None:
        dados["Destinatário CNPJ"] = get_text("nfe:CNPJ", dest)
        dados["Destinatário Nome"] = get_text("nfe:xNome", dest)
        dados["Destinatário IE"] = get_text("nfe:IE", dest)
        # UF do destinatário com conversão (CRÍTICO para ICMS)
        uf_dest = get_text("nfe:enderDest/nfe:UF", dest)
        dados["Destinatário UF"] = converter_codigo_uf(uf_dest) if uf_dest != "0" else uf_dest
        dados["Destinatário Município"] = get_text("nfe:enderDest/nfe:xMun", dest)
        dados["Destinatário CEP"] = get_text("nfe:enderDest/nfe:CEP", dest)

    # --- TRANSPORTE ---
    transp = infNFe.find("nfe:transp", ns)
    if transp is not None:
        transporta = transp.find("nfe:transporta", ns)
        vol = transp.find("nfe:vol", ns)
        dados["Modalidade Frete"] = get_text("nfe:modFrete", transp)
        if transporta is not None:
            dados["Transportadora Nome"] = get_text("nfe:xNome", transporta)
            dados["Transportadora CNPJ"] = get_text("nfe:CNPJ", transporta)
            # UF da transportadora com conversão
            uf_transp = get_text("nfe:UF", transporta)
            dados["Transportadora UF"] = converter_codigo_uf(uf_transp) if uf_transp != "0" else uf_transp
        if vol is not None:
            dados["Qtde Volumes"] = get_text("nfe:qVol", vol)
            dados["Peso Líquido"] = get_text("nfe:pesoL", vol)
            dados["Peso Bruto"] = get_text("nfe:pesoB", vol)

    # --- COBRANÇA / FATURA ---
    cobr = infNFe.find("nfe:cobr", ns)
    if cobr is not None:
        fat = cobr.find("nfe:fat", ns)
        dup = cobr.find("nfe:dup", ns)
        if fat is not None:
            dados["Número Fatura"] = get_text("nfe:nFat", fat)
            dados["Valor Original"] = get_text("nfe:vOrig", fat)
            dados["Valor Líquido"] = get_text("nfe:vLiq", fat)
        if dup is not None:
            dados["Número Duplicata"] = get_text("nfe:nDup", dup)
            dados["Data Vencimento"] = get_text("nfe:dVenc", dup)
            dados["Valor Duplicata"] = get_text("nfe:vDup", dup)

    # --- TOTALIZAÇÃO ---
    total = infNFe.find(".//nfe:ICMSTot", ns)
    if total is not None:
        dados["Base ICMS"] = get_text("nfe:vBC", total)
        dados["Valor ICMS"] = get_text("nfe:vICMS", total)
        dados["Valor Produtos"] = get_text("nfe:vProd", total)
        dados["Valor NF"] = get_text("nfe:vNF", total)
        dados["Valor Frete"] = get_text("nfe:vFrete", total)
        dados["Valor IPI"] = get_text("nfe:vIPI", total)
        dados["Valor COFINS"] = get_text("nfe:vCOFINS", total)
        dados["Valor PIS"] = get_text("nfe:vPIS", total)

    # --- PRODUTOS ---
    produtos = []
    for det in infNFe.findall("nfe:det", ns):
        prod = det.find("nfe:prod", ns)
        imp = det.find("nfe:imposto", ns)
        if prod is not None:
            p = {
                "Item": det.attrib.get("nItem", "0"),
                "Código": get_text("nfe:cProd", prod),
                "Descrição": get_text("nfe:xProd", prod),
                "NCM": get_text("nfe:NCM", prod),
                "CFOP": get_text("nfe:CFOP", prod),
                "Unidade": get_text("nfe:uCom", prod),
                "Quantidade": get_text("nfe:qCom", prod),
                "Valor Unitário": get_text("nfe:vUnCom", prod),
                "Valor Total": get_text("nfe:vProd", prod),
            }
            if imp is not None:
                p["ICMS"] = get_text(".//nfe:vICMS", imp)
                p["IPI"] = get_text(".//nfe:vIPI", imp)
                p["PIS"] = get_text(".//nfe:vPIS", imp)
                p["COFINS"] = get_text(".//nfe:vCOFINS", imp)
            produtos.append(p)

    produtos_df = pd.DataFrame(produtos).fillna("0")
    cabecalho_df = pd.DataFrame([dados]).fillna("0")

    return cabecalho_df, produtos_df


# ==============================
# STREAMLIT INTERFACE
# ==============================