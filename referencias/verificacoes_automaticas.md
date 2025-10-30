# Verificações Automáticas

Este documento descreve as regras lógicas que o sistema pode usar para verificações automáticas.

- **Alíquota ICMS Interestadual**:
  - **Condição**: CFOP começa com '6' E UF de origem é diferente da UF de destino.
  - **Valores Esperados**: 4%, 7%, ou 12%.

- **Alíquota ICMS Interna**:
  - **Condição**: CFOP começa com '5' E UF de origem é igual à UF de destino.
  - **Valores por UF**: SP (18%), RJ (20%), MG (18%), etc.

- **Obrigatoriedade de ICMS-ST**:
  - **Condição**: O NCM do produto está na lista de NCMs sujeitos a ST.
  - **Ação**: Verificar se o ICMS-ST foi calculado na nota.

- **Regime Não-Cumulativo (PIS/COFINS)**:
  - **Condição**: Alíquota de PIS é 1.65% E alíquota de COFINS é 7.6%.
  - **Oportunidade**: Verificar se a empresa está aproveitando todos os créditos permitidos.

- **Isenção de PIS/COFINS**:
  - **Condição**: O NCM do produto está na lista de NCMs isentos.
  - **Valores Esperados**: Alíquotas de PIS/COFINS devem ser zero.

- **Obrigatoriedade de IPI**:
  - **Condição**: O NCM do produto está na lista de NCMs tributados pelo IPI.
  - **Ação**: Verificar se o IPI foi calculado na nota.

- **Consistência CFOP vs. UF**:
  - **Condição**: CFOP começa com '5' (interno) MAS a UF de origem é diferente da de destino.
  - **Alerta**: Inconsistência entre o CFOP e as UFs da operação.
