# Fórmulas de Cálculo Fiscal

## PIS/COFINS

### Regime Cumulativo
- **PIS**: `Receita_Bruta * 0.0065`
- **COFINS**: `Receita_Bruta * 0.03`

### Regime Não-Cumulativo
- **PIS**: `(Receita_Bruta * 0.0165) - (Base_Calculo_Creditos * 0.0165)`
- **COFINS**: `(Receita_Bruta * 0.076) - (Base_Calculo_Creditos * 0.076)`

## ICMS

### ICMS Normal
- **Fórmula**: `Valor_da_Operacao * Aliquota_ICMS_Interna_ou_Interestadual`

### ICMS ST (Substituição Tributária)
- **ICMS Próprio**: `(Valor_do_Produto + IPI + Frete + Outras_Despesas) * Aliquota_ICMS_Interna`
- **Base de Cálculo ST**: `(Valor_do_Produto + IPI + Frete + Outras_Despesas) * (1 + MVA_Original_ou_Ajustada)`
- **ICMS ST Devido**: `(Base_Calculo_ST * Aliquota_ICMS_Interna) - ICMS_Proprio`

### MVA Ajustada
- **Fórmula**: `MVA_Ajustada = [(1 + MVA_Original) * (Alíquota_Interna / Alíquota_Interestadual)] - 1`
