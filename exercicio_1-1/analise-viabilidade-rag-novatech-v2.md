# Análise de Viabilidade Técnica: Assistente de IA Baseado em Documentos
## NovaTech — Projeto RAG para Atendimento ao Cliente
**DB1 Group | Junho 2026 | Versão 2.0**

---

> **Sobre esta versão:** A v2 corrige três imprecisões técnicas da v1 (detecção de contradições por embedding, comportamento do `openpyxl data_only`, e a técnica anti-*lost-in-middle*), revisa estimativas de overhead OCR para valores mais conservadores, adiciona uma seção de custo operacional ausente na v1, expande os riscos de 6 para 10 (incluindo controle de acesso, qualidade da base documental, viabilidade do prazo e limites de throughput), e inclui uma seção sobre o que o sistema não conseguirá responder — ponto crítico para gestão de expectativas.

---

## Sumário Executivo

Este documento analisa a viabilidade técnica de um assistente de IA baseado em RAG (*Retrieval-Augmented Generation*) para a equipe de atendimento ao cliente da NovaTech. O sistema proposto responde perguntas em linguagem natural consultando a documentação interna da empresa e indicando a fonte de cada resposta.

> **O que é RAG?** É uma arquitetura que combina dois passos: primeiro *recupera* fragmentos relevantes da base documental (busca semântica), depois *gera* uma resposta usando um LLM (modelo de linguagem), passando esses fragmentos como contexto. A resposta é fundamentada na documentação, não inventada pelo modelo.

A análise aponta que o projeto é **tecnicamente viável**, com as seguintes qualificações:

- O pré-processamento dos documentos — especialmente PDFs com tabelas e documentos escaneados — é o risco técnico número um e consome proporcionalmente mais esforço do que a integração com o LLM.
- A documentação contraditória identificada pela NovaTech é um problema de **governança de conhecimento**, não apenas técnico. O sistema pode detectar candidatos a conflito, mas a resolução exige processo humano — sem esse processo, o assistente simplesmente não serviu certos documentos, sem melhorar a qualidade da base.
- O prazo de 3 meses é **viável apenas com escopo controlado**. A v2 detalha os elementos que precisam ser priorizados versus diferidos para uma fase 2.
- O custo operacional estimado (~R$ 2.500/mês) precisa ser previsto no orçamento — estava ausente na v1.

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

Um desafio adicional frequentemente subestimado: **tabelas que ocupam múltiplas páginas**. Nesse caso, o cabeçalho da tabela aparece apenas na primeira página. A partir da segunda página, as linhas não têm contexto — a ferramenta de extração vê blocos de texto sem saber que são a continuação de uma tabela.

**Impacto no RAG**

Perguntas do tipo *"Qual o prazo de entrega para o Nordeste com carga de 8kg?"* podem gerar respostas incorretas mesmo que o dado correto esteja no documento. O modelo pode cruzar valores da linha errada da tabela e responder com confiança aparente — o pior cenário possível para um sistema de atendimento.

**Tratamento Técnico**

1. **Extração estruturada com bibliotecas especializadas:** Usar `pdfplumber` ou `camelot` (para PDFs nativos) para extrair tabelas como estruturas de dados, não como texto puro. Para tabelas multipágina, `pdfplumber` consegue detectar a continuidade quando o layout é consistente; quando não consegue, é necessário pós-processamento manual por regra.

2. **Serialização semântica em linguagem natural — formato explícito:** Converter cada linha da tabela em uma sentença autocontida. O formato escolhido deve ser linguagem natural, não markdown ou JSON, pois o modelo de embedding e o LLM foram treinados predominantemente em texto corrido.
   - *Formato recomendado:* `"Frete para a região Norte com peso entre 5 e 10 kg: prazo de 3 dias úteis, valor de R$ 12,50. (Fonte: Tabela de Fretes Regionais, versão set/2025, linha 14)"`
   - Incluir a identificação da fonte *dentro* do texto do chunk — isso garante que quando o chunk for recuperado, a rastreabilidade esteja no próprio conteúdo.

3. **Propagação de cabeçalho em tabelas multipágina:** Ao detectar que uma tabela continua na página seguinte, copiar os cabeçalhos da página original para cada bloco de continuação antes da serialização.

4. **Fallback para tabelas como imagem:** Documentos com tabelas renderizadas como imagem requerem **Azure Document Intelligence com modelo Layout** para extração. Isso cobre também fluxogramas embutidos — o serviço retorna uma representação estruturada do conteúdo visual.

5. **Teste de aceitação por tabela:** Para cada tabela crítica (fretes, SLAs), validar a extração com 5 perguntas de referência antes de incluir no índice de produção. Tabelas que não passam ficam em modo "texto puro com aviso" até correção manual.

---

### 1.2 PDFs Escaneados (OCR Necessário)

**Desafio**

Documentos escaneados são imagens — não há texto extraível diretamente. A aplicação de OCR (*Optical Character Recognition*) recupera o texto, mas introduz ruído proporcional à qualidade da digitalização: letras confundidas (`l` com `1`, `O` com `0`), palavras cortadas, hifenizações incorretas, parágrafos misturados.

**Estimativa de erro corrigida:** A v1 estimava overhead de +15%. Esse número corresponde a documentos digitalizados em condições ideais (300 DPI, folha plana, sem manchas). Documentos corporativos reais apresentam condições variadas — digitalização em lote com 200 DPI, folhas amareladas, carimbos sobre texto, selos de aprovação. A faixa realista é **+25% a +50% de overhead em tokens**, dependendo da qualidade do acervo. O valor exato só pode ser confirmado após auditoria de amostra no Mês 1.

Um documento com erro OCR de 10-15% por caracter é suficiente para corromper datas (`30 dias` → `3O dias`), valores monetários (`R$ 2,50` → `R$ 250`) e siglas críticas — todos os casos têm impacto direto em respostas ao cliente.

**Impacto no RAG**

- O índice vetorial é construído sobre texto ruidoso, reduzindo a chance de recuperar o fragmento certo.
- Tokens espúrios gerados por artefatos OCR consomem espaço no contexto sem contribuir com informação.
- Documentos com baixa qualidade OCR têm embeddings distorcidos — ficam "invisíveis" para perguntas que deveriam encontrá-los.

**Tratamento Técnico**

1. **Azure AI Document Intelligence com modelo Read:** Preferir sobre tesseract genérico. O serviço retorna score de confiança por palavra/bloco — use isso ativamente.

2. **Política de confiança por bloco:**
   - Score ≥ 0,90: ingerir normalmente
   - Score 0,75–0,89: ingerir com metadado `qualidade_ocr: media` + alerta na interface
   - Score < 0,75: colocar em quarentena para revisão humana — **não indexar**

3. **Limpeza pós-OCR:** Aplicar filtro para remover linhas com densidade de caracteres especiais acima de 30% (artefatos de digitalizações ruins), blocos com menos de 10 tokens (fragmentos inúteis) e sequências de caracteres repetidos (artefatos de selos).

4. **Metadado rastreável:** Todo chunk de documento OCR carrega `fonte: ocr`, `score_ocr_min`, `data_digitalizacao`. O assistente exibe esse metadado na resposta.

---

### 1.3 Wikis com Links e Referências Cruzadas (Confluence)

**Desafio**

Páginas de wiki raramente são autocontidas. Uma página sobre *Política de Devolução* pode dizer "conforme as regras da Seção 3 da Política de Frete" com um link para outra página. Quando essa página é fragmentada isoladamente, o fragmento contém uma referência irresolvível.

Além disso, macros customizadas do Confluence geram HTML ou marcações proprietárias que, quando exportadas, produzem texto estruturalmente incoerente.

**Cuidado com link expansion e referências circulares:** A técnica de embutir o conteúdo das páginas referenciadas (link expansion) precisa de controle de profundidade. Se a Página A referencia a Página B, que referencia a Página C, que referencia a Página A, um algoritmo ingênuo entra em loop infinito. Além disso, expandir todos os links recursivamente pode inflar chunks a tamanhos inúteis. A implementação correta expande **apenas um nível de profundidade** e usa cache para evitar re-expansão de páginas já visitadas na mesma sessão de ingestão.

**Impacto no RAG**

- Fragmentos que fazem sentido apenas dentro de um contexto maior geram respostas parciais.
- Links para páginas inexistentes (conteúdo deletado no Confluence mas referenciado em outras páginas) geram chunks com referências mortas — o assistente cita uma fonte que não existe.
- Macros exportadas como `{panel:title=Atenção}...{panel}` poluem o texto com marcações sem valor semântico.

**Tratamento Técnico**

1. **Link expansion com profundidade máxima 1 e cache de visitados:** Resolver referências diretas, não transitivas. Para a página A que referencia B: incluir o resumo de B no chunk de A. Para o link de B para C: registrar a dependência no grafo, mas não expandir recursivamente.

2. **Detecção de links mortos em pré-ingestão:** Antes de indexar, verificar via API do Confluence se todas as páginas referenciadas existem. Links mortos são sinalizados no chunk com `[REFERÊNCIA INDISPONÍVEL — ver original]` para que o atendente saiba que há contexto ausente.

3. **Fragmentação por hierarquia de cabeçalhos:** Respeitar a estrutura `H1 > H2 > H3` como delimitadores naturais de chunk. Cada chunk carrega no metadado a trilha de cabeçalhos pais: `{page: "Políticas de Frete", section: "Fretes Internacionais", subsection: "Restrições de Carga"}`.

4. **Conversores de macros comuns:** Mapear as 10 macros mais usadas no Confluence da NovaTech e criar regras de conversão simples antes da ingestão. Macros sem conversor mapeado: remover o markup, preservar o texto interno.

5. **Grafo de dependência para re-indexação em cascata:** Quando a Página B é atualizada, re-indexar automaticamente todas as páginas que a referenciam (dependentes diretos registrados no grafo).

---

### 1.4 Planilhas com Fórmulas Interdependentes

**Desafio**

Planilhas apresentam dois problemas sobrepostos. Primeiro, **células com fórmulas**: ao exportar, a ferramenta exporta ou a fórmula (ininteligível para o modelo) ou o valor calculado — mas esse valor pode estar desatualizado ou ausente. Segundo, **dependências entre abas**: a taxa de ICMS aplicável pode estar na aba "Configurações" enquanto a tabela de fretes na aba "Fretes" a usa silenciosamente — fragmentadas separadamente, as duas abas produzem chunks incompletos.

**Caveat importante sobre `openpyxl data_only=True`:** A v1 recomendava essa abordagem sem ressalvas. O comportamento real: `data_only=True` lê o *cache de valores calculados* que o Excel salva no arquivo. Se o arquivo foi gerado por automação (export de sistema ERP, script Python, etc.) ou salvo sem abrir no Excel após edição, esse cache está vazio — `openpyxl` retorna `None` silenciosamente para todas as células com fórmula, sem nenhum erro. O resultado é um corpus indexado com células em branco onde deveriam estar os valores críticos.

**Impacto no RAG**

- Valores calculados ausentes (retornados como `None`) geram chunks como `"Frete para SP: ___"` — inúteis.
- Fórmulas exportadas como texto consomem tokens sem valor informacional.
- Dados de abas interdependentes fragmentados separadamente produzem respostas inconsistentes.

**Tratamento Técnico**

1. **Validação do cache antes de usar `data_only=True`:** Após leitura, verificar a proporção de células `None` em colunas de dados. Se > 20% são `None`, o cache está vazio — sinalizar para pré-processamento manual.

2. **Pré-processamento garantido:** Antes da ingestão, abrir os arquivos Excel com uma instância do LibreOffice em modo headless (`--headless --calc`) para forçar recálculo e salvar os valores. Isso garante cache atualizado antes da leitura com `openpyxl`.

3. **Serialização explícita com contexto de configuração:** Para cada linha de dados, incluir os parâmetros relevantes das abas auxiliares:
   - *Metadado embutido no chunk:* `"[Parâmetros vigentes: ICMS_SP=12%, ICMS_RJ=20%, Taxa_Extra_Capital=5%] Frete SP para RJ, carga geral 10kg: valor base R$ 45,00, ICMS 20% aplicado = total R$ 54,00."`

4. **Atualização incremental por hash de conteúdo:** Calcular hash MD5 de cada aba individualmente. Re-indexar somente as abas modificadas desde a última ingestão — evita re-processamento completo das planilhas mensalmente.

5. **Alerta de dados potencialmente desatualizados:** Chunks de planilha com `data_ingestao` > 35 dias exibem aviso no assistente.

---

## 2. Estimativa de Consumo de Tokens

### Premissas do Cálculo

| Premissa | Valor Adotado | Justificativa |
|---|---|---|
| Conversão palavras → tokens | `tokens = palavras ÷ 0,75` | Padrão para texto em português (línguas latinas são ligeiramente menos densas em tokens que inglês) |
| Páginas por documento PDF (média) | 12 páginas | Estimativa para manuais e políticas. **Alta variância esperada**: documentos de 1 a 100+ páginas. Validar na amostra do Mês 1 |
| Palavras por página PDF (texto corrido) | 450 palavras | Páginas com margens, rodapés e formatação corporativa |
| Overhead de tabela (serialização) | +40% sobre texto base | Serializar tabelas em linguagem natural gera mais tokens que texto equivalente |
| Overhead de OCR (conservador) | +25% a +50% | **Corrigido da v1 (era +15%).** Faixa realista para acervos corporativos com qualidade variável. Usar 35% como estimativa central |
| Palavras por página Confluence | 600 palavras | Inclui overhead de expansão de links (+20%) |
| Tamanho médio de planilha serializada | 2.500 palavras por arquivo | Tabela de frete 100 linhas × 15 colunas serializada em sentenças |
| Overhead de metadados por chunk | +8% | Cabeçalhos de seção, trilha de documento, data, score OCR embutidos em cada chunk |

---

### 2.1 SharePoint — PDFs e Documentos Word (800 documentos)

**Categorização estimada do acervo:**

| Categoria | Qtd. Estimada | Características |
|---|---|---|
| Documentos texto corrido (manuais, políticas) | 500 docs | Texto simples, sem tabelas complexas |
| Documentos com tabelas (fretes, SLAs) | 200 docs | Texto + tabelas serializadas |
| Documentos escaneados (OCR) | 100 docs | Texto extraído via OCR com ruído |

**Grupo A — Texto corrido (500 documentos):**
```
500 docs × 12 páginas × 450 palavras        = 2.700.000 palavras
+ 8% overhead de metadados                  = 2.916.000 palavras
Tokens = 2.916.000 ÷ 0,75                  = 3.888.000 tokens
```

**Grupo B — Documentos com tabelas (200 documentos):**
```
200 docs × 12 páginas × 450 palavras        = 1.080.000 palavras (base)
+ 40% overhead de serialização              = 1.512.000 palavras
+ 8% overhead de metadados                  = 1.632.960 palavras
Tokens = 1.632.960 ÷ 0,75                  = 2.177.280 tokens
```

**Grupo C — Documentos escaneados OCR (100 documentos) — estimativa central (35% overhead):**
```
100 docs × 12 páginas × 450 palavras        = 540.000 palavras (base)
+ 35% overhead de OCR (central)             = 729.000 palavras
+ 8% overhead de metadados                  = 787.320 palavras
Tokens = 787.320 ÷ 0,75                    = 1.049.760 tokens

Cenário pessimista (50% overhead OCR):      = 972.000 palavras → 1.296.000 tokens
```

**Subtotal SharePoint: ~7.115.000 tokens (central) / ~7.362.000 tokens (pessimista)**

---

### 2.2 Confluence — Wiki Interna (400 páginas)

```
400 páginas × 600 palavras                  = 240.000 palavras (base)
+ 20% overhead de expansão de links         = 288.000 palavras
+ 8% overhead de metadados                  = 311.040 palavras
Tokens = 311.040 ÷ 0,75                    = 414.720 tokens
```

**Subtotal Confluence: ~415.000 tokens**

---

### 2.3 Pasta de Rede — Planilhas de Referência (30 planilhas)

```
30 planilhas × 2.500 palavras               = 75.000 palavras
+ 8% overhead de metadados                  = 81.000 palavras
Tokens = 81.000 ÷ 0,75                     = 108.000 tokens
```

**Subtotal Planilhas: ~108.000 tokens**

---

### Resumo do Corpus Total

| Fonte | Tokens (central) | Tokens (pessimista) | % do Total |
|---|---|---|---|
| SharePoint — texto corrido | 3.888.000 | 3.888.000 | 51,5% |
| SharePoint — tabelas | 2.177.000 | 2.177.000 | 28,8% |
| SharePoint — OCR | 1.050.000 | 1.296.000 | 13,9% / 16,2% |
| Confluence | 415.000 | 415.000 | 5,5% |
| Planilhas | 108.000 | 108.000 | 1,4% |
| **Total** | **~7.638.000** | **~7.884.000** | 100% |

> **Conclusão:** O corpus completo é ~60× maior que a janela de contexto de 128k tokens — confirmando que recuperar apenas o conteúdo relevante por consulta é o mecanismo central do sistema. A diferença entre cenário central e pessimista (~246.000 tokens) vem quase inteiramente da qualidade do OCR, reforçando por que a auditoria de amostra no Mês 1 é crítica.

---

## 3. Análise de Orçamento de Contexto

### 3.1 Mapa do Contexto Disponível

```
┌─────────────────────────────────────────────────────┐
│            JANELA DE CONTEXTO: 128.000 tokens       │
├─────────────────────────────────────────────────────┤
│  Reserva de segurança                               │
│  2.000 tokens                                       │
├─────────────────────────────────────────────────────┤
│  TOKENS EFETIVOS: 126.000 tokens                    │
│                                                     │
│  System Prompt (instruções do assistente)           │
│  ~1.500 tokens                                      │
│                                                     │
│  Histórico de conversa (últimas 4-6 trocas)         │
│  ~4.000 tokens                                      │
│                                                     │
│  Pergunta atual do atendente                        │
│  ~150 tokens                                        │
│                                                     │
│  CHUNKS RECUPERADOS (RAG)                           │
│  ~120.350 tokens disponíveis                        │
│                                                     │
│  Buffer para resposta gerada                        │
│  ~2.000 tokens                                      │
└─────────────────────────────────────────────────────┘
```

> **Nota sobre histórico:** A v1 estimava 3k tokens de histórico (3 trocas). Atendimentos de suporte tendem a ter 5-8 trocas em casos mais complexos. Usar 4-6 trocas (4k tokens) como planejamento, com janela deslizante + resumo comprimido para atendimentos longos.

### 3.2 Número Correto de Chunks por Requisição

O limite de chunks não pode ser um número fixo independente do tamanho dos chunks. A variável de controle real é o **orçamento de tokens para chunks**, derivado do que sobra após os componentes fixos.

**Orçamento para chunks: ~120k tokens**

| Tipo de Consulta | Chunks Alvo | Tokens Alvo | Lógica |
|---|---|---|---|
| Política simples (regra única) | 3–5 | 1.500–2.500 | Regra direta, sem ramificações |
| Cálculo de frete | 5–8 | 2.500–4.000 | Múltiplas variáveis + regra aplicável |
| Fluxo de processo (reclamação, devolução) | 8–12 | 4.000–6.000 | Etapas sequenciais interdependentes |
| Consulta comparativa (SLA por tipo de cliente) | 10–15 | 5.000–7.500 | Múltiplos segmentos para comparação |

**Verificação de token count obrigatória antes de cada chamada à API:** Como chunks de diferentes tipos têm tamanhos variáveis (um chunk de linha de tabela pode ter 120 tokens; um chunk de seção de manual pode ter 800 tokens), o código deve somar os tokens reais dos chunks recuperados e cortar quando o orçamento for atingido — não usar contagem de chunks como proxy.

### 3.3 Quando o Orçamento se Torna Insuficiente

**Cenário crítico 1 — Consulta com múltiplas tabelas de frete cruzadas:**
Remessa com produtos de categorias distintas, passando por dois CDs, destinos em estados diferentes. Resposta precisa de 3 tabelas × 5 linhas relevantes + 2 políticas de SLA + 1 regra de compliance. Estimativa: ~30 chunks = 15.000 tokens — ainda dentro do orçamento, mas o risco de atenção diluída aumenta.

*Compromisso:* Sumarização em cascata — usar um LLM para condensar as 5 linhas relevantes de cada tabela em 2-3 sentenças antes de inserir no contexto final. Custo: uma chamada extra de API por consulta desse tipo.

**Cenário crítico 2 — Histórico longo de conversa:**
Atendimento com 10+ trocas acumula 10-15k tokens de histórico, comprimindo o espaço para chunks.

*Compromisso:* Janela deslizante de histórico (últimas 5 trocas) + resumo comprimido das trocas anteriores em ~500 tokens. O resumo é gerado pelo LLM na primeira vez que o histórico excede 8 trocas.

**Cenário crítico 3 — Chunks de OCR com ruído elevado:**
Com overhead OCR de 50%, 12 chunks OCR consomem o mesmo espaço que 18 chunks limpos, com menos informação por token.

*Compromisso:* Limitar chunks de documentos com `qualidade_ocr: media` a no máximo 4 por requisição. Priorizar chunks com score OCR > 0,85.

---

## 4. Estratégia de Fragmentação

### 4.1 O Problema da Informação no Meio do Contexto

Quando o contexto contém muitas informações, modelos de linguagem tendem a priorizar o que está no início e no final, com atenção reduzida ao meio — fenômeno documentado por Liu et al. (2023).

```
CONTEXTO ENVIADO AO MODELO:
[System Prompt] → [Chunks] → [Pergunta]
                   ↑ início                  ↑ final
                   Alta atenção              Alta atenção
                              ↑ meio
                              Atenção reduzida
```

**Correção da v1:** A v1 recomendava *duplicar* os top chunks colocando-os tanto no início quanto no final do bloco de contexto. Essa abordagem está incorreta por duas razões: (a) duplicar chunks aumenta consumo de tokens sem garantia de melhoria proporcional; (b) o modelo pode simplesmente reforçar o chunk duplicado, introduzindo viés.

**Abordagem correta — ordenação por relevância com posicionamento nos extremos:**
Ordenar os chunks recuperados de forma que os mais relevantes ocupem as primeiras e últimas posições do bloco, com os de menor relevância no meio. Custo em tokens: zero (apenas reordenação). Implementação simples:

```python
chunks_ordenados = sorted(chunks_recuperados, key=lambda x: x.score, reverse=True)
contexto = (
    chunks_ordenados[:3]          # top 3 no início
    + chunks_ordenados[3:-2]      # demais no meio
    + chunks_ordenados[-2:]       # 2 mais relevantes restantes no final
)
```

### 4.2 Tamanho Alvo de Chunk por Tipo de Documento

**Alvo de 512 tokens (±10%) como tamanho padrão.** A escolha deste valor alinha com os limites de sequência dos modelos de embedding mais comuns (512 tokens por janela) e mantém os chunks semanticamente coesos.

| Tipo de Documento | Tamanho Alvo | Lógica do Corte |
|---|---|---|
| Políticas e manuais | 400–512 tokens | Por parágrafo ou subseção lógica (`H3`) |
| Tabelas de frete (linha serializada) | 150–300 tokens por grupo | 5–10 linhas relacionadas (ex: mesmo peso, todas as regiões) |
| Documentos OCR | 300–400 tokens | Menor para limitar impacto do ruído; corte por bloco de parágrafo detectado |
| Páginas Confluence | 450–512 tokens | Por seção, incluindo trilha de cabeçalhos pais |
| Planilhas serializadas | 200–300 tokens por bloco temático | Por conjunto de configuração coerente |

**Sobreposição (overlap) entre chunks consecutivos:** 50–80 tokens. Garante que sentenças que cruzam os limites de corte não percam contexto. O mesmo conteúdo que aparece no overlap de dois chunks adjacentes não é um problema — o re-ranker penaliza redundância.

### 4.3 Pipeline de Recuperação em Três Camadas

**Camada 1 — Busca vetorial (retrieval):**
Calcular similaridade de cosseno entre o embedding da pergunta e os embeddings do índice. Retornar top-20 candidatos. Modelo recomendado: `text-embedding-3-large` (Azure OpenAI) — multilíngue com bom desempenho em português.

**Camada 2 — Re-ranking (refinamento):**
Um *cross-encoder* (modelo que avalia o par pergunta-chunk diretamente, não apenas os embeddings separados) reordena os 20 candidatos e seleciona os top-N para envio ao LLM. Cross-encoders são mais precisos que busca vetorial pura porque processam a pergunta e o chunk em conjunto.

*Latência:* O re-ranking adiciona 300–600ms à consulta. Com a meta de reduzir de 12 minutos para menos de 2 minutos, essa latência é aceitável — mas deve ser monitorada em pico de uso.

**Camada 3 — Filtros por metadados (contextual):**
Após o re-ranking, aplicar boost/penalidade por metadados:

| Condição | Ajuste |
|---|---|
| Documento atualizado nos últimos 30 dias | +20% no score |
| Score de confiança OCR > 0,90 | +10% no score |
| Score de confiança OCR < 0,75 | −30% no score |
| Documento em quarentena por conflito | Excluído (não servido) |
| Mesma área que disparou a pergunta (ex: Comercial) | +15% no score |
| `data_ingestao` > 40 dias | Servido com alerta de data |

### 4.4 Fragmentação Hierárquica vs. Flat

| Tipo de Documento | Estratégia | Motivo |
|---|---|---|
| Manuais e políticas estruturados | **Hierárquica** | Hierarquia clara de cabeçalhos — recuperação em dois níveis melhora precisão |
| Manuais sem estrutura de cabeçalhos | **Flat por parágrafo** | Documentos sem H1-H3 consistentes não se beneficiam de hierarquia |
| Tabelas de frete | **Flat por linha serializada** | Cada linha é unidade atômica; hierarquia não agrega valor |
| Confluence (wiki) | **Hierárquica** | Dependências explícitas entre seções; hierarquia reduz perda de contexto |
| Planilhas | **Flat por bloco temático** | Grupos de linhas relacionadas são a unidade natural de busca |
| OCR (escaneados) | **Flat por bloco de parágrafo** | Estrutura original pode estar corrompida; usar blocos detectados pelo OCR |

---

## 5. Estimativa de Custo Operacional

*Esta seção estava ausente na v1. O custo operacional deve ser previsto no orçamento do projeto.*

### 5.1 Premissas

- 320 chamados/dia, 60% com consulta documental = **192 consultas/dia ao RAG**
- Distribuição de carga: ~70% das consultas entre 08h-12h e 13h-17h (pico ~25 consultas/hora)
- Tokens por consulta: ~8.000 input (system prompt + histórico + chunks) + ~500 output
- Modelo: GPT-4o via Azure OpenAI (disponível no Azure AI Services previsto)

### 5.2 Custo de Inferência (Azure OpenAI)

```
Input: 192 consultas × 8.000 tokens × 30 dias    = 46.080.000 tokens/mês
Custo input GPT-4o: $2,50 / 1M tokens            = $115,20/mês

Output: 192 consultas × 500 tokens × 30 dias     = 2.880.000 tokens/mês
Custo output GPT-4o: $10,00 / 1M tokens          = $28,80/mês

Subtotal inferência: ~$144/mês (~R$ 720/mês)
```

### 5.3 Custo do Índice Vetorial (Azure AI Search)

Azure AI Search (tier Standard S1, suficiente para ~7M tokens de corpus):
```
~$250/mês (~R$ 1.250/mês)
```

### 5.4 Custo de Reindexação (Azure Document Intelligence)

Ingestão inicial (OCR de 100 docs × 12 páginas = 1.200 páginas):
```
Azure Document Intelligence: $1,50 / 1.000 páginas
1.200 páginas = $1,80 (custo único)
```

Reindexação mensal (estimativa de 10% do corpus atualizado = 120 docs):
```
~120 docs × 2 páginas de tabelas complexas = ~240 páginas × $1,50/1.000 = $0,36/mês
```

### 5.5 Custo de Embedding (Re-indexação Mensal)

```
10% do corpus = ~764.000 tokens / mês
text-embedding-3-large: $0,13 / 1M tokens = $0,10/mês (desprezível)
```

### 5.6 Resumo de Custo Operacional Mensal

| Componente | Custo/mês (USD) | Custo/mês (BRL ~5,0) |
|---|---|---|
| Azure OpenAI (inferência) | ~$144 | ~R$ 720 |
| Azure AI Search (índice vetorial) | ~$250 | ~R$ 1.250 |
| Compute (pipeline de ingestão, lógica) | ~$50 | ~R$ 250 |
| Azure Document Intelligence (re-indexação) | ~$5 | ~R$ 25 |
| **Total Operacional Estimado** | **~$449/mês** | **~R$ 2.245/mês** |

> **Nota:** Esses valores pressupõem uso dentro das cotas padrão do Azure. Se o volume de consultas crescer (ex: extensão para outras equipes) ou o modelo for atualizado para GPT-4o-mini (mais barato) ou GPT-4-turbo (mais caro), os valores mudam proporcionalmente. Revisar após 60 dias de operação com dados reais.

---

## 6. O que o Sistema Não Conseguirá Responder

Esta seção define as fronteiras do sistema — crítica para gerenciar a expectativa da diretoria e dos atendentes.

### 6.1 Perguntas que Requerem Cálculo, não Consulta

O RAG recupera informações, não executa operações matemáticas de forma confiável. Perguntas como *"Qual será o custo total do frete para essa remessa específica?"* envolvem multiplicação de variáveis (peso × distância × fator de zona × ICMS). O sistema pode fornecer os valores de referência da tabela, mas o cálculo final depende de uma calculadora ou sistema de cotação integrado.

*Recomendação:* Para esse tipo de consulta, o assistente responde com os parâmetros encontrados na documentação e orienta o atendente a usar a ferramenta de cotação existente — não tenta calcular.

### 6.2 Perguntas sobre Estado em Tempo Real

*"O pedido do cliente X já foi despachado?"*, *"Qual o status da entrega Y?"* — essas perguntas requerem integração com o TMS (sistema de gestão de transporte) da NovaTech, não estão na documentação estática. O RAG não resolve isso.

*Recomendação:* Esclarecer na interface e no treinamento dos atendentes que o assistente responde sobre políticas e procedimentos — não sobre o status de operações em andamento.

### 6.3 Perguntas cuja Resposta Correta é "Depende"

Documentação de compliance frequentemente define regras com exceções e casos especiais que se contradizem dependendo do contexto. O assistente vai recuperar a regra geral e pode omitir a exceção que se aplica ao caso específico.

*Recomendação:* Para consultas de compliance complexas, o assistente deve explicitamente indicar: *"Esta resposta cobre o caso geral. Para situações especiais, consulte a equipe de Compliance."*

### 6.4 Perguntas onde a Base de Conhecimento é Lacunosa

Aproximadamente **15-25% das consultas** — estimativa conservadora baseada em projetos similares — serão sobre tópicos não documentados ou documentados de forma insuficiente na base atual. O sistema responderá honestamente *"Não encontrei documentação específica sobre isso"* — o que é o comportamento correto, mas significa que a meta de resolver 60% dos chamados via assistente pode demorar mais para ser atingida enquanto a base não for completada.

*Recomendação:* Implementar log de consultas sem resposta satisfatória. A equipe de cada área revisa esse log mensalmente e cria/atualiza os documentos ausentes — o assistente melhora continuamente.

---

## 7. Riscos e Mitigação

### 7.1 Documentos Contraditórios

**Descrição:** A NovaTech confirmou que versões diferentes de documentos se contradizem. O sistema RAG pode recuperar fragmentos de versões conflitantes e entregá-los ao modelo — que gera uma resposta sintetizando as duas versões, silenciosamente.

**Probabilidade:** Alta | **Impacto:** Alto

**Correção técnica da v1:** A detecção por "similaridade de embeddings acima de 85%" é incorreta para esse problema. Alta similaridade semântica indica que dois documentos são topicamente próximos — não que se contradizem. Um chunk afirmando *"prazo: 30 dias"* e outro *"prazo: 45 dias"* pode ter 92% de similaridade sem que o threshold de cosseno detecte o conflito.

**Abordagem correta:**
1. Identificar candidatos a conflito por alta similaridade de embedding (>85%) — essa etapa apenas filtra pares relevantes para análise.
2. Para cada par candidato, usar um LLM com prompt específico para extrair afirmações factuais (datas, valores, percentuais, prazos) de cada chunk e comparar — divergência em afirmações numericamente comparáveis aciona a flag de conflito.
3. Documentos em conflito entram em quarentena: não são servidos pelo RAG até resolução humana.
4. Painel de resolução: a equipe responsável (Operações/Compliance/Comercial) visualiza os pares conflitantes, define a versão oficial, e o outro documento é arquivado — não apenas ocultado.

---

### 7.2 Controle de Acesso — ACLs Não Respeitadas pelo Índice

*Este risco estava ausente na v1.*

**Descrição:** Documentos no SharePoint têm permissões por usuário/grupo (ACLs). Um atendente sem permissão para visualizar um documento confidencial (ex: tabela de preços negociados com grandes clientes) não pode acessá-lo diretamente no SharePoint — mas se o índice RAG não respeitar essas ACLs, o mesmo atendente pode recuperar o conteúdo via consulta ao assistente.

**Probabilidade:** Alta (ACLs existem em qualquer SharePoint corporativo) | **Impacto:** Alto (falha de segurança com risco de exposição de dados sensíveis)

**Mitigação:**
- Mapear no discovery quais documentos têm ACLs restritas no SharePoint.
- Implementar filtragem de documentos por perfil do usuário antes do retrieval: ao receber a consulta, o sistema verifica via Microsoft Graph API quais documentos o usuário autenticado tem permissão para visualizar, e o retrieval é feito apenas sobre esse subconjunto.
- Alternativa mais simples (menor esforço, menor cobertura): criar dois índices separados — um "público" (acessível a todos os 45 atendentes) e um "restrito" (acessível apenas por perfil específico, ex: supervisores).
- Documentar explicitamente quais documentos entrarão em qual índice antes de começar a ingestão.

---

### 7.3 Qualidade da Base Documental como Risco de Negócio

*Este risco estava ausente na v1.*

**Descrição:** O projeto pressupõe que a documentação interna da NovaTech, uma vez indexada, produzirá respostas confiáveis. Mas o cliente confirmou que a equipe resolve contradições *"perguntando para quem sabe"* — o que indica que parte do conhecimento operacional real está na cabeça das pessoas, não nos documentos. Além disso, documentos desatualizados, incompletos ou escritos de forma ambígua geram respostas de baixa qualidade não por falha técnica do RAG, mas por falha da base de conhecimento.

**Probabilidade:** Média-Alta (confirmado indiretamente pelo cliente) | **Impacto:** Alto (o assistente propaga imprecisões da documentação com aparência de autoridade)

**Mitigação:**
- Durante o discovery, auditar a qualidade dos 50 documentos mais consultados (não apenas a qualidade técnica de extração, mas a qualidade do conteúdo em si).
- Identificar os "donos de conhecimento" em cada área — as pessoas que hoje respondem as dúvidas informalmente — e envolvê-las na validação das respostas do assistente durante o piloto.
- Implementar o log de consultas sem resposta satisfatória como mecanismo contínuo de identificação de lacunas.
- Comunicar à diretoria: a qualidade do assistente é limitada pela qualidade da documentação. Se a documentação for atualizada e completada, o assistente melhora sem mudanças técnicas.

---

### 7.4 Qualidade da Extração de Tabelas

**Descrição:** Tabelas de frete são o coração da operação. Se a extração falhar — por OCR ruim, estrutura tabular incomum, ou tabelas como imagem — as respostas sobre cálculo de frete serão imprecisas.

**Probabilidade:** Alta | **Impacto:** Alto (erro de frete tem impacto financeiro direto)

**Mitigação:**
- Suite de testes de regressão: 50 perguntas sobre tabelas de frete com respostas esperadas, executada após cada re-indexação. Taxa de acerto alvo: ≥ 90%. Abaixo disso: bloquear deploy e acionar equipe técnica.
- Para as 20 tabelas mais consultadas: manter uma versão de fallback em texto estruturado, mantida manualmente pela equipe de Operações. Se a extração automática falhar os testes de aceitação, o fallback é servido com alerta: *"Dados verificados manualmente — atualização automática em revisão."*
- Extração paralela com duas ferramentas para tabelas de alto valor: comparar resultados de `pdfplumber` e Azure Document Intelligence. Divergência > 5% aciona revisão manual antes de indexar.

---

### 7.5 Desatualização Silenciosa do Índice

**Descrição:** Sem automação de re-indexação, o índice envelhece silenciosamente. O assistente responde com confiança sobre regras que mudaram há semanas.

**Probabilidade:** Alta (sem automação, a desatualização é certa) | **Impacto:** Médio-Alto

**Mitigação:**
- **SharePoint:** Webhook via Microsoft Graph API para eventos de modificação de arquivo. Dispara re-indexação do documento modificado em até 30 minutos.
- **Confluence:** Polling da API REST a cada 6 horas verificando `lastModifiedDate` > `última_ingestão`. Re-indexar páginas modificadas e todas as suas dependentes (via grafo de referências).
- **Planilhas:** Script PowerShell agendado diariamente, comparando hash MD5 dos arquivos. Re-indexar apenas arquivos com hash alterado.
- **Monitoramento ativo:** Dashboard de saúde do índice com alerta automático se nenhuma atualização for processada em 35 dias (possível falha silenciosa no pipeline de ingestão).
- **Metadado de data em todo chunk:** O assistente exibe data de ingestão em respostas baseadas em conteúdo com mais de 40 dias.

---

### 7.6 Alucinação com Alta Confiança Aparente

**Descrição:** Modelos de linguagem podem gerar informações incorretas apresentadas com confiança — especialmente quando os chunks recuperados são insuficientes ou ambíguos.

**Probabilidade:** Média | **Impacto:** Alto

**Mitigação:**
- Instruir o modelo no system prompt a citar a fonte específica (documento + seção + data) de cada afirmação.
- Quando o score máximo de similaridade dos chunks recuperados for < 0,75: o assistente responde *"Não encontrei documentação específica. Escale para [área responsável]."* — não tenta gerar uma resposta.
- Botão "Ver Fonte" na interface abre o trecho original — cria hábito de verificação.
- Amostragem de 10% das consultas para revisão humana nos primeiros 30 dias. Medir taxa de respostas incorretas.

---

### 7.7 Rate Limits e Throughput da API

*Este risco estava ausente na v1.*

**Descrição:** Azure OpenAI tem cotas de tokens por minuto (TPM) e requisições por minuto (RPM) configuradas por deployment. Com ~25 consultas/hora em pico e ~8.000 tokens de input por consulta, o consumo em pico é ~200.000 tokens/hora. A cota padrão para GPT-4o no Azure OpenAI pode ser inferior a isso em deployments não provisionados.

**Probabilidade:** Média | **Impacto:** Médio (timeout ou degradação em horários de pico)

**Mitigação:**
- Provisionar quota de TPM antecipadamente com base na estimativa de pico: solicitar ao menos 50k TPM (tokens por minuto) no deployment GPT-4o.
- Implementar fila com backoff exponencial para consultas em período de burst.
- Monitorar taxa de erros 429 (rate limit) em produção e ajustar quota se necessário.
- Considerar uso de GPT-4o-mini para consultas de baixa complexidade (regras simples, busca de um campo específico) — 6× mais barato, 3× maior quota padrão.

---

### 7.8 Adoção Baixa pelos Atendentes

**Descrição:** Um sistema tecnicamente excelente pode ser subutilizado se os atendentes não confiarem nele ou se o fluxo de uso introduzir atrito.

**Probabilidade:** Média | **Impacto:** Alto (ROI do projeto depende de adoção real)

**Mitigação:**
- 5–8 atendentes experientes como *champions* durante o desenvolvimento — testam, sugerem melhorias, treinam colegas.
- Integração direta no Microsoft Teams (canal de atendimento) — zero atrito de ferramenta nova.
- Feedback estruturado nos primeiros 60 dias: thumbs up/down por resposta. Respostas negativas alimentam backlog de melhoria.
- Comunicar a meta concreta: *"O assistente vai te poupar 10 minutos por chamado. Nos primeiros dias, verifique as fontes para ganhar confiança no sistema."*

---

### 7.9 Viabilidade do Prazo de 3 Meses

*Este risco estava ausente na v1.*

**Descrição:** O prazo de 3 meses para discovery + desenvolvimento + go-live é apertado para a complexidade técnica deste projeto. O pipeline de ingestão com OCR, detecção de conflitos, extração de tabelas, grafo de dependências Confluence e automação de re-indexação são individualmente não triviais.

**Probabilidade:** Alta que haja ajustes de escopo | **Impacto:** Médio (prazo pode escorregar, ou funcionalidades importantes ficam de fora)

**Mitigação — Estratégia de escopo em duas fases:**

*Fase 1 (3 meses — go-live inicial):*
- Ingestão dos 500 documentos de texto corrido do SharePoint (sem OCR, sem tabelas complexas)
- Ingestão das 400 páginas do Confluence (sem link expansion completa — apenas texto)
- Interface básica no Teams com citação de fonte
- Re-indexação manual mensal (sem automação)
- **Coberto:** ~70% das consultas de política e procedimento

*Fase 2 (meses 4-6):*
- Pipeline OCR para os 100 documentos escaneados
- Extração e serialização de tabelas complexas de frete
- Automação de re-indexação (webhooks SharePoint + Confluence)
- Detecção de conflitos com LLM
- Controle de acesso por ACL
- **Coberto:** 100% das fontes, incluindo tabelas de frete

> Essa divisão entrega valor real no prazo comprometido (Fase 1) e reserva as partes técnicas mais complexas para uma fase com mais tempo e validação real de uso.

---

### 7.10 Privacidade e Compliance

**Descrição:** Documentos de compliance podem conter dados pessoais de clientes ou informações contratuais confidenciais.

**Probabilidade:** Baixa-Média | **Impacto:** Alto

**Mitigação:**
- Mapeamento de dados sensíveis no corpus antes do desenvolvimento.
- Anonimização em pré-processamento (CPFs, CNPJs, nomes de clientes substituídos por tokens).
- Azure OpenAI processa dados dentro do tenant Azure da NovaTech — dados não saem para treinamento de modelos. Documentar essa garantia para equipe jurídica.
- Categoria *"apenas consulta humana"*: documentos nunca entram no índice RAG, mas o assistente direciona o atendente ao lugar certo quando a consulta é sobre esse tema.

---

## Conclusão e Roadmap

A análise confirma viabilidade técnica com **escopo em duas fases como caminho mais seguro para o prazo.**

### Fase 1 — Go-Live em 3 Meses (Escopo Controlado)

**Mês 1 — Discovery e Fundações:**
- [ ] Auditar amostra de 50 documentos por fonte — qualidade de conteúdo e de extração
- [ ] Mapear ACLs do SharePoint e definir estratégia de controle de acesso
- [ ] Mapear dados sensíveis e definir política de anonimização
- [ ] Testar extração de tabelas em amostra de 20 documentos com tabelas complexas
- [ ] Definir processo de governança para resolução de conflitos (dono de processo em cada área)
- [ ] Provisionar quota Azure OpenAI adequada ao volume estimado

**Mês 2 — Desenvolvimento:**
- [ ] Pipeline de ingestão para texto corrido e Confluence (sem OCR, tabelas simplificadas)
- [ ] Índice vetorial com metadados rastreáveis e filtros por data e área
- [ ] Interface Teams: pergunta → resposta → citação de fonte → botão "Ver Fonte"
- [ ] Suite de testes de regressão (50+ perguntas de referência com resposta esperada)
- [ ] Monitoramento de saúde do índice e log de consultas sem resposta satisfatória

**Mês 3 — Piloto e Go-Live:**
- [ ] Piloto com 8–10 atendentes por 2 semanas
- [ ] Medir: tempo médio de busca, taxa de adoção, taxa de thumbs down
- [ ] Iterar antes de rollout para os 45 atendentes
- [ ] Apresentar relatório de Fase 1 com baseline para Fase 2

### Fase 2 — Funcionalidades Completas (Meses 4-6)

- [ ] OCR (Azure Document Intelligence) para documentos escaneados
- [ ] Extração e serialização de tabelas de frete complexas com testes de aceitação
- [ ] Automação de re-indexação via webhooks SharePoint e Confluence
- [ ] Detecção de conflitos com LLM + painel de resolução
- [ ] Controle de acesso por ACL do SharePoint
- [ ] Estimativa de custo real após 60 dias de operação

**Indicador crítico de sucesso:** A meta de reduzir de 12 para ≤ 2 minutos de busca é atingível para os tipos de consulta cobertos na Fase 1 (políticas, procedimentos gerais). A redução completa — incluindo cálculos de frete e SLAs por tipo de cliente — depende da Fase 2 e da qualidade da extração de tabelas, que só pode ser confirmada após os testes de aceitação do Mês 1.

---

*Documento preparado por DB1 Group | Versão 2.0 | Junho 2026*
*Alterações desta versão documentadas no cabeçalho. Versão anterior disponível em `analise-viabilidade-rag-novatech.md`.*
