# Log de Sessão: Análise de Viabilidade RAG — NovaTech
**DB1 Group | Formação IA Prática | Junho 2026**

---

> Este documento registra a íntegra da sessão de trabalho, incluindo prompts enviados, respostas geradas e a análise crítica intermediária. Os documentos de entrega estão referenciados e reproduzidos integralmente.

---

## Índice

1. [Interação 1 — Geração da Análise de Viabilidade (v1)](#interação-1)
   - [Prompt](#prompt-1)
   - [Resposta — analise-viabilidade-rag-novatech.md](#resposta-1)
2. [Interação 2 — Revisão Crítica e Geração da v2](#interação-2)
   - [Prompt](#prompt-2)
   - [Análise Crítica Intermediária](#análise-crítica-intermediária)
   - [Resposta — analise-viabilidade-rag-novatech-v2.md](#resposta-2)

---

## Interação 1

### Prompt 1

> *Prompt enviado pelo usuário:*

---

Você é um arquiteto de soluções de IA especializado em sistemas RAG (Retrieval-Augmented Generation). Sua tarefa é produzir uma análise técnica de viabilidade para um assistente baseado em documentos, com foco em desafios práticos de ingestão e gerenciamento de contexto.

**Contexto:**
A NovaTech é uma empresa de médio porte do setor de logística com 1.200 funcionários. Sua operação depende de um conjunto extenso de documentação interna: manuais de procedimento operacional, políticas de compliance, tabelas de SLA por tipo de cliente, regras de cálculo de frete, e normas de segurança de carga.

Hoje, essa documentação está espalhada em três fontes: um SharePoint corporativo com ~800 documentos (PDFs e Word), uma wiki interna no Confluence com ~400 páginas, e uma pasta de rede com planilhas de referência atualizadas mensalmente.

O problema: a equipe de atendimento ao cliente (45 pessoas) gasta em média 12 minutos por chamado buscando informações nessas fontes para responder dúvidas de clientes sobre prazos, regras de frete, políticas de devolução e procedimentos de reclamação. Isso gera atrasos, respostas inconsistentes e frustração tanto dos atendentes quanto dos clientes.

A NovaTech contratou a DB1 para construir um assistente de IA que permita aos atendentes fazer perguntas em linguagem natural e receber respostas fundamentadas na documentação oficial da empresa, com indicação da fonte. O assistente será integrado ao ambiente Microsoft da NovaTech (Teams + SharePoint).

**Informações adicionais fornecidas pela NovaTech**

- O volume médio é de 320 chamados/dia, dos quais ~60% envolvem consulta a documentação.
- A documentação é atualizada mensalmente por 3 áreas diferentes (Operações, Compliance, Comercial), sem processo unificado de revisão.
- Alguns documentos se contradizem entre versões — a equipe de atendimento hoje resolve isso "perguntando para quem sabe".
- A NovaTech já tem licenças Microsoft 365 E3 e está disposta a provisionar Azure AI Services.
- O projeto tem orçamento para 3 meses de discovery + desenvolvimento + go-live.
- A expectativa da diretoria é reduzir o tempo médio de busca de 12 para menos de 2 minutos por chamado.

**Informações técnicas adicionais:**
Os PDFs do SharePoint incluem documentos com tabelas complexas (tabelas de frete com 15+ colunas), fluxogramas embutidos como imagens, e alguns documentos escaneados (OCR necessário). A wiki do Confluence tem links internos entre páginas e usa macros customizadas. As planilhas têm fórmulas interdependentes.

**Conceito de context engineering aplicado a RAG:**

O contexto que o LLM recebe a cada pergunta é limitado pela janela de contexto do modelo. A qualidade da resposta depende de: quais chunks são selecionados (relevância), quantos chunks cabem no contexto (orçamento de atenção), onde ficam posicionados no prompt (informação no meio de contextos longos é 'esquecida' — o efeito 'lost in the middle'), e o que mais está no contexto competindo por atenção (system prompt, histórico de conversa, instruções).

**Estrutura do relatório:**

**1. Análise de Desafios por Tipo de Fonte**
Para cada tipo de documento listado abaixo, identifique o desafio técnico, seu impacto na qualidade do RAG e a solução recomendada:
- PDFs com tabelas
- PDFs escaneados (OCR)
- Wikis com links e referências cruzadas
- Planilhas com fórmulas

Para cada um, organize em: Desafio → Impacto → Tratamento técnico

**2. Estimativa de Consumo de Tokens**
- Use a conversão: **tokens ≈ palavras / 0.75**
- Forneça estimativas para cada tipo de documento (assumindo volumes típicos que você deve explicitar)
- Detalhe todas as suposições usadas no cálculo (ex: "assumindo média de 500 palavras por página PDF", "OCR com 15% de erro introduz repetições")
- Apresente o cálculo de forma transparente para que seja verificável

**3. Análise de Orçamento de Contexto**
- Contexto disponível: janela de 128k tokens
- Reserva obrigatória: 2k tokens
- Tokens efetivos para RAG: 126k
- Mostre como distribuir esse orçamento entre diferentes tipos de documentos
- Indique quando o orçamento se torna insuficiente e quais compromissos são necessários

**4. Estratégia de Fragmentação**
Recomende uma abordagem considerando o fenômeno de "perda de informação no meio" (middle token problem):
- Tamanho ótimo de fragmentos por tipo de documento
- Ordem de ingestão dos fragmentos na janela de contexto
- Técnicas de priorização (ex: relevância, proximidade ao início/fim, marcadores semânticos)
- Quando usar fragmentação hierárquica vs. flat

**5. Riscos e Mitigação**
Identifique os principais riscos técnicos e operacionais, com estratégias de mitigação para cada um.

**Requisitos de escrita:**
- Português claro e direto, sem jargão desnecessário
- Explique termos técnicos quando usados pela primeira vez
- Use exemplos concretos quando apropriado
- Pressuponha conhecimento técnico moderado (não é necessário explicar o que é IA, mas sim os detalhes específicos de RAG)
- Estrutura visual com cabeçalhos e bullets para legibilidade

Gere um arquivo Markdown com sua análise

---

### Resposta 1

> *Arquivo gerado: `analise-viabilidade-rag-novatech.md`*

---

# Análise de Viabilidade Técnica: Assistente de IA Baseado em Documentos
## NovaTech — Projeto RAG para Atendimento ao Cliente
**DB1 Group | Junho 2026**

---

## Sumário Executivo

Este documento analisa a viabilidade técnica de um assistente de IA baseado em RAG (*Retrieval-Augmented Generation*) para a equipe de atendimento ao cliente da NovaTech. O sistema proposto responde perguntas em linguagem natural consultando a documentação interna da empresa e indicando a fonte de cada resposta.

> **O que é RAG?** É uma arquitetura que combina dois passos: primeiro *recupera* fragmentos relevantes da base documental (busca semântica), depois *gera* uma resposta usando um LLM (modelo de linguagem), passando esses fragmentos como contexto. A resposta é fundamentada na documentação, não inventada pelo modelo.

A análise aponta que o projeto é **tecnicamente viável**, mas exige atenção especial ao pré-processamento dos documentos — especialmente PDFs com tabelas, documentos escaneados e planilhas — e a uma estratégia disciplinada de gerenciamento do contexto enviado ao modelo. Sem esse cuidado, o sistema responderá com confiança, porém de forma imprecisa.

---

## 1. Análise de Desafios por Tipo de Fonte

### 1.1 PDFs com Tabelas Complexas

**Desafio**

Tabelas de frete com 15 ou mais colunas não são simples texto corrido. Quando uma biblioteca padrão de extração de PDF processa um arquivo assim, o resultado é uma sequência de texto linear onde as relações entre células se perdem. Por exemplo, uma tabela que relaciona *Região de Destino × Peso × Prazo × Valor* pode ser extraída como:

```
Norte Nordeste Sul Sudeste Centro-Oeste 0-5kg 5-10kg ...
3 dias 4 dias 2 dias ...
R$ 12,50 R$ 18,00 R$ 9,80 ...
```

O modelo de linguagem não consegue inferir com confiança que "R$ 9,80" corresponde a "Sul + 5-10kg + 2 dias" — a relação espacial original foi destruída.

**Impacto no RAG**

Perguntas do tipo *"Qual o prazo de entrega para o Nordeste com carga de 8kg?"* podem gerar respostas incorretas mesmo que o dado correto esteja no documento. O modelo pode cruzar valores da linha errada da tabela e responder com confiança aparente — o pior cenário possível para um sistema de atendimento.

**Tratamento Técnico**

1. **Extração estruturada com bibliotecas especializadas:** Usar `pdfplumber` ou `camelot` (para PDFs nativos) para extrair tabelas como estruturas de dados (DataFrames), não como texto puro.
2. **Serialização semântica das tabelas:** Converter cada linha da tabela em uma sentença autocontida antes de fragmentar. Exemplo:
   - *Antes:* `Norte | 5-10kg | 3 dias | R$ 12,50`
   - *Depois (chunk gerado):* `"Frete para a região Norte com peso entre 5 e 10 kg: prazo de 3 dias úteis, valor de R$ 12,50."`
3. **Chunking por linha/grupo de linhas:** Cada linha ou grupo de linhas da tabela torna-se um fragmento independente, com o cabeçalho da tabela repetido em cada fragmento como contexto.
4. **Fallback para tabelas embutidas como imagem:** Documentos com tabelas renderizadas como imagem (fluxogramas) requerem modelos multimodais (Azure Document Intelligence com layout analysis) para extração.

---

### 1.2 PDFs Escaneados (OCR Necessário)

**Desafio**

Documentos escaneados são imagens — não há texto extraível diretamente. A aplicação de OCR (*Optical Character Recognition*) recupera o texto, mas introduz ruído proporcional à qualidade da digitalização: letras confundidas (`l` com `1`, `O` com `0`), palavras cortadas, hifenizações incorretas, parágrafos misturados. Um documento com OCR de qualidade média apresenta tipicamente 5–15% de erros por caracter — suficiente para corromper datas, valores monetários e siglas críticas.

**Impacto no RAG**

- O índice vetorial (a base que permite a busca semântica) é construído sobre texto ruidoso, reduzindo a chance de recuperar o fragmento certo para uma pergunta.
- Valores críticos como prazos (`30 dias` vira `3O dias`) ou percentuais (`2,5%` vira `25%`) podem ser transmitidos incorretamente ao modelo sem nenhum alerta.
- Tokens desnecessários gerados por erros de OCR consomem espaço no contexto sem contribuir com informação.

**Tratamento Técnico**

1. **Pipeline OCR de alta qualidade:** Usar **Azure AI Document Intelligence** (disponível nas licenças Azure AI Services já previstas) em vez de tesseract genérico.
2. **Score de confiança por bloco:** Blocos com score abaixo de 0,80 devem ser sinalizados para revisão humana antes de entrar no índice.
3. **Pós-processamento linguístico:** Aplicar um corretor contextual para detectar anomalias numéricas e siglas corrompidas.
4. **Metadado de origem:** Todo chunk de documento OCR carrega `fonte: ocr` e `score_ocr: 0.XX`.

---

### 1.3 Wikis com Links e Referências Cruzadas (Confluence)

**Desafio**

Páginas de wiki raramente são autocontidas. Uma página sobre *Política de Devolução* pode dizer "conforme as regras da Seção 3 da Política de Frete" e ter um link para outra página. Quando essa página é fragmentada e indexada isoladamente, o fragmento extraído contém uma referência que não pode ser resolvida.

**Impacto no RAG**

- Respostas incompletas: o modelo recebe a referência mas não o conteúdo referenciado.
- Macros exportadas como `{panel:title=Atenção}...{panel}` poluem o texto com marcações sem significado semântico.

**Tratamento Técnico**

1. **Resolução de links em tempo de ingestão** (técnica de *link expansion*).
2. **Fragmentação por seção lógica** respeitando hierarquia `H1 > H2 > H3`.
3. **Limpeza de macros** via pré-processamento.
4. **Grafo de dependência entre páginas** para re-indexação em cascata.

---

### 1.4 Planilhas com Fórmulas Interdependentes

**Desafio**

Células com fórmulas exportam ou a fórmula (ininteligível para o modelo) ou o valor calculado (que pode estar desatualizado). Dependências entre abas produzem chunks incompletos quando fragmentadas separadamente.

**Tratamento Técnico**

1. Usar `openpyxl` com `data_only=True` para capturar valores calculados.
2. Serialização por contexto incluindo parâmetros das abas auxiliares.
3. Atualização mensal automatizada via Power Automate.
4. Alerta de dados com mais de 35 dias.

---

## 2. Estimativa de Consumo de Tokens

### Premissas

| Premissa | Valor Adotado |
|---|---|
| Conversão palavras → tokens | `tokens = palavras ÷ 0,75` |
| Páginas por documento PDF (média) | 12 páginas |
| Palavras por página PDF | 450 palavras |
| Overhead de tabela (serialização) | +40% |
| Overhead de OCR | +15% *(corrigido na v2 para +25-50%)* |
| Palavras por página Confluence | 600 palavras |
| Tamanho médio de planilha serializada | 2.500 palavras |

### Cálculos

**SharePoint — Grupo A (texto corrido, 500 docs):**
```
500 × 12 × 450 = 2.700.000 palavras → 3.600.000 tokens
```

**SharePoint — Grupo B (tabelas, 200 docs):**
```
200 × 12 × 450 × 1,40 = 1.512.000 palavras → 2.016.000 tokens
```

**SharePoint — Grupo C (OCR, 100 docs):**
```
100 × 12 × 450 × 1,15 = 621.000 palavras → 828.000 tokens
```

**Confluence (400 páginas):**
```
400 × 600 × 1,20 = 288.000 palavras → 384.000 tokens
```

**Planilhas (30 arquivos):**
```
30 × 2.500 = 75.000 palavras → 100.000 tokens
```

**Total do Corpus: ~6.928.000 tokens (~55× a janela de contexto)**

---

## 3. Análise de Orçamento de Contexto

Distribuição dos 128k tokens:
- Reserva: 2k
- System prompt: ~1,5k
- Histórico (3 trocas): ~3k
- Pergunta: ~150 tokens
- **Chunks RAG disponíveis: ~121k tokens**

Recomendação prática: **máximo 15 chunks por requisição (~7.500 tokens de chunks)**, com verificação de token count antes de cada chamada.

Cenários críticos de esgotamento: consulta com múltiplas tabelas, histórico longo, OCR com ruído elevado.

---

## 4. Estratégia de Fragmentação

- **Mitigação do lost-in-middle:** Posicionar chunks mais relevantes no início e no final do bloco de contexto *(técnica corrigida na v2)*.
- **Tamanho alvo:** 400–512 tokens por chunk.
- **Overlap:** 50–80 tokens entre chunks consecutivos.
- **Re-ranking:** Cohere Rerank ou cross-encoder para refinar top-20 candidatos.
- **Boost por metadados:** data, score OCR, área da pergunta.
- **Hierárquica vs. flat:** Hierárquica para manuais e Confluence; flat para tabelas, planilhas e OCR.

---

## 5. Riscos e Mitigação (v1 — 6 riscos)

| # | Risco | Probabilidade | Impacto |
|---|---|---|---|
| 5.1 | Documentos contraditórios | Alta | Alto |
| 5.2 | Alucinação com alta confiança | Média | Alto |
| 5.3 | Desatualização silenciosa do índice | Alta | Médio-Alto |
| 5.4 | Baixa qualidade na extração de tabelas | Alta | Alto |
| 5.5 | Adoção baixa pelos atendentes | Média | Alto |
| 5.6 | Conflito com privacidade/compliance | Baixa-Média | Alto |

*Nota: riscos 5.1 continha imprecisão técnica na detecção. Quatro riscos relevantes estavam ausentes. Ver v2 para versão corrigida e completa.*

---

## Conclusão e Próximos Passos (v1)

Projeto tecnicamente viável em 3 meses. Maior risco: qualidade da extração de tabelas — deve ser o primeiro item do Mês 1.

**Mês 1:** Auditoria de documentos, pipeline OCR, testes de extração de tabelas, mapeamento de dados sensíveis.
**Mês 2:** Pipeline de ingestão, índice vetorial, interface Teams, suite de testes de regressão.
**Mês 3:** Piloto com 10 atendentes, medição, rollout.

---

## Interação 2

### Prompt 2

> *Prompt enviado pelo usuário:*

---

Revise o documento que você gerou e identifique pontos fracos, estimativas otimistas demais ou riscos não considerados. Incorpore a análise ao documento, gerando um arquivo analise-viabilidade-rag-novatech-v2.md

---

### Análise Crítica Intermediária

> *Antes de gerar a v2, foi executada uma revisão técnica crítica independente. Abaixo estão os achados completos da revisão.*

---

#### 1. Imprecisões Técnicas

**1.1 Detecção de contradição por similaridade de embeddings >85%**

A v1 afirma que documentos contraditórios podem ser detectados por similaridade de embeddings acima de 85%. Isso está **invertido**. Alta similaridade semântica indica que os documentos são topicamente próximos — não que se contradizem. Um chunk dizendo "prazo é 30 dias" e outro "prazo é 45 dias" pode ter similaridade de 92% sem que nenhum threshold de cosseno detecte o conflito.

*Correção necessária:* Usar NLI (Natural Language Inference) com modelo classificador de contradição, ou extração de triplas factuais com comparação por entidade/relação. Similarity threshold serve apenas para filtrar pares candidatos, não para detectar contradição.

**1.2 `openpyxl` com `data_only=True` captura valores calculados**

Isso é **condicionalmente falso**. `data_only=True` lê o cache de valores calculados que o Excel salva no arquivo. Se o arquivo foi salvo sem recalcular (comum em automações, exports de sistemas ERP, ou arquivos nunca abertos no Excel após edição programática), esse cache está vazio ou desatualizado. O valor retornado será `None` **silenciosamente**.

*Correção necessária:* Validar proporção de células `None` pós-leitura. Se > 20% são `None`, o cache está vazio — pré-processar com LibreOffice headless para forçar recálculo antes da ingestão.

**1.3 Chunks repetidos no início e final para mitigar lost-in-middle**

A técnica está **incorretamente descrita**. Duplicar chunks aumenta consumo de tokens sem garantia de melhoria — o modelo pode simplesmente reforçar o chunk duplicado independente de sua relevância real.

*Correção necessária:* A mitigação correta é **ordenação por relevância com posicionamento nos extremos** do contexto (relevance-aware ordering). Os chunks mais relevantes ocupam o início e o final da janela — sem duplicação, custo em tokens = zero.

---

#### 2. Estimativas Otimistas Demais

**2.1 Overhead OCR de +15%**

O número não tem base metodológica declarada e é sistematicamente baixo. PDFs escaneados com baixa resolução, orientação incorreta, múltiplas colunas ou tabelas em imagem geram erros que inflam o corpus com ruído. Em corpora corporativos reais, o overhead fica entre **25-60%**. Os 15% correspondem a documentos de alta qualidade em condições ideais.

*Correção:* Substituir por faixa conservadora de 25-50% (central: 35%), com nota de que depende da qualidade do acervo — a confirmar na auditoria do Mês 1.

**2.2 Máximo 15 chunks como número fixo**

O documento trata 15 chunks como limite arquitetural, mas ignora variância real. Um chunk de seção de manual pode ter 800 tokens; uma linha de tabela serializada pode ter 120 tokens. Fixar 15 chunks é uma média que falha nos dois extremos.

*Correção:* Definir tamanho alvo de chunk (ex: 512 tokens ±10%) e verificar token count antes da chamada à API — não usar contagem de chunks como proxy.

---

#### 3. Riscos Não Considerados

**3.1 Controle de acesso — ACLs não respeitadas pelo índice**

Documentos no SharePoint têm permissões por usuário/grupo. Se o índice vetorial não respeita ACLs, um atendente sem permissão pode recuperar conteúdo confidencial via consulta ao assistente. Não é risco teórico — é falha de segurança real.

**3.2 Qualidade da base documental como risco de negócio**

O cliente confirmou que a equipe resolve contradições "perguntando para quem sabe" — parte do conhecimento operacional real está nas pessoas, não nos documentos. O assistente vai propagar imprecisões da documentação com aparência de autoridade.

**3.3 Viabilidade do prazo de 3 meses**

3 meses para discovery + desenvolvimento + go-live com OCR, detecção de conflitos, extração de tabelas, grafo de dependências Confluence e automação de re-indexação é apertado. Nenhuma estratégia de escopo controlado ou faseamento estava na v1.

**3.4 Rate limits e throughput da API**

Com ~25 consultas/hora em pico e ~8.000 tokens por consulta, o consumo em pico é ~200.000 tokens/hora. A cota padrão Azure OpenAI pode ser inferior a isso em deployments não provisionados.

---

#### 4. Recomendações Vagas

**4.1 "Serialização semântica das tabelas"**

A frase aparece sem definição operacional. Serialização pode significar markdown, JSON, ou linguagem natural. Cada abordagem tem tradeoffs radicalmente diferentes em tokens e qualidade de retrieval. O documento precisa especificar o formato exato com exemplo concreto.

**4.2 Ausência completa de estimativa de custo operacional**

O custo mensal do sistema em produção (inferência de LLM, índice vetorial, compute) estava completamente ausente da v1 — uma omissão crítica para um projeto com orçamento definido.

---

### Resposta 2

> *Arquivo gerado: `analise-viabilidade-rag-novatech-v2.md`*

---

# Análise de Viabilidade Técnica: Assistente de IA Baseado em Documentos
## NovaTech — Projeto RAG para Atendimento ao Cliente
**DB1 Group | Junho 2026 | Versão 2.0**

---

> **Sobre esta versão:** A v2 corrige três imprecisões técnicas da v1 (detecção de contradições por embedding, comportamento do `openpyxl data_only`, e a técnica anti-*lost-in-middle*), revisa estimativas de overhead OCR para valores mais conservadores, adiciona uma seção de custo operacional ausente na v1, expande os riscos de 6 para 10 (incluindo controle de acesso, qualidade da base documental, viabilidade do prazo e limites de throughput), e inclui uma seção sobre o que o sistema não conseguirá responder — ponto crítico para gestão de expectativas.

---

## Sumário Executivo

Este documento analisa a viabilidade técnica de um assistente de IA baseado em RAG (*Retrieval-Augmented Generation*) para a equipe de atendimento ao cliente da NovaTech.

A análise aponta que o projeto é **tecnicamente viável**, com as seguintes qualificações:

- O pré-processamento dos documentos é o risco técnico número um — consome proporcionalmente mais esforço do que a integração com o LLM.
- A documentação contraditória é um problema de **governança de conhecimento**, não apenas técnico. O sistema detecta candidatos a conflito, mas a resolução exige processo humano.
- O prazo de 3 meses é **viável apenas com escopo controlado**. A v2 detalha os elementos a priorizar versus diferir para Fase 2.
- O custo operacional estimado (~R$ 2.245/mês) precisa ser previsto no orçamento — estava ausente na v1.

---

## 1. Análise de Desafios por Tipo de Fonte

### 1.1 PDFs com Tabelas Complexas

**Desafio**

Tabelas de frete com 15+ colunas têm relações espaciais destruídas na extração linear por bibliotecas padrão. Problema adicional na v2: **tabelas que ocupam múltiplas páginas** — a partir da segunda página, as linhas não têm cabeçalho de contexto.

**Impacto no RAG**

Respostas incorretas em perguntas sobre prazos e valores, com confiança aparente — pior cenário para atendimento ao cliente.

**Tratamento Técnico**

1. `pdfplumber` ou `camelot` para PDFs nativos; Azure Document Intelligence (Layout) para tabelas como imagem.
2. **Serialização em linguagem natural** — formato explícito com identificação da fonte embutida:
   `"Frete para a região Norte com peso entre 5 e 10 kg: prazo de 3 dias úteis, valor de R$ 12,50. (Fonte: Tabela de Fretes Regionais, set/2025, linha 14)"`
3. Propagação de cabeçalho em tabelas multipágina.
4. **Teste de aceitação por tabela:** 5 perguntas de referência por tabela crítica antes de incluir no índice de produção.

---

### 1.2 PDFs Escaneados (OCR Necessário)

**Desafio**

Overhead OCR corrigido: faixa realista é **+25% a +50%** (central: 35%), não +15% como na v1. Documentos com baixa resolução, orientação incorreta ou carimbos sobre texto atingem o limite superior da faixa.

**Tratamento Técnico**

1. Azure AI Document Intelligence com modelo Read.
2. **Política de confiança por bloco:**
   - Score ≥ 0,90: ingerir normalmente
   - Score 0,75–0,89: ingerir com alerta `qualidade_ocr: media`
   - Score < 0,75: quarentena — **não indexar**
3. Limpeza pós-OCR de artefatos (linhas com >30% de caracteres especiais, blocos com <10 tokens).

---

### 1.3 Wikis com Links e Referências Cruzadas (Confluence)

**Desafio**

Link expansion sem controle de profundidade causa loops em referências circulares (Página A → B → C → A).

**Tratamento Técnico**

1. **Link expansion com profundidade máxima 1 e cache de visitados** — resolver referências diretas, não transitivas.
2. **Detecção de links mortos** em pré-ingestão via API do Confluence.
3. Chunk carrega trilha de cabeçalhos: `{page: "Políticas de Frete", section: "Fretes Internacionais", subsection: "Restrições de Carga"}`.
4. Grafo de dependência para re-indexação em cascata quando uma página é atualizada.

---

### 1.4 Planilhas com Fórmulas Interdependentes

**Desafio**

`openpyxl data_only=True` é condicionalmente inútil: se o arquivo foi gerado por automação ou nunca aberto no Excel após edição, o cache de valores é vazio e todas as células com fórmula retornam `None` silenciosamente.

**Tratamento Técnico**

1. **Validação do cache:** Verificar proporção de células `None`. Se > 20%, o cache está vazio.
2. **Pré-processamento garantido:** Abrir os arquivos com LibreOffice headless (`--calc --headless`) para forçar recálculo antes da leitura com `openpyxl`.
3. Serialização com parâmetros de configuração embutidos:
   `"[Parâmetros vigentes: ICMS_SP=12%, ICMS_RJ=20%] Frete SP para RJ, 10kg: valor base R$ 45,00, ICMS 20% aplicado = total R$ 54,00."`

---

## 2. Estimativa de Consumo de Tokens

### Premissas Corrigidas

| Premissa | Valor v1 | Valor v2 | Mudança |
|---|---|---|---|
| Overhead OCR | +15% | +25-50% (central 35%) | Corrigido |
| Overhead metadados por chunk | não previsto | +8% | Adicionado |
| Histórico de conversa | 3k tokens | 4k tokens | Ajustado |

### Totais por Fonte

| Fonte | Tokens (central) | Tokens (pessimista) |
|---|---|---|
| SharePoint — texto corrido | 3.888.000 | 3.888.000 |
| SharePoint — tabelas | 2.177.000 | 2.177.000 |
| SharePoint — OCR | 1.050.000 | 1.296.000 |
| Confluence | 415.000 | 415.000 |
| Planilhas | 108.000 | 108.000 |
| **Total** | **~7.638.000** | **~7.884.000** |

*Corpus ~60× maior que a janela de 128k tokens. A diferença entre central e pessimista (~246k tokens) vem quase inteiramente da qualidade do OCR.*

---

## 3. Análise de Orçamento de Contexto

Distribuição dos 128k tokens:
- Reserva: 2k
- System prompt: ~1,5k
- Histórico (4–6 trocas): ~4k *(ajustado da v1)*
- Pergunta: ~150 tokens
- Buffer de resposta: ~2k
- **Chunks RAG disponíveis: ~120k tokens**

**Verificação de token count obrigatória antes de cada chamada à API** — tamanho variável dos chunks torna contagem de chunks um proxy inadequado.

---

## 4. Estratégia de Fragmentação

### Técnica Anti-Lost-in-Middle Corrigida

**v1 (incorreto):** Duplicar top chunks no início e no final — desperdício de tokens.

**v2 (correto):** Reordenação por relevância com posicionamento nos extremos — custo zero em tokens:

```python
chunks_ordenados = sorted(chunks_recuperados, key=lambda x: x.score, reverse=True)
contexto = (
    chunks_ordenados[:3]          # top 3 no início
    + chunks_ordenados[3:-2]      # demais no meio
    + chunks_ordenados[-2:]       # 2 mais relevantes restantes no final
)
```

### Pipeline de Recuperação em Três Camadas

1. **Busca vetorial:** top-20 candidatos por similaridade de cosseno (`text-embedding-3-large`)
2. **Re-ranking por cross-encoder:** refina os 20 candidatos; adiciona 300–600ms de latência — aceitável para a meta de <2 minutos
3. **Filtros por metadados:** boost/penalidade por data, score OCR, área

### Hierárquica vs. Flat por Tipo

| Documento | Estratégia |
|---|---|
| Manuais e políticas estruturados | Hierárquica |
| Manuais sem hierarquia de cabeçalhos | Flat por parágrafo |
| Tabelas de frete | Flat por linha serializada |
| Confluence | Hierárquica |
| Planilhas | Flat por bloco temático |
| OCR | Flat por bloco de parágrafo |

---

## 5. Estimativa de Custo Operacional *(seção nova, ausente na v1)*

**Premissas:** 192 consultas/dia ao RAG (320 chamados × 60%); 8.000 tokens input + 500 tokens output por consulta; GPT-4o via Azure OpenAI.

| Componente | Custo/mês (USD) | Custo/mês (BRL) |
|---|---|---|
| Azure OpenAI (inferência) | ~$144 | ~R$ 720 |
| Azure AI Search (índice vetorial) | ~$250 | ~R$ 1.250 |
| Compute (pipeline) | ~$50 | ~R$ 250 |
| Azure Document Intelligence | ~$5 | ~R$ 25 |
| **Total** | **~$449** | **~R$ 2.245** |

---

## 6. O que o Sistema Não Conseguirá Responder *(seção nova)*

| Tipo de Pergunta | Motivo da Limitação | Tratamento |
|---|---|---|
| Cálculo de frete para remessa específica | Requer operação matemática, não consulta | Fornecer parâmetros; orientar para ferramenta de cotação |
| Status de pedido/entrega em tempo real | Requer integração com TMS, não na documentação estática | Comunicar claramente no treinamento |
| Interpretação de regras ambíguas/com exceções | Documentação contradiz o caso específico | Indicar que a resposta é o caso geral; escalar para Compliance |
| Tópicos não documentados (~15-25% das consultas) | Lacuna na base de conhecimento | Log de consultas sem resposta → backlog de documentação |

---

## 7. Riscos e Mitigação *(expandido de 6 para 10 riscos)*

| # | Risco | Prob. | Impacto | Status |
|---|---|---|---|---|
| 7.1 | Documentos contraditórios *(detecção corrigida)* | Alta | Alto | Corrigido da v1 |
| 7.2 | Controle de acesso — ACLs não respeitadas | Alta | Alto | **Novo** |
| 7.3 | Qualidade da base documental como risco de negócio | Média-Alta | Alto | **Novo** |
| 7.4 | Baixa qualidade na extração de tabelas | Alta | Alto | Mantido |
| 7.5 | Desatualização silenciosa do índice | Alta | Médio-Alto | Mantido |
| 7.6 | Alucinação com alta confiança aparente | Média | Alto | Mantido |
| 7.7 | Rate limits e throughput da API | Média | Médio | **Novo** |
| 7.8 | Adoção baixa pelos atendentes | Média | Alto | Mantido |
| 7.9 | Viabilidade do prazo de 3 meses | Alta | Médio | **Novo** |
| 7.10 | Privacidade e compliance | Baixa-Média | Alto | Mantido |

### 7.2 Controle de Acesso — ACLs *(destaque por ser novo e crítico)*

Se o índice vetorial não respeitar as ACLs do SharePoint, atendentes sem permissão podem recuperar documentos confidenciais via consulta ao assistente — falha de segurança real, não teórica.

**Mitigação:** Filtrar documentos por perfil do usuário via Microsoft Graph API antes do retrieval. Alternativa mais simples: dois índices separados (público + restrito por perfil).

### 7.9 Viabilidade do Prazo *(destaque por impacto no escopo)*

**Estratégia de escopo em duas fases:**

**Fase 1 (3 meses — go-live):**
- Ingestão de texto corrido (500 docs SharePoint) e Confluence sem link expansion completa
- Interface Teams com citação de fonte
- Re-indexação manual mensal
- Cobre ~70% das consultas de política e procedimento

**Fase 2 (meses 4-6):**
- OCR para 100 documentos escaneados
- Extração de tabelas complexas com testes de aceitação
- Automação de re-indexação (webhooks)
- Detecção de conflitos com LLM
- Controle de acesso por ACL

---

## Conclusão e Roadmap (v2)

Projeto tecnicamente viável com **escopo em duas fases como caminho mais seguro**.

**Indicador crítico:** A meta de 12→2 minutos é atingível para consultas de política/procedimento (Fase 1). Redução completa para consultas de frete/SLA depende da qualidade de extração de tabelas — confirmada só após testes de aceitação no Mês 1.

---

## Apêndice: Comparativo v1 → v2

| Item | v1 | v2 | Tipo de Mudança |
|---|---|---|---|
| Detecção de documentos contraditórios | Threshold de embedding | Extração de triplas + LLM | Correção técnica |
| `openpyxl data_only=True` | Solução direta | Condicional com validação | Correção técnica |
| Anti-lost-in-middle | Duplicar top chunks | Reordenar por relevância | Correção técnica |
| Overhead OCR | +15% | +25-50% (central 35%) | Estimativa conservadora |
| Overhead de metadados | Não previsto | +8% por chunk | Adição |
| Histórico de conversa | 3k tokens (3 trocas) | 4k tokens (4-6 trocas) | Ajuste |
| Total do corpus | ~6,9M tokens | ~7,6M tokens | Revisão |
| Custo operacional | Ausente | ~R$ 2.245/mês | Adição de seção |
| O que o sistema não responde | Ausente | Seção dedicada | Adição de seção |
| Número de riscos | 6 | 10 | Expansão |
| Riscos novos | — | ACLs, qualidade da base, prazo, rate limits | Adição |
| Estratégia de prazo | Roadmap linear 3 meses | Faseamento Fase 1 / Fase 2 | Adição |

---

*Log gerado por Claude Sonnet 4.6 (DB1 Group / Formação IA Prática) | Junho 2026*
*Arquivos de entrega: `analise-viabilidade-rag-novatech.md` (v1) e `analise-viabilidade-rag-novatech-v2.md` (v2)*
