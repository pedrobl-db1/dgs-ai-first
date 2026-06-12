# Skills Tree — NovaTech Assistant

> Mapeamento da hierarquia de skills que governa a geração de artefatos no projeto.
> Hierarquia: **Foundation** (convenções globais) → **Domain** (padrões por camada) → **Artifact** (receitas de geração).

---

## Visão geral da hierarquia

```
Foundation
├── typescript-conventions      ← base de tipagem e estilo para todo o código TS
├── error-handling              ← padrão de erros e respostas HTTP em todos os módulos
├── logging                     ← uso de pino: campos obrigatórios, níveis, correlação
├── env-config                  ← carregamento de variáveis de ambiente com zod/validação
└── project-structure           ← layout do repositório e regras de co-localização

Domain
├── azure-functions-endpoint    ← contrato HTTP, middleware, schema de entrada/saída
├── rag-pipeline                ← etapas de chunking → embedding → indexing → retrieval
├── testing-patterns            ← estrutura de testes com vitest: unit vs integration
├── react-components            ← convenções de componentes React no painel web
└── azure-ai-search-integration ← integração com índice semântico (mocked localmente)

Artifact
├── create-rag-endpoint         ← endpoint Azure Function com fluxo RAG completo
├── create-integration-test     ← teste de integração para um endpoint existente
├── create-react-card           ← componente de card React (resposta ou feedback)
├── create-endpoint-doc         ← documentação técnica de endpoint (README de módulo)
└── create-product-spec         ← spec de produto seguindo template SDD
```

---

## Foundation Skills

Skills de nível Foundation definem as convenções que **todo artefato gerado precisa respeitar**, independente da camada. São consumidas como pré-condição implícita por todas as skills de Domain e Artifact.

### `foundation/typescript-conventions`

| Campo | Valor |
|---|---|
| Arquivo | `skills/foundation/typescript-conventions.md` |
| Propósito | Tipagem estrita, convenções de nomenclatura e organização de módulos TypeScript |
| Conteúdo | Target ES2022, `strict: true`, uso obrigatório de `type` vs `interface`, convenções de export, proibição de `any` explícito, padrão de imports (sem barrel files salvo em `index.ts` de camada) |
| Consumida por | Todos os Artifact skills que geram código `.ts` |

### `foundation/error-handling`

| Campo | Valor |
|---|---|
| Arquivo | `skills/foundation/error-handling.md` |
| Propósito | Padrão único de criação, propagação e serialização de erros em toda a aplicação |
| Conteúdo | Classe `AppError` com código e mensagem, mapeamento para status HTTP, nunca expor stack trace ao cliente, log do erro completo no servidor, formato de resposta de erro `{ error: { code, message } }` |
| Consumida por | `domain/azure-functions-endpoint`, `artifact/create-rag-endpoint`, `artifact/create-integration-test` |

### `foundation/logging`

| Campo | Valor |
|---|---|
| Arquivo | `skills/foundation/logging.md` |
| Propósito | Uso consistente da biblioteca `pino` para logs estruturados em todos os serviços |
| Conteúdo | Instância singleton do logger, campos obrigatórios por log (`requestId`, `module`, `durationMs`), níveis (`info` para fluxo normal, `warn` para fallback, `error` para falhas com stack), proibição de `console.log` em código de produção |
| Consumida por | `domain/azure-functions-endpoint`, `domain/rag-pipeline`, `artifact/create-rag-endpoint` |

### `foundation/env-config`

| Campo | Valor |
|---|---|
| Arquivo | `skills/foundation/env-config.md` |
| Propósito | Carregamento e validação de variáveis de ambiente com schema explícito |
| Conteúdo | Schema `zod` para todas as envs, falha rápida na inicialização se env inválida, nunca ler `process.env` direto fora do módulo de config, nomenclatura `SCREAMING_SNAKE_CASE` |
| Consumida por | Qualquer artefato que acesse variáveis de ambiente (endpoints, serviços de AI) |

### `foundation/project-structure`

| Campo | Valor |
|---|---|
| Arquivo | `skills/foundation/project-structure.md` |
| Propósito | Layout do repositório e regras de onde cada tipo de artefato deve residir |
| Conteúdo | `src/functions/<nome>/` para endpoints, `src/services/` para lógica de negócio, `src/pipeline/` para etapas de ingestão, `specs/<feature>/` para requisitos, `skills/` para templates, `docs/adr/` para decisões arquiteturais |
| Consumida por | Todos os Artifact skills (determina onde gerar os arquivos) |

---

## Domain Skills

Skills de nível Domain definem **como cada camada da aplicação é estruturada**. Ficam entre as convenções globais (Foundation) e as receitas específicas (Artifact). Toda Domain skill referencia as Foundation skills que aplica.

### `domain/azure-functions-endpoint`

| Campo | Valor |
|---|---|
| Arquivo | `skills/domain/azure-functions-endpoint.md` |
| Propósito | Contrato e estrutura padrão de qualquer Azure Function HTTP neste projeto |
| Conteúdo | Handler com `HttpRequest` → validação com `zod` → lógica → `HttpResponse`, middleware de logging (requestId injetado), middleware de error handling (captura `AppError` e erros inesperados), convenção de co-localizar `handler.ts` + arquivos auxiliares dentro de `src/functions/<nome>/` |
| Foundation deps | `typescript-conventions`, `error-handling`, `logging` |
| Consumida por | `artifact/create-rag-endpoint`, `artifact/create-endpoint-doc` |

### `domain/rag-pipeline`

| Campo | Valor |
|---|---|
| Arquivo | `skills/domain/rag-pipeline.md` |
| Propósito | Sequência canônica das etapas de Retrieval-Augmented Generation neste projeto |
| Conteúdo | Fluxo: `extractor` → `chunker` → `embedder` → `indexer` para ingestão; `search` → `prompt-builder` → `completion` → `response-validator` para consulta. Tratamento de documentos contraditórios (prioridade pela data mais recente + nota de ambiguidade na resposta). Limite de contexto: máximo 3 chunks por consulta (ADR-0002) |
| Foundation deps | `typescript-conventions`, `logging`, `env-config` |
| Consumida por | `artifact/create-rag-endpoint`, `domain/azure-ai-search-integration` |

### `domain/testing-patterns`

| Campo | Valor |
|---|---|
| Arquivo | `skills/domain/testing-patterns.md` |
| Propósito | Estrutura e convenções de testes com `vitest` para todo o projeto |
| Conteúdo | Testes unitários em `src/**/*.test.ts` co-localizados com o módulo, testes de integração em `tests/integration/**/*.test.ts`, mocks somente para dependências externas (Azure AI Search, LLM), nunca mockar código interno do projeto, nomenclatura `describe('<módulo>') / it('deve <comportamento esperado>')`, asserções em português |
| Foundation deps | `typescript-conventions`, `error-handling` |
| Consumida por | `artifact/create-integration-test` |

### `domain/react-components`

| Campo | Valor |
|---|---|
| Arquivo | `skills/domain/react-components.md` |
| Propósito | Convenções de componentes React no painel web (`src/web/`) |
| Conteúdo | Componentes funcionais com TypeScript, props tipadas com `interface`, sem estado global (props drilling ou Context simples), um componente por arquivo, nomenclatura PascalCase para componentes e camelCase para hooks, sem CSS-in-JS (usar módulos CSS ou Tailwind) |
| Foundation deps | `typescript-conventions` |
| Consumida por | `artifact/create-react-card` |

### `domain/azure-ai-search-integration`

| Campo | Valor |
|---|---|
| Arquivo | `skills/domain/azure-ai-search-integration.md` |
| Propósito | Padrão de integração com o índice semântico (Azure AI Search em produção, filesystem MCP local em dev) |
| Conteúdo | Interface `SearchService` isolada no módulo `src/services/search.ts`, dependency injection no handler, mock local via `data/retrieval-corpus/`, retorno sempre como array tipado de chunks com `score` e `source`, fallback para array vazio em caso de timeout |
| Foundation deps | `typescript-conventions`, `error-handling`, `logging`, `env-config` |
| Consumida por | `artifact/create-rag-endpoint` |

---

## Artifact Skills

Skills de nível Artifact são **receitas completas** para gerar um tipo específico de artefato. Cada skill lista os inputs necessários, os arquivos que serão criados e o template passo-a-passo.

### `artifact/create-rag-endpoint`

| Campo | Valor |
|---|---|
| Arquivo | `skills/artifact/create-rag-endpoint.md` |
| Propósito | Criar um endpoint Azure Function com fluxo RAG completo |
| Inputs | Nome do endpoint (ex: `query`), schema de request/response, serviços de busca e LLM injetados |
| Outputs gerados | `src/functions/<nome>/handler.ts`, `src/functions/<nome>/response-builder.ts`, `src/functions/<nome>/validator.ts` |
| Passos | 1. Definir schema zod de entrada/saída, 2. Implementar handler com middleware padrão, 3. Chamar `SearchService` com query do usuário, 4. Montar prompt com `prompt-builder`, 5. Chamar `completion`, 6. Validar resposta com `response-validator`, 7. Retornar `HttpResponse` estruturada |
| Domain deps | `azure-functions-endpoint`, `rag-pipeline`, `azure-ai-search-integration` |
| Foundation deps | `typescript-conventions`, `error-handling`, `logging`, `env-config` |

### `artifact/create-integration-test`

| Campo | Valor |
|---|---|
| Arquivo | `skills/artifact/create-integration-test.md` |
| Propósito | Criar teste de integração para um endpoint existente |
| Inputs | Nome do endpoint, cenários de sucesso e falha mapeados pelo QA |
| Outputs gerados | `tests/integration/<nome>.test.ts` |
| Passos | 1. Importar handler do endpoint, 2. Criar `describe` com o nome do endpoint, 3. Para cada cenário: montar `HttpRequest` de teste, invocar handler, fazer asserções em status code e body, 4. Incluir cenário de falha (serviço de busca indisponível), 5. Incluir cenário de resposta ambígua (documentos contraditórios) |
| Domain deps | `testing-patterns` |
| Foundation deps | `typescript-conventions`, `error-handling` |

### `artifact/create-react-card`

| Campo | Valor |
|---|---|
| Arquivo | `skills/artifact/create-react-card.md` |
| Propósito | Criar componente de card React para o painel web (resposta do assistente ou formulário de feedback) |
| Inputs | Tipo do card (`response` ou `feedback`), props necessárias, eventos emitidos |
| Outputs gerados | `src/web/src/components/<NomeCard>.tsx`, `src/web/src/components/<NomeCard>.module.css` |
| Passos | 1. Definir interface de props com TypeScript, 2. Implementar componente funcional, 3. Renderizar conteúdo com dados das props, 4. Emitir callbacks para ações do usuário (ex: `onFeedbackSubmit`), 5. Aplicar estilos via CSS module |
| Domain deps | `react-components` |
| Foundation deps | `typescript-conventions` |

### `artifact/create-endpoint-doc`

| Campo | Valor |
|---|---|
| Arquivo | `skills/artifact/create-endpoint-doc.md` |
| Propósito | Criar documentação técnica de um endpoint (README do módulo) |
| Inputs | Nome do endpoint, schema de request/response, comportamentos de erro, dependências externas |
| Outputs gerados | `src/functions/<nome>/README.md` |
| Passos | 1. Descrever propósito em 2 frases, 2. Documentar schema de entrada com exemplos, 3. Documentar schema de saída com exemplos, 4. Listar códigos de erro possíveis, 5. Descrever dependências (serviços, envs necessárias), 6. Incluir exemplo de chamada `curl` |
| Domain deps | `azure-functions-endpoint` |
| Foundation deps | `project-structure` |

### `artifact/create-product-spec`

| Campo | Valor |
|---|---|
| Arquivo | `skills/artifact/create-product-spec.md` |
| Propósito | Criar spec de produto para uma nova feature seguindo o template SDD do projeto |
| Inputs | Nome da feature, problema que resolve, requisitos funcionais e não-funcionais, critérios de aceite |
| Outputs gerados | `specs/<feature>/requirements.md`, `specs/<feature>/plan.md`, `specs/<feature>/tasks.md` |
| Passos | 1. Preencher `requirements.md` com contexto, problema, requisitos e critérios de aceite, 2. Descrever abordagem técnica em `plan.md` referenciando ADRs relevantes, 3. Decompor em tasks atômicas em `tasks.md` com estimativa e dependências |
| Domain deps | *(nenhum — é cross-cutting)* |
| Foundation deps | `project-structure` |

---

## Mapa de dependências

```
artifact/create-rag-endpoint
  ├── domain/azure-functions-endpoint
  │     └── foundation/error-handling
  │     └── foundation/logging
  │     └── foundation/typescript-conventions
  ├── domain/rag-pipeline
  │     └── foundation/logging
  │     └── foundation/env-config
  │     └── foundation/typescript-conventions
  └── domain/azure-ai-search-integration
        └── foundation/error-handling
        └── foundation/logging
        └── foundation/env-config
        └── foundation/typescript-conventions

artifact/create-integration-test
  └── domain/testing-patterns
        └── foundation/typescript-conventions
        └── foundation/error-handling

artifact/create-react-card
  └── domain/react-components
        └── foundation/typescript-conventions

artifact/create-endpoint-doc
  └── domain/azure-functions-endpoint
        └── (ver acima)
  └── foundation/project-structure

artifact/create-product-spec
  └── foundation/project-structure
```

---

## Localização dos arquivos de skill

```
novatech-assistant/
└── skills/
    ├── foundation/
    │   ├── typescript-conventions.md
    │   ├── error-handling.md
    │   ├── logging.md
    │   ├── env-config.md
    │   └── project-structure.md
    ├── domain/
    │   ├── azure-functions-endpoint.md
    │   ├── rag-pipeline.md
    │   ├── testing-patterns.md
    │   ├── react-components.md
    │   └── azure-ai-search-integration.md
    └── artifact/
        ├── create-rag-endpoint.md
        ├── create-integration-test.md
        ├── create-react-card.md
        ├── create-endpoint-doc.md
        └── create-product-spec.md
```

---

## Critério de uso

| Situação | Skill a aplicar |
|---|---|
| Criar qualquer arquivo `.ts` | Verificar `foundation/typescript-conventions` |
| Novo endpoint Azure Function | `artifact/create-rag-endpoint` (RAG) ou `domain/azure-functions-endpoint` (endpoint simples) |
| Testar endpoint existente | `artifact/create-integration-test` |
| Novo card no painel web | `artifact/create-react-card` |
| Documentar endpoint | `artifact/create-endpoint-doc` |
| Especificar nova feature | `artifact/create-product-spec` |
| Integrar com índice de busca | `domain/azure-ai-search-integration` |
