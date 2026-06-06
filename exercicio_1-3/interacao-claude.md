# Registro de Atendimentos — Assistente NovaTech

**Data de geração:** 2026-06-06
**Sistema:** Assistente de Atendimento NovaTech (Logística)
**Total de interações:** 5

---

## Sumário

| # | Pergunta | Resultado | Escalação necessária |
|---|---|---|---|
| 1 | Frete 600 kg → Manaus | Parcial — fator de peso identificado | Sim |
| 2 | Frete 300 kg → Salvador | Sem cobertura | Sim |
| 3 | Frete 500 kg → Salvador | Parcial — fator de peso identificado | Sim |
| 4 | SLA cliente Platinum | Tier inexistente | Sim |
| 5 | Devolução de carga perigosa | Respondida — não elegível | Sim (Gestão de Riscos) |

---

## Interação 1 — Frete para 600 kg com destino a Manaus

**Pergunta do usuário:** Frete para 600kg para Manaus?

### Resposta

O cálculo de frete especial utiliza a fórmula:

> **Valor do frete = Valor base × Multiplicador regional × Fator de peso**

Para 600 kg, o **Fator de peso = 1,0** (faixa de 500 kg a 1.000 kg).

O cálculo final **não pôde ser concluído** por ausência, nos chunks consultados, do valor base (tabela mensal) e do multiplicador regional de Manaus (seção 2.1).

O prazo de entrega vigente é: **prazo padrão da rota + 3 dias úteis**.

### Fontes utilizadas

| Fonte | Conteúdo |
|---|---|
| [PROC-042v2-A] | Fórmula de cálculo e fatores de peso |
| [PROC-042v2-C] | Prazo de entrega — versão mais recente |

### Observações de risco

- **Conflito de versões:** [PROC-042-C] indicava **+2 dias úteis**; [PROC-042v2-C] estabelece **+3 dias úteis**. Priorizada a versão mais recente.
- **Escalação recomendada:** Consultar supervisor ou Comercial para obter tabela mensal e multiplicador regional do Norte.

---

## Interação 2 — Frete para 300 kg com destino a Salvador

**Pergunta do usuário:** Frete para 300kg para Salvador?

### Resposta

**Não encontrei essa informação na base oficial consultada.**

Os chunks disponíveis não continham:
- Fórmula de cálculo para cargas de 300 kg
- Enquadramento da carga (padrão ou especial)
- Valor base ou multiplicador regional para Salvador
- Fatores de peso para a faixa abaixo de 500 kg

### Fontes utilizadas

Nenhum chunk disponível cobriu esta consulta de forma suficiente.

### Observações de risco

- **Cobertura insuficiente:** Os documentos recuperados tratavam de prazos, devoluções, seguro e descontos — nenhum abrangia cálculo de frete para essa faixa de peso ou destino.
- **Escalação obrigatória:** Encaminhar ao supervisor ou Comercial, informando peso (300 kg) e destino (Salvador).

---

## Interação 3 — Frete para 500 kg com destino a Salvador

**Pergunta do usuário:** Frete para 500kg para Salvador?

### Resposta

O cálculo de frete especial utiliza a fórmula:

> **Valor do frete = Valor base × Multiplicador regional × Fator de peso**

Para 500 kg, o **Fator de peso = 1,0** (faixa de 500 kg a 1.000 kg).

O cálculo final **não pôde ser concluído** por ausência, nos chunks consultados, do valor base (tabela mensal) e do multiplicador regional de Salvador (seção 2.1).

O prazo de entrega vigente é: **prazo padrão da rota + 3 dias úteis**.

### Fontes utilizadas

| Fonte | Conteúdo |
|---|---|
| [PROC-042-A] | Fórmula de cálculo e fatores de peso |
| [PROC-042v2-C] | Prazo de entrega — versão mais recente |

### Observações de risco

- **Conflito de versões:** [PROC-042-C] indicava **+2 dias úteis**; [PROC-042v2-C] estabelece **+3 dias úteis**. Priorizada a versão mais recente.
- **Escalação recomendada:** Consultar supervisor ou Comercial para obter tabela mensal e multiplicador regional de Salvador.

---

## Interação 4 — SLA do cliente Platinum

**Pergunta do usuário:** Qual o SLA do cliente Platinum?

### Resposta

O tier **Platinum não existe na NovaTech**. Os tiers vigentes são exclusivamente:

- **Gold**
- **Silver**
- **Standard**

O cliente pode estar confundindo com outra transportadora ou com o programa de fidelidade antigo, **descontinuado em 2022**.

**Ação recomendada:** Solicitar o número do contrato para verificar o tier correto cadastrado no sistema.

Os valores específicos de SLA por tier não constavam nos chunks disponíveis — o documento SLA-2024 foi recuperado apenas em seu cabeçalho e seção de medição.

### Fontes utilizadas

| Fonte | Conteúdo |
|---|---|
| [FAQ-15] | Inexistência do tier Platinum; tiers vigentes |
| [SLA-2024] | Documento identificado, sem tabela de SLAs por tier nos chunks |

### Observações de risco

- **Tier inválido:** Informar SLA de um tier inexistente configuraria erro de atendimento.
- **Cobertura insuficiente para SLA:** Mesmo para tiers válidos, os valores não estavam disponíveis. Escalação ao supervisor para consulta ao documento contratual completo.

---

## Interação 5 — Devolução de carga perigosa

**Pergunta do usuário:** Posso devolver carga perigosa?

### Resposta

**Não.** Cargas perigosas classificadas nas **classes 1 a 6 da ANTT** não são elegíveis para devolução pelo processo padrão, conforme Resolução ANTT nº 5.947/2021.

| Classe | Tipo |
|---|---|
| Classe 1 | Explosivos |
| Classe 2 | Gases |
| Classe 3 | Líquidos inflamáveis |
| Classe 4 | Sólidos inflamáveis |
| Classe 5 | Oxidantes e peróxidos orgânicos |
| Classe 6 | Substâncias tóxicas e infectantes |

**Ação obrigatória:** Encaminhar o cliente ao setor de **Gestão de Riscos** pelo **ramal 4500** para tratamento individualizado.

### Fontes utilizadas

| Fonte | Conteúdo |
|---|---|
| [POL-001-A] | Exceções ao prazo geral — cargas não elegíveis para devolução padrão |

### Observações de risco

- **Caráter regulatório:** A restrição tem base na Resolução ANTT nº 5.947/2021 — não é apenas uma regra operacional interna.
- **Sem autonomia do atendente:** O encaminhamento ao ramal 4500 é mandatório. O atendente não pode processar ou excepcionar esse tipo de solicitação.

---

## Padrões identificados nas interações

### Limitações recorrentes dos chunks recuperados

1. **Multiplicadores regionais ausentes:** Em todas as perguntas de cálculo de frete, a seção 2.1 (multiplicadores por região) não estava disponível, impedindo o cálculo do valor final.
2. **Tabela mensal de fretes ausente:** O valor base nunca estava nos chunks, tornando o cálculo sempre incompleto.
3. **Conflito de versões PROC-042:** Os chunks de v1 e v2 coexistiram em múltiplas interações, exigindo aplicação da Regra 5 (priorizar versão mais recente).

### Escalações necessárias

| Interação | Destino de escalação |
|---|---|
| 1, 2, 3 | Supervisor / Comercial (tabela de fretes e multiplicadores regionais) |
| 4 | Supervisor (tabela de SLA completa) |
| 5 | Gestão de Riscos — ramal 4500 |

---

*Documento gerado pelo Assistente de Atendimento NovaTech com base nas interações registradas em 2026-06-06.*
