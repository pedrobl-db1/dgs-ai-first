# Implementação da conversa com Copilot

## Solicitação do usuário

Implementar as Tasks 001-005 do setup do endpoint, respeitando a estrutura atual do repositorio.

## O que foi feito

Foram implementadas as seguintes tasks no projeto `novatech-assistant`:

1. TASK-001 - Shared Types

- Arquivo: `src/shared/types.ts`
- Interfaces exportadas:
  - `QueryRequest { question: string }`
  - `QueryResponse { answer: string; source_document: string }`
  - `Chunk { id: string; content: string; source_document: string; score?: number }`
  - `SearchResult { chunks: Chunk[] }`

2. TASK-002 - Shared Config

- Arquivo: `src/shared/config.ts`
- Env vars obrigatorias com erro descritivo quando ausentes:
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
  - `AZURE_OPENAI_COMPLETION_DEPLOYMENT`
  - `AZURE_SEARCH_ENDPOINT`
  - `AZURE_SEARCH_API_KEY`
  - `AZURE_SEARCH_INDEX_NAME`
- Exportado `SYSTEM_PROMPT_PATH` com fallback para `./prompts/system-prompt.md`
- Exportado `CONTEXT_BUDGET` com:
  - `systemTokens: 4096`
  - `chunksTokens: 8192`

3. TASK-003 - Shared Logger

- Arquivo: `src/shared/logger.ts`
- Logger implementado com `pino()`
- Nível via `LOG_LEVEL`, default `info`
- Sem uso de `console.log`, `console.warn` ou `console.error`

4. TASK-004 - Shared Errors

- Arquivo: `src/shared/errors.ts`
- Classes de erro implementadas:
  - `ValidationError` com `field?: string`
  - `SearchError` com `statusCode?: number`
  - `CompletionError` com `statusCode?: number`
- Todas estendem `Error`

5. TASK-005 - Retry Utility

- Arquivo: `src/shared/retry.ts`
- Função exportada:
  - `withRetry<T>(fn, opts?)`
- Defaults:
  - `maxAttempts = 3`
  - `baseDelayMs = 200`
  - backoff exponencial com fator 2
- Cada tentativa é logada com número da tentativa e delay
- Ultimo erro é relançado ao esgotar tentativas

## Ajustes de dependência

- `pino` adicionado em `package.json`.

## Validacao executada

- Comando: `npm install`
- Comando: `npx tsc --noEmit`
- Resultado: compilação sem erros em modo strict.

## Observação de contexto

Durante a execução, haviam alterações não relacionadas no repositório. Elas nao foram revertidas nem modificadas pelo assistente.

## Nova interação - Task 006

### Solicitação do usuário

Implementar a Task 006 e acrescentar essa interação ao arquivo de implementação.

### O que foi feito

- Arquivo implementado: `src/functions/query/validator.ts`
- Criado schema `QueryRequestSchema` com Zod:
  - `question` obrigatorio como string
  - mínimo de 1 caractere
  - maximo de 1000 caracteres
- Criada função `parseQueryRequest(body: unknown): QueryRequest`
  - valida o body com `safeParse`
  - em caso de erro, lança `ValidationError`
  - inclui o campo inválido em `field` quando disponível
- Sem acoplamento ao SDK de Azure Functions

### Validacao executada

- Comando: `npx tsc --noEmit`
- Resultado: compilação sem erros em modo strict.

## Observação final

Por conta das tasks geradas serem muito pequenas, o usuário optou pela criação das 6 primeiras tasks para obter mais material avaliativo.
