# Registro de Atendimentos — Assistente NovaTech (v2 — Corrigido)

**Data de geração:** 2026-06-06
**Versão anterior:** registro-atendimentos-novatech.md
**Motivo da revisão:** As três primeiras interações não utilizaram os multiplicadores regionais presentes na seção 2.1 dos documentos PROC-042 e PROC-042-v2, que estavam disponíveis na base de conhecimento. As respostas foram corrigidas para incorporar essa informação.
**Total de interações:** 5

---

## Nota sobre a correção

Nas interações 1, 2 e 3, a seção 2.1 (Multiplicadores regionais) foi referenciada na fórmula de cálculo mas não utilizada nas respostas anteriores, gerando escalações desnecessárias. Os valores corretos por versão são:

| Região | PROC-042 v1 [PROC-042-A] | PROC-042-v2 [PROC-042v2-A] | Versão aplicável |
|---|---|---|---|
| Sul | 1,2 | 1,3 | v2 |
| Sudeste | 1,0 | 1,1 | v2 |
| Centro-Oeste | 1,3 | 1,4 | v2 |
| **Nordeste** | **1,4** | **1,5** | **v2** |
| **Norte** | **1,6** | **1,8** | **v2** |

> **Regra aplicada:** Em conformidade com a Regra 5 do protocolo de atendimento, os multiplicadores da versão mais recente (PROC-042-v2, emitida em 10/11/2023) são utilizados para chamados novos a partir de 01/12/2023 [PROC-042v2 | 5]. Como a data atual é 2026-06-06, todos os chamados utilizam os valores da v2.

> **Conflito de versões — Fatores de peso:**
> - v1 [PROC-042-A]: 1,0 / 1,2 / 1,5
> - v2 [PROC-042v2-A]: 1,0 / 1,15 / 1,4
> Priorizada a v2. Para a faixa de 500 kg a 1.000 kg, ambas as versões convergem em **1,0** — sem impacto nas interações 1 e 3.

---

## Sumário

| # | Pergunta | Resultado (v1) | Resultado (v2 — Corrigido) | Escalação necessária |
|---|---|---|---|---|
| 1 | Frete 600 kg → Manaus | Parcial (sem multiplicador) | Parcial (multiplicador aplicado) | Sim — apenas valor base |
| 2 | Frete 300 kg → Salvador | Sem cobertura | Sem cobertura (300 kg < mínimo frete especial) | Sim |
| 3 | Frete 500 kg → Salvador | Parcial (sem multiplicador) | Parcial (multiplicador aplicado) | Sim — apenas valor base |
| 4 | SLA cliente Platinum | Tier inexistente | Inalterado | Sim |
| 5 | Devolução de carga perigosa | Não elegível | Inalterado | Sim (ramal 4500) |

---

## Interação 1 — Frete para 600 kg com destino a Manaus (CORRIGIDA)

**Pergunta do usuário:** Frete para 600kg para Manaus?

### Resposta corrigida

Manaus está localizada na **região Norte**. O cálculo de frete especial utiliza a fórmula [PROC-042v2-A]:

> **Valor do frete = Valor base × Multiplicador regional × Fator de peso**

Aplicando os parâmetros disponíveis:

| Componente | Valor | Fonte |
|---|---|---|
| Multiplicador regional (Norte) | **1,8** | [PROC-042v2 seção 2.1] |
| Fator de peso (500 kg–1.000 kg) | **1,0** | [PROC-042v2-A] |
| Valor base | **Não disponível** — requer tabela mensal vigente | — |

Portanto:

> **Valor do frete = Valor base × 1,8 × 1,0 = Valor base × 1,8**

O cálculo **não pode ser finalizado** sem o valor base da tabela mensal de fretes.

O prazo de entrega vigente é: **prazo padrão da rota + 3 dias úteis** [PROC-042v2-C].

### O que mudou em relação à resposta anterior

| Ponto | Resposta anterior | Resposta corrigida |
|---|---|---|
| Multiplicador regional | "Não disponível nos chunks" | **1,8** (Norte, v2) aplicado |
| Escalação | Supervisor + Comercial (multiplicador + valor base) | Apenas valor base — multiplicador já disponível |

### Fontes utilizadas

| Fonte | Conteúdo |
|---|---|
| [PROC-042v2-A] | Fórmula de cálculo e fator de peso |
| [PROC-042v2 seção 2.1] | Multiplicador regional — Norte: 1,8 |
| [PROC-042v2-C] | Prazo de entrega (versão mais recente) |
| [PROC-042v2 seção 5] | Disposição transitória: v2 aplica-se a chamados a partir de 01/12/2023 |

### Observações de risco

> **Conflito de multiplicadores entre versões:** v1 define Norte = 1,6; v2 define Norte = 1,8. Priorizada a v2 (mais recente, emitida 10/11/2023). [PROC-042v2 seção 5]

> **Conflito de prazo entre versões:** v1 = +2 dias úteis [PROC-042-C]; v2 = +3 dias úteis [PROC-042v2-C]. Priorizada a v2.

> **Pendência:** Valor base (tabela mensal) ainda ausente. Consultar supervisor ou Comercial apenas para esse dado.

---

## Interação 2 — Frete para 300 kg com destino a Salvador (INALTERADA)

**Pergunta do usuário:** Frete para 300kg para Salvador?

### Resposta

**Não encontrei essa informação na base oficial consultada.**

Embora o multiplicador regional do Nordeste esteja disponível (Salvador → Nordeste → 1,5 em v2 [PROC-042v2 seção 2.1]), o frete especial é aplicável **apenas a cargas com peso acima de 500 kg** [PROC-042v1 seção 1 / PROC-042v2 seção 1]. Uma carga de 300 kg não se enquadra nessa modalidade.

Não há nos documentos disponíveis informações sobre cálculo de frete **padrão** (abaixo de 500 kg).

### O que mudou em relação à resposta anterior

| Ponto | Resposta anterior | Resposta corrigida |
|---|---|---|
| Motivo da impossibilidade de cálculo | Falta de fórmula, multiplicador e valor base | Explicitado que 300 kg < mínimo exigido para frete especial (500 kg) — multiplicador identificado, mas inaplicável |
| Fundamentação | Genérica | Embasada no escopo do PROC-042 |

### Fontes utilizadas

| Fonte | Conteúdo |
|---|---|
| [PROC-042v1 seção 1] | Escopo: frete especial aplica-se a cargas acima de 500 kg |
| [PROC-042v2 seção 2.1] | Multiplicador Nordeste identificado (1,5), porém inaplicável para esta faixa |

### Observações de risco

> **Escalação necessária:** Consultar supervisor ou Comercial para obter tabela e regras de frete padrão (abaixo de 500 kg). A ausência dessa informação na base de conhecimento configura lacuna documental relevante.

---

## Interação 3 — Frete para 500 kg com destino a Salvador (CORRIGIDA)

**Pergunta do usuário:** Frete para 500kg para Salvador?

### Resposta corrigida

Salvador está localizada na **região Nordeste**. O cálculo de frete especial utiliza a fórmula [PROC-042-A]:

> **Valor do frete = Valor base × Multiplicador regional × Fator de peso**

Aplicando os parâmetros disponíveis:

| Componente | Valor | Fonte |
|---|---|---|
| Multiplicador regional (Nordeste) | **1,5** | [PROC-042v2 seção 2.1] |
| Fator de peso (500 kg–1.000 kg) | **1,0** | [PROC-042v2-A] |
| Valor base | **Não disponível** — requer tabela mensal vigente | — |

Portanto:

> **Valor do frete = Valor base × 1,5 × 1,0 = Valor base × 1,5**

O cálculo **não pode ser finalizado** sem o valor base da tabela mensal de fretes.

O prazo de entrega vigente é: **prazo padrão da rota + 3 dias úteis** [PROC-042v2-C].

### O que mudou em relação à resposta anterior

| Ponto | Resposta anterior | Resposta corrigida |
|---|---|---|
| Multiplicador regional | "Não disponível nos chunks" | **1,5** (Nordeste, v2) aplicado |
| Escalação | Supervisor + Comercial (multiplicador + valor base) | Apenas valor base — multiplicador já disponível |

### Fontes utilizadas

| Fonte | Conteúdo |
|---|---|
| [PROC-042-A] | Fórmula de cálculo e fator de peso |
| [PROC-042v2 seção 2.1] | Multiplicador regional — Nordeste: 1,5 |
| [PROC-042v2-C] | Prazo de entrega (versão mais recente) |
| [PROC-042v2 seção 5] | Disposição transitória: v2 aplica-se a chamados a partir de 01/12/2023 |

### Observações de risco

> **Conflito de multiplicadores entre versões:** v1 define Nordeste = 1,4; v2 define Nordeste = 1,5. Priorizada a v2 (mais recente). [PROC-042v2 seção 5]

> **Conflito de prazo entre versões:** v1 = +2 dias úteis [PROC-042-C]; v2 = +3 dias úteis [PROC-042v2-C]. Priorizada a v2.

> **Pendência:** Valor base (tabela mensal) ainda ausente. Consultar supervisor ou Comercial apenas para esse dado.

---

## Interação 4 — SLA do cliente Platinum (INALTERADA)

**Pergunta do usuário:** Qual o SLA do cliente Platinum?

### Resposta

**O tier Platinum não existe na NovaTech.** Os tiers vigentes são: **Gold, Silver e Standard**. O tier Platinum fazia parte de um programa de fidelidade descontinuado em 2022. [FAQ-15]

**Ação recomendada:** Solicitar o número do contrato para verificar o tier correto.

Os valores de SLA por tier não constavam nos chunks disponíveis — o documento SLA-2024 foi recuperado apenas em seu cabeçalho e seção de medição, sem a tabela de SLAs.

### Fontes utilizadas

| Fonte | Conteúdo |
|---|---|
| [FAQ-15] | Inexistência do tier Platinum; tiers vigentes |
| [SLA-2024] | Documento identificado; tabela de SLAs por tier não disponível nos chunks |

### Observações de risco

> Informar SLA de um tier inexistente configuraria erro de atendimento. Escalar ao supervisor para consulta ao SLA-2024 completo.

---

## Interação 5 — Devolução de carga perigosa (INALTERADA)

**Pergunta do usuário:** Posso devolver carga perigosa?

### Resposta

**Não.** Cargas perigosas classificadas nas **classes 1 a 6 da ANTT** não são elegíveis para devolução pelo processo padrão, conforme Resolução ANTT nº 5.947/2021. [POL-001-A]

| Classe | Tipo |
|---|---|
| Classe 1 | Explosivos |
| Classe 2 | Gases |
| Classe 3 | Líquidos inflamáveis |
| Classe 4 | Sólidos inflamáveis |
| Classe 5 | Oxidantes e peróxidos orgânicos |
| Classe 6 | Substâncias tóxicas e infectantes |

**Ação obrigatória:** Encaminhar ao setor de **Gestão de Riscos** pelo **ramal 4500**. [POL-001-A]

### Fontes utilizadas

| Fonte | Conteúdo |
|---|---|
| [POL-001-A] | Exceções ao prazo geral — cargas não elegíveis para devolução padrão |

### Observações de risco

> Restrição com base regulatória (Resolução ANTT nº 5.947/2021) — o atendente não possui autonomia para excepcionar. Encaminhamento ao ramal 4500 é mandatório.

---

## Consolidado de parâmetros aplicáveis (para referência)

### Multiplicadores regionais vigentes — PROC-042-v2 (aplicável a chamados a partir de 01/12/2023)

| Região | Multiplicador v1 | Multiplicador v2 | Diferença |
|---|---|---|---|
| Sul | 1,2 | 1,3 | +0,1 |
| Sudeste | 1,0 | 1,1 | +0,1 |
| Centro-Oeste | 1,3 | 1,4 | +0,1 |
| **Nordeste** | **1,4** | **1,5** | **+0,1** |
| **Norte** | **1,6** | **1,8** | **+0,2** |

### Fatores de peso vigentes — PROC-042-v2

| Faixa | Fator |
|---|---|
| 500 kg a 1.000 kg | 1,0 |
| 1.001 kg a 3.000 kg | 1,15 |
| Acima de 3.000 kg | 1,4 |

> **Nota:** O frete especial aplica-se **apenas a cargas acima de 500 kg**. Cargas abaixo desse peso devem ser tratadas como frete padrão — cujas regras e tarifas não constam nos documentos disponíveis.

---

## Lição aprendida — Falha de cobertura de chunks

A principal falha identificada nas interações 1 e 3 foi a ausência do chunk correspondente à **seção 2.1** dos documentos PROC-042 e PROC-042-v2 no conjunto de chunks recuperados pelo sistema RAG. A seção 2.1 é diretamente relevante para qualquer pergunta sobre frete com destino especificado, e sua não recuperação gerou respostas incompletas com escalações desnecessárias.

**Recomendação:** Incluir a seção 2.1 como chunk fixo (ou de alta prioridade) em qualquer consulta que envolva cálculo de frete especial.

---

*Documento gerado pelo Assistente de Atendimento NovaTech — versão corrigida em 2026-06-06.*
