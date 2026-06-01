# Análise de Viabilidade Técnica: Assistente de IA Baseado em Documentos

## NovaTech — Projeto RAG para Atendimento ao Cliente

**DB1 Group | Junho 2026**

---

## Sumário Executivo

Este documento analisa a viabilidade técnica de um assistente de IA baseado em RAG (_Retrieval-Augmented Generation_) para a equipe de atendimento ao cliente da NovaTech. O sistema proposto responde perguntas em linguagem natural consultando a documentação interna da empresa e indicando a fonte de cada resposta.

> **O que é RAG?** É uma arquitetura que combina dois passos: primeiro _recupera_ fragmentos relevantes da base documental (busca semântica), depois _gera_ uma resposta usando um LLM (modelo de linguagem), passando esses fragmentos como contexto. A resposta é fundamentada na documentação, não inventada pelo modelo.

A análise aponta que o projeto é **tecnicamente viável**, mas exige atenção especial ao pré-processamento dos documentos — especialmente PDFs com tabelas, documentos escaneados e planilhas — e a uma estratégia disciplinada de gerenciamento do contexto enviado ao modelo. Sem esse cuidado, o sistema responderá com confiança, porém de forma imprecisa.

---

## 1. Análise de Desafios por Tipo de Fonte

### 1.1 PDFs com Tabelas Complexas

**Desafio**

Tabelas de frete com 15 ou mais colunas não são simples texto corrido. Quando uma biblioteca padrão de extração de PDF processa um arquivo assim, o resultado é uma sequência de texto linear onde as relações entre células se perdem. Por exemplo, uma tabela que relaciona _Região de Destino × Peso × Prazo × Valor_ pode ser extraída como:

```
Norte Nordeste Sul Sudeste Centro-Oeste 0-5kg 5-10kg ...
3 dias 4 dias 2 dias ...
R$ 12,50 R$ 18,00 R$ 9,80 ...
```

O modelo de linguagem não consegue inferir com confiança que "R$ 9,80" corresponde a "Sul + 5-10kg + 2 dias" — a relação espacial original foi destruída.

**Impacto no RAG**

Perguntas do tipo _"Qual o prazo de entrega para o Nordeste com carga de 8kg?"_ podem gerar respostas incorretas mesmo que o dado correto esteja no documento. O modelo pode cruzar valores da linha errada da tabela e responder com confiança aparente — o pior cenário possível para um sistema de atendimento.

**Tratamento Técnico**

1. **Extração estruturada com bibliotecas especializadas:** Usar `pdfplumber` ou `camelot` (para PDFs nativos) para extrair tabelas como estruturas de dados (DataFrames), não como texto puro.
2. **Serialização semântica das tabelas:** Converter cada linha da tabela em uma sentença autocontida antes de fragmentar. Exemplo:
   - _Antes:_ `Norte | 5-10kg | 3 dias | R$ 12,50`
   - _Depois (chunk gerado):_ `"Frete para a região Norte com peso entre 5 e 10 kg: prazo de 3 dias úteis, valor de R$ 12,50."`
3. **Chunking por linha/grupo de linhas:** Cada linha ou grupo de linhas da tabela torna-se um fragmento independente, com o cabeçalho da tabela repetido em cada fragmento como contexto.
4. **Fallback para tabelas embutidas como imagem:** Documentos com tabelas renderizadas como imagem (fluxogramas) requerem modelos multimodais (Azure Document Intelligence com layout analysis) para extração.

---

### 1.2 PDFs Escaneados (OCR Necessário)

**Desafio**

Documentos escaneados são imagens — não há texto extraível diretamente. A aplicação de OCR (_Optical Character Recognition_) recupera o texto, mas introduz ruído proporcional à qualidade da digitalização: letras confundidas (`l` com `1`, `O` com `0`), palavras cortadas, hifenizações incorretas, parágrafos misturados. Um documento com OCR de qualidade média apresenta tipicamente 5–15% de erros por caracter — suficiente para corromper datas, valores monetários e siglas críticas.

**Impacto no RAG**

- O índice vetorial (a base que permite a busca semântica) é construído sobre texto ruidoso, reduzindo a chance de recuperar o fragmento certo para uma pergunta.
- Valores críticos como prazos (`30 dias` vira `3O dias`) ou percentuais (`2,5%` vira `25%`) podem ser transmitidos incorretamente ao modelo sem nenhum alerta.
- Tokens desnecessários gerados por erros de OCR consomem espaço no contexto sem contribuir com informação.

**Tratamento Técnico**

1. **Pipeline OCR de alta qualidade:** Usar **Azure AI Document Intelligence** (disponível nas licenças Azure AI Services já previstas) em vez de tesseract genérico. O serviço foi treinado especificamente para documentos empresariais e apresenta acurácia significativamente superior.
2. **Score de confiança por bloco:** O Azure Document Intelligence retorna um score de confiança por parágrafo. Blocos com score abaixo de 0,80 devem ser sinalizados para revisão humana antes de entrar no índice.
3. **Pós-processamento linguístico:** Aplicar um corretor contextual (por exemplo, usando um LLM pequeno em modo de revisão) para detectar anomalias numéricas e siglas corrompidas nos blocos extraídos.
4. **Metadado de origem:** Todo chunk gerado de documento OCR deve carregar o metadado `fonte: ocr` e `score_ocr: 0.XX` para que o sistema possa alertar o atendente: _"Esta resposta vem de um documento digitalizado — verifique a fonte original em caso de dúvida."_

---

### 1.3 Wikis com Links e Referências Cruzadas (Confluence)

**Desafio**

Páginas de wiki raramente são autocontidas. Uma página sobre _Política de Devolução_ pode dizer "conforme as regras da Seção 3 da Política de Frete" e ter um link para outra página. Quando essa página é fragmentada e indexada isoladamente, o fragmento extraído contém uma referência que não pode ser resolvida — o contexto necessário para compreender o conteúdo não está no chunk.

Além disso, macros customizadas do Confluence (painéis de status, listas geradas dinamicamente, abas de conteúdo) geram HTML ou marcações proprietárias que, quando exportadas, produzem texto estruturalmente incoerente.

**Impacto no RAG**

- Respostas incompletas: o modelo recebe a referência mas não o conteúdo referenciado.
- Fragmentos que fazem sentido apenas dentro de um contexto maior são recuperados isoladamente e geram respostas parciais ou ambíguas.
- Macros exportadas como `{panel:title=Atenção}...{panel}` poluem o texto com marcações que não têm significado semântico.

**Tratamento Técnico**

1. **Resolução de links em tempo de ingestão:** Antes de fragmentar, percorrer a árvore de links de cada página e embutir um resumo da página referenciada no chunk que a menciona (técnica de _link expansion_). Isso aumenta o tamanho do chunk, mas garante autocontido.
2. **Fragmentação por seção lógica, não por tamanho fixo:** Respeitar a hierarquia de cabeçalhos (`H1 > H2 > H3`) do Confluence para definir os limites dos fragmentos, em vez de cortar no número de tokens.
3. **Limpeza de macros via pré-processamento:** Mapear as macros mais usadas no Confluence da NovaTech e criar conversores: `{panel:title=X}` → `**X:**`, `{code}` → bloco de código, macros de tabela → serialização estruturada.
4. **Grafo de dependência entre páginas:** Manter um grafo que registra quais páginas referenciam quais. Quando uma página é atualizada, re-indexar automaticamente todas as páginas que a referenciam — evita que links apontem para conteúdo desatualizado no índice.

---

### 1.4 Planilhas com Fórmulas Interdependentes

**Desafio**

Planilhas de referência frequentemente apresentam duas categorias de problema. Primeiro, **células com fórmulas** que calculam valores derivados (`=B2*C2*1.12`): ao exportar para texto, a ferramenta exporta ou a fórmula (ininteligível para o modelo) ou o valor calculado no momento da exportação (que pode estar desatualizado). Segundo, **estrutura tabular com dependências implícitas**: uma célula pode depender de contexto em linhas distantes na planilha — por exemplo, a taxa de ICMS aplicável está na aba "Configurações", e a tabela de fretes na aba "Fretes" a referencia silenciosamente.

**Impacto no RAG**

- O modelo pode receber um valor calculado que era correto no mês passado, mas a regra de cálculo mudou.
- Fórmulas exportadas como texto (`=PROCV(A2,Tabela_Regras,3,0)`) são incompreensíveis para o modelo e consomem tokens sem valor.
- Dados de abas diferentes que são interdependentes são fragmentados separadamente e podem produzir respostas inconsistentes entre si.

**Tratamento Técnico**

1. **Avaliação de fórmulas em tempo de ingestão:** Abrir as planilhas com `openpyxl` (Python) com `data_only=True` para capturar os valores calculados, não as fórmulas. Registrar a data de ingestão nos metadados.
2. **Serialização por contexto:** Cada linha de dados deve ser acompanhada dos cabeçalhos e, quando relevante, dos parâmetros de configuração das abas auxiliares. Exemplo:
   - _Configuração (Aba Parâmetros):_ `ICMS_SP = 12%, ICMS_RJ = 20%`
   - _Linha serializada:_ `"Frete SP para RJ, carga geral 10kg: valor base R$ 45,00, ICMS aplicado (20%) = R$ 54,00 total."`
3. **Atualização mensal automatizada:** Como as planilhas são atualizadas mensalmente, criar um gatilho (Azure Logic Apps ou Power Automate — já disponível no M365 E3) que detecta modificações na pasta de rede e re-indexa as planilhas afetadas automaticamente dentro de 24 horas.
4. **Alerta de dados potencialmente desatualizados:** Incluir nos metadados do chunk a `data_ingestao`. O sistema deve alertar o atendente quando um chunk for de uma ingestão com mais de 35 dias.

---

## 2. Estimativa de Consumo de Tokens

### Premissas do Cálculo

Antes dos números, as premissas adotadas — todas verificáveis e ajustáveis conforme levantamento real:

| Premissa                                | Valor Adotado              | Justificativa                                                                                       |
| --------------------------------------- | -------------------------- | --------------------------------------------------------------------------------------------------- |
| Conversão palavras → tokens             | `tokens = palavras ÷ 0,75` | Padrão para texto em português (línguas latinas são ligeiramente menos densas em tokens que inglês) |
| Páginas por documento PDF (média)       | 12 páginas                 | Estimativa conservadora para manuais e políticas operacionais                                       |
| Palavras por página PDF (texto corrido) | 450 palavras               | Páginas com margens, rodapés e formatação típica de documentos corporativos                         |
| Overhead de tabela (serialização)       | +40% sobre texto base      | Serializar tabelas gera mais tokens que o texto equivalente                                         |
| Overhead de OCR (ruído + repetições)    | +15% sobre texto base      | Erros de OCR introduzem tokens espúrios; texto repetido por baixa segmentação                       |
| Palavras por página Confluence          | 600 palavras               | Wikis tendem a ser mais densas; inclui metadados de links expandidos (+20%)                         |
| Tamanho médio de planilha serializada   | 2.500 palavras por arquivo | Tabela de frete 100 linhas × 15 colunas, serializada em sentenças                                   |

---

### 2.1 SharePoint — PDFs e Documentos Word (800 documentos)

**Categorização estimada do acervo:**

| Categoria                                     | Qtd. Estimada | Características                      |
| --------------------------------------------- | ------------- | ------------------------------------ |
| Documentos texto corrido (manuais, políticas) | 500 docs      | Texto simples, sem tabelas complexas |
| Documentos com tabelas (fretes, SLAs)         | 200 docs      | Texto + tabelas serializadas         |
| Documentos escaneados (OCR)                   | 100 docs      | Texto extraído via OCR com ruído     |

**Cálculo:**

**Grupo A — Texto corrido (500 documentos):**

```
500 docs × 12 páginas × 450 palavras = 2.700.000 palavras
Tokens = 2.700.000 ÷ 0,75 = 3.600.000 tokens
```

**Grupo B — Documentos com tabelas (200 documentos):**

```
200 docs × 12 páginas × 450 palavras = 1.080.000 palavras (base)
+ 40% overhead de serialização = 1.080.000 × 1,40 = 1.512.000 palavras
Tokens = 1.512.000 ÷ 0,75 = 2.016.000 tokens
```

**Grupo C — Documentos escaneados OCR (100 documentos):**

```
100 docs × 12 páginas × 450 palavras = 540.000 palavras (base)
+ 15% overhead de OCR = 540.000 × 1,15 = 621.000 palavras
Tokens = 621.000 ÷ 0,75 = 828.000 tokens
```

**Subtotal SharePoint: ~6.444.000 tokens**

---

### 2.2 Confluence — Wiki Interna (400 páginas)

```
400 páginas × 600 palavras = 240.000 palavras (base)
+ 20% overhead de expansão de links = 240.000 × 1,20 = 288.000 palavras
Tokens = 288.000 ÷ 0,75 = 384.000 tokens
```

**Subtotal Confluence: ~384.000 tokens**

---

### 2.3 Pasta de Rede — Planilhas de Referência

**Estimativa: 30 planilhas (atualizadas mensalmente)**

```
30 planilhas × 2.500 palavras = 75.000 palavras
Tokens = 75.000 ÷ 0,75 = 100.000 tokens
```

**Subtotal Planilhas: ~100.000 tokens**

---

### Resumo do Corpus Total

| Fonte                               | Tokens Estimados      | % do Total |
| ----------------------------------- | --------------------- | ---------- |
| SharePoint — texto corrido          | 3.600.000             | 55,0%      |
| SharePoint — documentos com tabelas | 2.016.000             | 30,8%      |
| SharePoint — documentos OCR         | 828.000               | 12,6%      |
| Confluence                          | 384.000               | 5,9%       |
| Planilhas                           | 100.000               | 1,5%       |
| **Total do Corpus**                 | **~6.928.000 tokens** | 100%       |

> **Conclusão:** O corpus completo é ~55× maior que a janela de contexto de 128k tokens. Isso confirma que **não é possível — nem desejável — passar todos os documentos ao modelo a cada consulta**. O valor do RAG está exatamente em recuperar apenas os ~2–5% de conteúdo relevante para cada pergunta específica.

---

## 3. Análise de Orçamento de Contexto

### 3.1 Mapa do Contexto Disponível

A cada requisição ao modelo, os 128.000 tokens disponíveis precisam ser distribuídos entre diferentes componentes que competem pelo mesmo espaço:

```
┌─────────────────────────────────────────────────────┐
│            JANELA DE CONTEXTO: 128.000 tokens       │
├─────────────────────────────────────────────────────┤
│  Reserva de segurança (output mínimo garantido)     │
│  2.000 tokens                                       │
├─────────────────────────────────────────────────────┤
│  TOKENS EFETIVOS PARA RAG: 126.000 tokens           │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ System Prompt (instruções do assistente)     │  │
│  │ ~1.500 tokens                               │  │
│  ├──────────────────────────────────────────────┤  │
│  │ Histórico de conversa (últimas 3 trocas)    │  │
│  │ ~3.000 tokens                               │  │
│  ├──────────────────────────────────────────────┤  │
│  │ Pergunta atual do atendente                 │  │
│  │ ~150 tokens                                 │  │
│  ├──────────────────────────────────────────────┤  │
│  │ CHUNKS RECUPERADOS (RAG)                    │  │
│  │ ~121.350 tokens disponíveis                 │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 3.2 Distribuição dos Chunks Recuperados

Com ~121.000 tokens disponíveis para chunks e chunk sizes recomendados de 400–600 tokens, é matematicamente possível inserir até **200–300 chunks** por requisição. Porém, **isso seria um erro** — quanto mais chunks no contexto, maior o risco do fenômeno "lost in the middle" (detalhado na seção 4).

**Distribuição prática recomendada por tipo de consulta:**

| Tipo de Pergunta                                   | Chunks Recomendados | Tokens Médios      | Raciocínio                                      |
| -------------------------------------------------- | ------------------- | ------------------ | ----------------------------------------------- |
| Pergunta simples de política                       | 3–5 chunks          | 1.500–2.500 tokens | Regra direta, sem dependências                  |
| Cálculo de frete (tabela)                          | 5–8 chunks          | 2.500–4.000 tokens | Múltiplas variáveis da tabela + regra aplicável |
| Fluxo de processo (ex: reclamação)                 | 8–12 chunks         | 4.000–6.000 tokens | Múltiplas etapas interdependentes               |
| Consulta comparativa (ex: SLA por tipo de cliente) | 10–15 chunks        | 5.000–7.500 tokens | Dados de múltiplos segmentos para comparação    |

**Tamanho máximo recomendado por requisição: 15 chunks (~7.500 tokens de chunks)**

Isso representa apenas 6% dos tokens disponíveis, mas é o ponto de equilíbrio entre cobertura e precisão. Os tokens restantes são reservados para:

- Respostas mais longas em casos complexos
- Crescimento natural do histórico de conversa ao longo do atendimento
- Espaço de manobra para perguntas de seguimento no mesmo chamado

### 3.3 Quando o Orçamento se Torna Insuficiente

**Cenário crítico 1 — Consulta com múltiplas tabelas:**
Um atendente pergunta sobre uma remessa que envolve diferentes produtos com regras de frete distintas, passando por dois CDs diferentes. A resposta precisa de dados de 3 tabelas de frete + 2 políticas de SLA + 1 regra de compliance. Com chunks de 500 tokens, isso demanda ~30 chunks = 15.000 tokens de RAG. Ainda dentro do orçamento, mas o risco de "lost in the middle" aumenta significativamente.

_Compromisso necessário:_ Implementar sumarização em cascata — resumir os chunks de cada tabela antes de inseri-los no contexto final.

**Cenário crítico 2 — Histórico longo de conversa:**
Se um atendimento durar 10 ou mais trocas de mensagens, o histórico acumulado pode chegar a 10.000–15.000 tokens. Isso comprime o espaço disponível para chunks.

_Compromisso necessário:_ Implementar janela deslizante de histórico (manter apenas as últimas 4–6 trocas) combinado com um resumo comprimido das trocas anteriores (~500 tokens).

**Cenário crítico 3 — Chunks de OCR com ruído:**
Chunks gerados de documentos OCR de baixa qualidade são 15% maiores que o equivalente em texto limpo, e carregam informação de menor qualidade por token. Com 15 chunks OCR, o consumo real pode ser de ~8.600 tokens para a mesma cobertura que 7.500 tokens limpos ofereceriam.

_Compromisso necessário:_ Reduzir o número de chunks OCR aceitos por requisição (máximo 5) e priorizar documentos com score de confiança OCR > 0,85.

---

## 4. Estratégia de Fragmentação

### 4.1 O Problema da Informação Perdida no Meio

Estudos com modelos de linguagem demonstram um padrão consistente: quando o contexto contém muitas informações, o modelo tende a priorizar o que está **no início** e **no final** da janela de contexto, "esquecendo" parcialmente o que está no meio. Esse fenômeno é chamado de _lost in the middle_.

Para o assistente da NovaTech, isso significa que, se recuperarmos 15 chunks e posicioná-los aleatoriamente no contexto, a resposta será mais influenciada pelos chunks nas primeiras e últimas posições — mesmo que o chunk mais relevante esteja no meio.

```
CONTEXTO ENVIADO AO MODELO:
[System Prompt] → [Chunk 1] → [Chunk 2] → ... [Chunk 7] → ... [Chunk 14] → [Chunk 15] → [Pergunta]
                   ↑ Alta atenção                ↑ Baixa atenção              ↑ Alta atenção
```

### 4.2 Tamanho Ótimo de Fragmentos por Tipo de Documento

| Tipo de Documento                   | Tamanho Recomendado                | Lógica do Corte                                                               |
| ----------------------------------- | ---------------------------------- | ----------------------------------------------------------------------------- |
| Políticas e manuais (texto corrido) | 400–500 tokens (~300–375 palavras) | Por parágrafo ou subseção lógica (`H3`)                                       |
| Tabelas de frete serializadas       | 200–300 tokens por grupo de linhas | 5–10 linhas relacionadas por chunk (ex: mesmo peso, todas as regiões)         |
| Documentos OCR                      | 300–400 tokens                     | Menor para limitar o impacto do ruído; corte por bloco de parágrafo detectado |
| Páginas Confluence                  | 450–600 tokens                     | Por seção lógica, incluindo título do pai para contexto                       |
| Planilhas serializadas              | 200–250 tokens por bloco temático  | Por conjunto de configuração (ex: todas as regras do mesmo tipo de carga)     |

**Sobreposição (overlap) entre chunks:** Recomenda-se uma sobreposição de 50–80 tokens entre chunks consecutivos. Isso garante que sentenças que cruzam os limites de corte não sejam cortadas ao meio, preservando o sentido.

### 4.3 Ordem de Ingestão no Contexto (Posicionamento Anti-Lost-in-Middle)

Ao montar o contexto final para envio ao modelo, seguir esta ordem:

```
1. [System Prompt]
2. [Chunks de alta relevância — Top 3 por score de similaridade]  ← posição privilegiada: início
3. [Chunks de média relevância — posições 4 a N-3]
4. [Chunks de alta relevância — repetir Top 2]  ← posição privilegiada: final
5. [Histórico de conversa resumido]
6. [Pergunta atual do atendente]
```

> **Por que repetir os top chunks?** Colocar os fragmentos mais relevantes tanto no início quanto no final do bloco de contexto reduz o risco de serem "esquecidos" pelo modelo. O custo em tokens é baixo (2 chunks extras ≈ 800–1.000 tokens), e o ganho em consistência da resposta é substancial.

### 4.4 Técnicas de Priorização

**Priorização em três camadas:**

**Camada 1 — Relevância semântica (obrigatória):**
Calcular a similaridade de cosseno entre o embedding da pergunta e o embedding de cada chunk. Usar um modelo de embedding treinado para português — recomendado: `text-embedding-3-large` da Azure OpenAI.

**Camada 2 — Re-ranking por modelo especializado (recomendado):**
Usar um modelo de re-ranking (por exemplo, Cohere Rerank ou um cross-encoder local) para refinar a ordem dos top-20 chunks retornados na busca semântica. Re-rankers avaliam a relevância do par (pergunta, chunk) diretamente, não apenas por similaridade vetorial — capturando nuances que busca vetorial pura perde.

**Camada 3 — Boost por metadados (contextual):**
Aplicar multiplicadores de score baseados em contexto:

| Condição                                                 | Multiplicador                  |
| -------------------------------------------------------- | ------------------------------ |
| Documento atualizado nos últimos 30 dias                 | +20%                           |
| Score de confiança OCR > 0,90                            | +10%                           |
| Score de confiança OCR < 0,75                            | -30%                           |
| Documento marcado como "versão em conflito"              | -50% (com alerta ao atendente) |
| Chunk da mesma área que gerou a pergunta (ex: Comercial) | +15%                           |

### 4.5 Fragmentação Hierárquica vs. Flat

**Fragmentação Flat** cria chunks de tamanho uniforme, independentemente da estrutura do documento. É simples de implementar, mas perde hierarquia e contexto estrutural.

**Fragmentação Hierárquica** preserva a relação pai-filho entre seções: um chunk de subseção carrega consigo o título da seção pai. Isso permite dois modos de recuperação:

- **Recuperação grossa:** buscar pela seção pai (resumo de alto nível)
- **Recuperação fina:** buscar dentro da seção pelo fragmento específico

**Recomendação para a NovaTech:**

| Tipo de Documento                  | Estratégia                      | Motivo                                                                                             |
| ---------------------------------- | ------------------------------- | -------------------------------------------------------------------------------------------------- |
| Manuais e políticas (estruturados) | **Hierárquica**                 | Documentos longos com hierarquia clara de cabeçalhos — recuperação em dois níveis melhora precisão |
| Tabelas de frete                   | **Flat por linha serializada**  | Cada linha é uma unidade atômica de informação; hierarquia não agrega valor                        |
| Confluence (wiki)                  | **Hierárquica**                 | Dependências entre páginas e seções são explícitas; preservar hierarquia reduz perda de contexto   |
| Planilhas                          | **Flat por bloco temático**     | Grupos de linhas relacionadas são a unidade natural de busca                                       |
| OCR (escaneados)                   | **Flat por bloco de parágrafo** | Estrutura original pode estar corrompida; usar blocos detectados pelo OCR como unidade             |

---

## 5. Riscos e Mitigação

### 5.1 Risco: Documentos Contraditórios

**Descrição:** A NovaTech já identificou que versões diferentes de documentos se contradizem. O sistema RAG, sem tratamento, recupera fragmentos de versões conflitantes e os entrega ao modelo — que pode gerar uma resposta sintetizando as duas versões, silenciosamente.

**Probabilidade:** Alta (problema confirmado pelo cliente)
**Impacto:** Alto (respostas erradas entregues a clientes, risco de compliance)

**Mitigação:**

- Implementar detecção de conflito na fase de ingestão: ao indexar um novo documento, comparar embeddings com documentos existentes da mesma categoria. Similaridade acima de 85% com conteúdo divergente aciona uma flag de conflito.
- Documentos em conflito ficam em quarentena e não são servidos pelo RAG até resolução humana.
- Criar um painel de gestão de conflitos: a equipe de Operações/Compliance/Comercial visualiza os pares conflitantes, resolve qual versão é oficial, e o outro documento é arquivado.
- Enquanto houver conflito não resolvido, o assistente responde: _"Existem versões divergentes deste procedimento. Consulte [contato responsável] para confirmação."_

---

### 5.2 Risco: Alucinação com Alta Confiança Aparente

**Descrição:** Modelos de linguagem podem gerar informações incorretas mas apresentadas com confiança — especialmente quando os chunks recuperados são insuficientes ou ambíguos. Para o atendente, uma resposta bem estruturada parece confiável independentemente de sua acurácia.

**Probabilidade:** Média
**Impacto:** Alto (informação incorreta transmitida ao cliente)

**Mitigação:**

- Instruir o modelo no system prompt a **sempre citar a fonte específica** (documento + seção) de cada afirmação, tornando verificável.
- Implementar respostas com score de confiança explícito: quando o score máximo de similaridade dos chunks recuperados for abaixo de 0,75, o assistente deve indicar: _"Não encontrei uma resposta específica para isso na documentação. Recomendo escalar para [área responsável]."_
- Incluir na interface um botão "Ver Fonte" que abre o trecho original do documento — inibe o uso irrefletido e cria o hábito de verificação.
- Fase de validação: durante os primeiros 30 dias de operação, amostrar 10% das consultas para revisão humana e medir taxa de respostas incorretas.

---

### 5.3 Risco: Desatualização Silenciosa do Índice

**Descrição:** A documentação é atualizada mensalmente por três áreas sem processo unificado. Se o pipeline de re-indexação falhar, o assistente continuará respondendo com base em informações desatualizadas — sem alertar ninguém.

**Probabilidade:** Alta (sem automação, a desatualização é certa)
**Impacto:** Médio-alto (informações de prazo, valor e política incorretas)

**Mitigação:**

- Integrar o pipeline de ingestão com **Microsoft Graph API** para monitorar modificações no SharePoint em tempo quase-real (webhook de alteração de arquivo).
- Para o Confluence: usar a API REST nativa para detectar páginas modificadas após a última ingestão.
- Para planilhas na pasta de rede: script PowerShell agendado (Task Scheduler) que compara hash MD5 dos arquivos diariamente e dispara re-indexação quando detecta mudança.
- Dashboard de saúde do índice com alerta automático se nenhuma atualização for detectada em 35 dias (indicador de falha no pipeline).
- Todo chunk indexado carrega a data de ingestão — o assistente alerta automaticamente quando serve conteúdo com mais de 40 dias.

---

### 5.4 Risco: Baixa Qualidade da Extração de Tabelas

**Descrição:** Tabelas de frete são o coração da operação de atendimento. Se a extração falhar — seja por OCR ruim, estrutura tabular incomum, ou tabelas renderizadas como imagem — as respostas sobre cálculo de frete serão imprecisas, prejudicando exatamente o tipo de consulta mais frequente.

**Probabilidade:** Alta (tabelas complexas são tecnicamente desafiadoras)
**Impacto:** Alto (erro no cálculo de frete tem impacto financeiro direto)

**Mitigação:**

- Criar um conjunto de testes de regressão: 50 perguntas-padrão sobre tabelas de frete com respostas esperadas. Executar após cada re-indexação.
- Se taxa de acerto cair abaixo de 90%, bloquear o deploy e acionar a equipe técnica.
- Para tabelas de alto valor (fretes, SLAs), implementar extração paralela com duas ferramentas diferentes e comparar resultados — divergência acima de 5% aciona revisão manual.
- Manter uma versão simplificada das tabelas mais críticas como texto estruturado mantido manualmente pela equipe de Operações (fallback confiável para as 20 tabelas mais consultadas).

---

### 5.5 Risco: Adoção Baixa pelos Atendentes

**Descrição:** Um sistema tecnicamente excelente pode ser subutilizado se os atendentes não confiarem nele ou se o fluxo de uso introduzir atrito. A meta de reduzir 12 para 2 minutos por chamado depende de adoção real, não apenas de disponibilidade técnica.

**Probabilidade:** Média
**Impacto:** Alto (o ROI do projeto depende diretamente da adoção)

**Mitigação:**

- Envolver 5–8 atendentes experientes como _champions_ durante o desenvolvimento — eles testam, sugerem melhorias e treinam os colegas.
- Integrar diretamente no Microsoft Teams (canal de atendimento) — zero fricção de abertura de nova ferramenta.
- Durante os primeiros 60 dias, colher feedback estruturado: "Esta resposta foi útil?" (thumbs up/down). Respostas negativas alimentam um backlog de melhoria da base de conhecimento.
- Gamificação leve: painel visível da equipe mostrando consultas resolvidas com o assistente vs. busca manual — sem pressão, mas com visibilidade.

---

### 5.6 Risco: Conflito com Restrições de Privacidade e Compliance

**Descrição:** Documentos de compliance e políticas internas podem conter informações sensíveis. Enviar fragmentos desses documentos para uma API de LLM (mesmo Azure OpenAI, que tem garantias contratuais) pode conflitar com políticas internas de dados da NovaTech ou com requisitos regulatórios do setor de logística.

**Probabilidade:** Baixa-Média
**Impacto:** Alto (risco jurídico e de reputação)

**Mitigação:**

- Realizar um mapeamento de dados sensíveis no corpus antes do início do desenvolvimento. Identificar documentos que contenham dados pessoais de clientes, valores contratuais confidenciais, ou informações regulatórias restritas.
- Para esses documentos, aplicar anonimização automática em pré-processamento (substituir CPFs, CNPJs, nomes de clientes por tokens genéricos) antes da indexação.
- Aproveitar que o Azure OpenAI (disponível via Azure AI Services já previsto) processa dados **dentro da infraestrutura Azure do tenant da NovaTech** — os dados não saem para treinamento de modelos. Documentar essa garantia contratual para a equipe jurídica.
- Criar uma categoria de documentos "apenas consulta humana" — esses nunca entram no índice RAG, mas o assistente sabe que existem e direciona o atendente ao lugar certo.

---

## Conclusão e Próximos Passos Recomendados

A análise confirma que o projeto é **tecnicamente viável dentro do prazo de 3 meses**, com as seguintes condições:

**Mês 1 — Discovery e Pré-processamento (Critical Path):**

- [ ] Auditar amostra de 50 documentos de cada fonte para validar premissas de qualidade
- [ ] Definir processo de governança para resolução de conflitos entre documentos
- [ ] Escolher e testar pipeline de extração de tabelas (pdfplumber vs. Azure Document Intelligence)
- [ ] Mapear dados sensíveis e definir política de anonimização

**Mês 2 — Desenvolvimento e Indexação:**

- [ ] Construir pipeline de ingestão completo com monitoramento de saúde
- [ ] Implementar estratégia de fragmentação por tipo de documento
- [ ] Desenvolver interface no Teams com citação de fontes
- [ ] Criar suite de testes de regressão (50+ perguntas de referência)

**Mês 3 — Piloto e Go-Live:**

- [ ] Piloto com 10 atendentes durante 2 semanas
- [ ] Medir: tempo médio de busca, taxa de adoção, taxa de satisfação com as respostas
- [ ] Iterar com base no feedback antes do rollout para todos os 45 atendentes
- [ ] Treinar equipe de Operações/Compliance/Comercial no painel de gestão de conflitos

**Indicador crítico de sucesso:** Redução do tempo médio de busca de 12 para ≤ 2 minutos é atingível, **desde que** a qualidade da extração de tabelas seja validada antes do go-live. Esse é o maior risco técnico do projeto e deve ser o primeiro item de discovery do Mês 1.

---

_Documento preparado por DB1 Group | Versão 1.0 | Junho 2026_
_Para revisão ou complementação, contactar a equipe de Arquitetura de Soluções de IA da DB1._
