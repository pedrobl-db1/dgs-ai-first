# Tasks — Query Endpoint

Derivadas do [plan.md](./plan.md). Seguem a organização de diretórios de `src/` e `tests/` do repositório.

---

## TASK-001 — Shared Types

**Descrição:** Implementar `src/shared/types.ts` com os contratos de dados usados por toda a feature.

**Critérios de aceite:**
- Exporta `QueryRequest { question: string }` e `QueryResponse { answer: string; source_document: string }`
- Exporta `Chunk { id: string; content: string; source_document: string; score?: number }`
- Exporta `SearchResult { chunks: Chunk[] }`
- Compila sem erros em modo strict (`tsc --noEmit`)

**Dependências:** nenhuma

**Estimativa:** P

---

## TASK-002 — Shared Config

**Descrição:** Implementar `src/shared/config.ts` lendo variáveis de ambiente necessárias para a feature.

**Critérios de aceite:**
- Lê e exporta as seguintes env vars (lança erro descritivo se ausente): `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`, `AZURE_OPENAI_COMPLETION_DEPLOYMENT`, `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_API_KEY`, `AZURE_SEARCH_INDEX_NAME`
- Exporta `SYSTEM_PROMPT_PATH` com fallback para `./prompts/system-prompt.md`
- Exporta `CONTEXT_BUDGET { systemTokens: 4096; chunksTokens: 8192 }`
- Compila sem erros em modo strict

**Dependências:** nenhuma

**Estimativa:** P

---

## TASK-003 — Shared Logger

**Descrição:** Implementar `src/shared/logger.ts` com pino, substituindo qualquer uso de `console.log`.

**Critérios de aceite:**
- Exporta instância `logger` criada com `pino()`
- Nivel padrão configurável via env var `LOG_LEVEL` (default `info`)
- Nenhum `console.log/warn/error` no arquivo

**Dependências:** nenhuma

**Estimativa:** P

---

## TASK-004 — Shared Errors

**Descrição:** Implementar `src/shared/errors.ts` com classes de erro tipadas para a feature.

**Critérios de aceite:**
- Exporta `ValidationError extends Error` com campo `field?: string`
- Exporta `SearchError extends Error` com campo `statusCode?: number`
- Exporta `CompletionError extends Error` com campo `statusCode?: number`
- Todas herdam de `Error` e preservam `message` e `stack`

**Dependências:** TASK-001

**Estimativa:** P

---

## TASK-005 — Retry Utility

**Descrição:** Criar `src/shared/retry.ts` com função genérica de retry com exponential backoff.

**Critérios de aceite:**
- Exporta `withRetry<T>(fn: () => Promise<T>, opts?: { maxAttempts?: number; baseDelayMs?: number }): Promise<T>`
- Default: 3 tentativas, delay inicial 200 ms, fator 2 (400 ms, 800 ms)
- Loga cada tentativa via `logger` (TASK-003) com número da tentativa e delay
- Relança o último erro após esgotar tentativas

**Dependências:** TASK-003

**Estimativa:** P

---

## TASK-006 — Input Validator

**Descrição:** Implementar `src/functions/query/validator.ts` com schema Zod para o body do POST.

**Critérios de aceite:**
- Exporta `QueryRequestSchema = z.object({ question: z.string().min(1).max(1000) })`
- Exporta `parseQueryRequest(body: unknown): QueryRequest` que lança `ValidationError` (TASK-004) em caso de falha, com o campo inválido no `field`
- Sem acoplamento a Azure Functions SDK (facilita testes unitários)

**Dependências:** TASK-001, TASK-004

**Estimativa:** P

---

## TASK-007 — Search Service

**Descrição:** Implementar `src/services/search.ts`: gera embedding da pergunta e recupera top-5 chunks do Azure AI Search.

**Critérios de aceite:**
- Exporta `searchChunks(question: string): Promise<SearchResult>`
- Passo 1 — Embedding: chama `POST {AZURE_OPENAI_ENDPOINT}/openai/deployments/{EMBEDDING_DEPLOYMENT}/embeddings` e extrai o vetor
- Passo 2 — Busca vetorial: chama Azure AI Search com `top=5` e o vetor gerado; mapeia resultado para `Chunk[]`
- Ambas as chamadas HTTP usam `withRetry` (TASK-005)
- Lança `SearchError` em caso de falha com `statusCode` da resposta HTTP
- Usa `logger` com campos estruturados (`question`, `chunksFound`)

**Dependências:** TASK-001, TASK-002, TASK-003, TASK-004, TASK-005

**Estimativa:** M

---

## TASK-008 — Prompt Builder

**Descrição:** Implementar `src/services/prompt-builder.ts` montando o prompt respeitando o context budget definido na ADR-0002.

**Critérios de aceite:**
- Exporta `buildPrompt(question: string, chunks: Chunk[]): Promise<{ systemPrompt: string; userMessage: string }>`
- Lê o system prompt de `SYSTEM_PROMPT_PATH` (TASK-002); lança erro se arquivo não encontrado
- Trunca chunks se a soma dos tokens estimados ultrapassar `CONTEXT_BUDGET.chunksTokens` (estimativa simples: `chars / 4`)
- System prompt respeitado em até `CONTEXT_BUDGET.systemTokens` tokens
- `userMessage` concatena chunks selecionados (com `source_document`) e a pergunta
- Loga número de chunks incluídos vs. descartados

**Dependências:** TASK-001, TASK-002, TASK-003

**Estimativa:** M

---

## TASK-009 — Completion Service

**Descrição:** Implementar `src/services/completion.ts`: envia prompt para GPT-4o e extrai resposta com `source_document`.

**Critérios de aceite:**
- Exporta `getCompletion(systemPrompt: string, userMessage: string, chunks: Chunk[]): Promise<QueryResponse>`
- Chama `POST {AZURE_OPENAI_ENDPOINT}/openai/deployments/{COMPLETION_DEPLOYMENT}/chat/completions`
- Usa `withRetry` (TASK-005) para a chamada HTTP
- `source_document` é o `source_document` do chunk de maior score em `chunks`
- Lança `CompletionError` em caso de falha com `statusCode`
- Loga `promptTokens` e `completionTokens` retornados pela API

**Dependências:** TASK-001, TASK-002, TASK-003, TASK-004, TASK-005

**Estimativa:** M

---

## TASK-010 — Response Builder

**Descrição:** Implementar `src/functions/query/response-builder.ts` montando o objeto de resposta HTTP.

**Critérios de aceite:**
- Exporta `buildSuccessResponse(result: QueryResponse): { status: 200; body: QueryResponse; headers: Record<string, string> }`
- Exporta `buildErrorResponse(error: unknown): { status: number; body: { error: string } }` mapeando `ValidationError` → 400, `SearchError`/`CompletionError` → 502, demais → 500
- `Content-Type: application/json` em todos os casos
- Sem dependência direta no Azure Functions SDK

**Dependências:** TASK-001, TASK-004

**Estimativa:** P

---

## TASK-011 — Query Handler

**Descrição:** Implementar `src/functions/query/handler.ts` orquestrando o fluxo completo como Azure Functions v4 HTTP trigger.

**Critérios de aceite:**
- Registra rota `POST /api/query` usando `app.http('query', { methods: ['POST'], ... })`
- Fluxo: parse body → `parseQueryRequest` → `searchChunks` → `buildPrompt` → `getCompletion` → `buildSuccessResponse`
- Erros capturados via try/catch e delegados a `buildErrorResponse`
- Loga início e fim de cada request com `requestId` (gerado a partir do header `x-request-id` ou UUID fallback)
- Nenhum `console.log` no arquivo

**Dependências:** TASK-006, TASK-007, TASK-008, TASK-009, TASK-010

**Estimativa:** M

---

## TASK-012 — Unit Tests: Validator

**Descrição:** Criar `tests/unit/query-validator.test.ts` cobrindo o módulo `validator.ts`.

**Critérios de aceite:**
- Testa: pergunta válida retorna objeto `QueryRequest` correto
- Testa: body vazio lança `ValidationError` com `field: 'question'`
- Testa: pergunta acima de 1000 chars lança `ValidationError`
- Testa: campo `question` não-string lança `ValidationError`
- Cobertura de linhas ≥ 80 % para o arquivo alvo (`vitest run --coverage`)

**Dependências:** TASK-006

**Estimativa:** P

---

## TASK-013 — Unit Tests: Prompt Builder

**Descrição:** Criar `tests/unit/prompt-builder.test.ts` cobrindo `prompt-builder.ts`.

**Critérios de aceite:**
- Testa: chunks dentro do budget são todos incluídos
- Testa: chunks que ultrapassam `chunksTokens` são truncados (verifica que o total de chars / 4 ≤ budget)
- Testa: ausência do arquivo de system prompt lança erro descritivo
- Usa fixtures de `tests/fixtures/chunks.ts`
- Cobertura de linhas ≥ 80 %

**Dependências:** TASK-008

**Estimativa:** P

---

## TASK-014 — Unit Tests: Response Builder

**Descrição:** Criar `tests/unit/response-builder.test.ts` cobrindo `response-builder.ts`.

**Critérios de aceite:**
- Testa: `buildSuccessResponse` retorna `status: 200` e `Content-Type: application/json`
- Testa: `buildErrorResponse` com `ValidationError` retorna `status: 400`
- Testa: `buildErrorResponse` com `SearchError` retorna `status: 502`
- Testa: `buildErrorResponse` com `Error` genérico retorna `status: 500`
- Cobertura de linhas ≥ 80 %

**Dependências:** TASK-010

**Estimativa:** P

---

## TASK-015 — Integration Tests: Query Handler

**Descrição:** Criar `tests/integration/query-handler.test.ts` testando o handler de ponta a ponta com stubs das APIs Azure.

**Critérios de aceite:**
- Stubeia chamadas HTTP ao Azure OpenAI (embedding + completion) e Azure AI Search usando `vi.spyOn` ou interceptor HTTP
- Testa golden path: POST válido retorna `200` com `answer` e `source_document` preenchidos
- Testa: corpo inválido retorna `400`
- Testa: falha no Search (5xx simulado) retorna `502` após retries esgotados
- Testa: falha no Completion (5xx simulado) retorna `502` após retries esgotados
- Usa fixtures de `tests/fixtures/queries.ts` e `tests/fixtures/expected-responses.ts`

**Dependências:** TASK-011, TASK-012, TASK-013, TASK-014

**Estimativa:** M

---

## TASK-016 — Eval Tests: Qualidade das Respostas

**Descrição:** Criar `tests/eval/query-eval.test.ts` avaliando a qualidade semântica das respostas contra o corpus.

**Critérios de aceite:**
- Para cada caso em `tests/fixtures/expected-responses.ts`: envia pergunta real (sem stubs de IA) e verifica que a resposta contém palavras-chave esperadas (lista por caso de teste)
- Verifica que `source_document` corresponde ao documento esperado no fixture
- Marcado com `test.concurrent` para rodar em paralelo
- Guarda relatório de passes/falhas em saída de console estruturada (pino)
- Deve rodar isolado (`vitest run tests/eval`) sem impactar cobertura de unit/integration

**Dependências:** TASK-011, TASK-015

**Estimativa:** G
