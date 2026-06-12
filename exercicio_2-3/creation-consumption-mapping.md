# Creation & Consumption Mapping — Skills NovaTech Assistant

> Para cada skill: nome, frase-ativação que um agente reconheceria, papel que cria, papel + agentes que consomem, e frequência estimada de uso.
> Escala de frequência: **Implícita** (toda geração de código) · **Alta** (múltiplas vezes por sprint) · **Média** (algumas vezes por sprint) · **Baixa** (algumas vezes por release).

---

## Foundation Skills

### `foundation/typescript-conventions`

| Campo | Detalhe |
|---|---|
| **Nome** | TypeScript Conventions |
| **Frase-ativação** | "Crie um módulo TypeScript" · "Adicione tipagem a este serviço" · "Como exportar este tipo no projeto" |
| **Quem cria** | **Tech Lead** — define no início do projeto, atualiza quando surgem novos padrões de tipagem |
| **Quem consome (papel)** | Dev Backend, Dev Frontend, QA (ao escrever helpers de teste) |
| **Quem consome (agente)** | **Claude Code** — lida implicitamente antes de qualquer geração de arquivo `.ts`; **Copilot** — aplicada em autocomplete de código TypeScript |
| **Frequência** | **Implícita** — pré-condição silenciosa de toda geração de código; não é invocada explicitamente, mas é a mais consultada de todas |

---

### `foundation/error-handling`

| Campo | Detalhe |
|---|---|
| **Nome** | Error Handling |
| **Frase-ativação** | "Como tratar erros neste endpoint" · "O que retornar quando a busca falhar" · "Padronizar resposta de erro" |
| **Quem cria** | **Tech Lead** — define a classe `AppError` e o mapeamento HTTP; revisada junto com QA nos cenários de falha |
| **Quem consome (papel)** | Dev Backend (ao implementar handlers e serviços); QA (ao escrever testes de cenários de falha) |
| **Quem consome (agente)** | **Claude Code** — consultada ao gerar qualquer `handler.ts`, bloco `try/catch` ou resposta HTTP com status != 200; **Copilot** — autocomplete em blocos de tratamento de exceção |
| **Frequência** | **Alta** — toda vez que um endpoint ou serviço com chamada externa é criado (estimado: 6–8 vezes no projeto) |

---

### `foundation/logging`

| Campo | Detalhe |
|---|---|
| **Nome** | Logging |
| **Frase-ativação** | "Adicione logs neste serviço" · "Instrumentar esta operação com pino" · "Como registrar a duração da chamada ao LLM" |
| **Quem cria** | **Tech Lead** — define a instância singleton, os campos obrigatórios e os níveis de severidade |
| **Quem consome (papel)** | Dev Backend (ao implementar endpoints e serviços do pipeline); QA (ao verificar evidências de log nos testes) |
| **Quem consome (agente)** | **Claude Code** — consultada ao gerar `handler.ts`, etapas do pipeline (`chunker`, `embedder`, `search`) e qualquer serviço que faça chamada externa; **Copilot** — autocomplete de chamadas ao logger |
| **Frequência** | **Alta** — presente em todo módulo de código de produção (estimado: 8–10 vezes no projeto) |

---

### `foundation/env-config`

| Campo | Detalhe |
|---|---|
| **Nome** | Environment Configuration |
| **Frase-ativação** | "Este serviço precisa de uma variável de ambiente" · "Como acessar a chave do Azure AI" · "Adicionar nova configuração de conexão" |
| **Quem cria** | **Tech Lead** — define o schema zod centralizado de envs no início do projeto; atualizada a cada nova integração |
| **Quem consome (papel)** | Dev Backend (ao criar novos serviços com dependências externas); Delivery Manager (ao provisionar ambientes) |
| **Quem consome (agente)** | **Claude Code** — consultada ao gerar serviços que acessam Azure AI Search, Azure OpenAI, ou qualquer credencial; garante que o acesso é feito via módulo de config e não via `process.env` direto |
| **Frequência** | **Média** — invocada ao adicionar nova integração ou credencial (estimado: 3–5 vezes no projeto) |

---

### `foundation/project-structure`

| Campo | Detalhe |
|---|---|
| **Nome** | Project Structure |
| **Frase-ativação** | "Onde criar este arquivo" · "Em qual pasta vai este módulo" · "Qual o caminho correto para esta spec" |
| **Quem cria** | **Tech Lead** — define o layout do repositório no início do projeto; atualizada apenas em decisões arquiteturais relevantes |
| **Quem consome (papel)** | Dev Backend, Dev Frontend, QA, Product Specialist (ao criar specs), Delivery Manager (ao referenciar artefatos) |
| **Quem consome (agente)** | **Claude Code** — consultada ao decidir o caminho de saída de qualquer artefato gerado; é a primeira skill aplicada em todo Artifact skill; **Copilot** — orienta estrutura de novos arquivos sugeridos |
| **Frequência** | **Alta** — invocada implicitamente por todos os Artifact skills (estimado: 10+ vezes no projeto) |

---

## Domain Skills

### `domain/azure-functions-endpoint`

| Campo | Detalhe |
|---|---|
| **Nome** | Azure Functions Endpoint |
| **Frase-ativação** | "Crie um novo endpoint HTTP" · "Adicionar uma rota para X" · "Como estruturar este Azure Function" |
| **Quem cria** | **Tech Lead** — define o contrato HTTP, o middleware de logging e o middleware de error handling como padrão da camada de functions |
| **Quem consome (papel)** | Dev Backend (ao implementar ou revisar qualquer handler); Tech Lead (ao fazer code review) |
| **Quem consome (agente)** | **Claude Code** — consumida diretamente por `artifact/create-rag-endpoint` e `artifact/create-endpoint-doc`; é o esqueleto base de todo handler gerado; **Copilot** — orienta autocomplete da assinatura do handler |
| **Frequência** | **Alta** — referenciada toda vez que um endpoint é criado ou revisado (estimado: 5–7 vezes no projeto, cobrindo query, feedback, health e futuros endpoints) |

---

### `domain/rag-pipeline`

| Campo | Detalhe |
|---|---|
| **Nome** | RAG Pipeline |
| **Frase-ativação** | "Implemente o fluxo RAG" · "Como a consulta recupera contexto" · "Adicionar etapa no pipeline de ingestão" · "Limite de chunks por consulta" |
| **Quem cria** | **Tech Lead** (decisões arquiteturais: ADR-0002, limite de 3 chunks, tratamento de contradições) em conjunto com **Dev Backend AI** (sequência técnica das etapas) |
| **Quem consome (papel)** | Dev Backend AI (ao implementar ou estender o pipeline); QA (ao mapear cenários de falha do RAG, ex: resposta ambígua); Product Specialist (ao entender o comportamento do assistente) |
| **Quem consome (agente)** | **Claude Code** — consultada ao gerar qualquer endpoint de consulta e ao modificar etapas do pipeline (`extractor`, `chunker`, `embedder`, `indexer`, `search`, `completion`); é a skill de maior profundidade técnica do projeto |
| **Frequência** | **Alta** — núcleo do produto; referenciada em toda feature que envolve consulta ou ingestão (estimado: 6–8 vezes no projeto) |

---

### `domain/testing-patterns`

| Campo | Detalhe |
|---|---|
| **Nome** | Testing Patterns |
| **Frase-ativação** | "Escreva testes para este módulo" · "Como mockar o serviço de busca nos testes" · "Adicionar cobertura para o cenário de falha" |
| **Quem cria** | **QA** (estratégia de mocks, cenários obrigatórios, nomenclatura) em revisão com **Tech Lead** (convenções de estrutura de arquivos) |
| **Quem consome (papel)** | Dev Backend (ao implementar testes junto com a feature); Dev Frontend (testes de componente); QA (ao especificar e validar os cenários) |
| **Quem consome (agente)** | **Claude Code** — consumida diretamente por `artifact/create-integration-test`; define o que pode e não pode ser mockado, guiando as decisões de geração dos testes |
| **Frequência** | **Alta** — um conjunto de testes por endpoint ou módulo relevante (estimado: 5–8 vezes no projeto) |

---

### `domain/react-components`

| Campo | Detalhe |
|---|---|
| **Nome** | React Components |
| **Frase-ativação** | "Crie um componente React" · "Adicionar elemento ao painel web" · "Como tipar as props deste card" |
| **Quem cria** | **Tech Lead** ou **Dev Frontend sênior** — define convenções de componentes funcionais, tipagem de props e estilo |
| **Quem consome (papel)** | Dev Frontend (ao implementar qualquer elemento do `src/web/`); QA (ao escrever testes de componente) |
| **Quem consome (agente)** | **Claude Code** — consumida por `artifact/create-react-card`; orienta a estrutura do componente, o tipo das props e a separação de estilos; **Copilot** — orienta autocomplete de JSX e hooks |
| **Frequência** | **Média** — escopo limitado ao painel web (estimado: 3–5 componentes no projeto: ResponseCard, FeedbackCard, e variantes) |

---

### `domain/azure-ai-search-integration`

| Campo | Detalhe |
|---|---|
| **Nome** | Azure AI Search Integration |
| **Frase-ativação** | "Integrar com o índice de busca semântica" · "Recuperar chunks relevantes para a query" · "Mockar o SearchService localmente" |
| **Quem cria** | **Tech Lead** (decisão de isolar via interface e dependency injection) em conjunto com **Dev Backend AI** (implementação do mock local e fallback) |
| **Quem consome (papel)** | Dev Backend AI (ao implementar endpoints de consulta); QA (ao escrever testes que precisam mockar o `SearchService`) |
| **Quem consome (agente)** | **Claude Code** — consultada ao gerar qualquer endpoint que precise de retrieval; define como injetar o `SearchService`, o schema de retorno e o comportamento de fallback |
| **Frequência** | **Alta** — presente em todo endpoint de consulta RAG (estimado: 4–6 vezes no projeto) |

---

## Artifact Skills

### `artifact/create-rag-endpoint`

| Campo | Detalhe |
|---|---|
| **Nome** | Create RAG Endpoint |
| **Frase-ativação** | "Crie um endpoint RAG para X" · "Novo endpoint de consulta com recuperação de contexto" · "Implementar o fluxo completo de query para esta feature" |
| **Quem cria** | **Dev Backend AI** — executa a receita com o suporte direto do Claude Code; o Tech Lead revisa o artefato gerado |
| **Quem consome (papel)** | Dev Backend AI (invoca a skill e revisa o output); Tech Lead (revisão e aprovação); QA (base para criar os testes de integração) |
| **Quem consome (agente)** | **Claude Code** — principal executor da receita; scaffolda `handler.ts`, `response-builder.ts` e `validator.ts` em uma única invocação orquestrada |
| **Frequência** | **Alta** — a skill Artifact mais usada no projeto; um endpoint RAG por feature de consulta (estimado: 3–5 endpoints ao longo do projeto: `query`, `feedback`, e futuros) |

---

### `artifact/create-integration-test`

| Campo | Detalhe |
|---|---|
| **Nome** | Create Integration Test |
| **Frase-ativação** | "Escreva testes de integração para o endpoint X" · "Adicione teste cobrindo o cenário de busca indisponível" · "Gere o arquivo de teste de integração para este handler" |
| **Quem cria** | **QA** — especifica os cenários; **Claude Code** gera o scaffold; Dev Backend valida e ajusta |
| **Quem consome (papel)** | QA (especifica e valida); Dev Backend (ajusta e mantém); Tech Lead (revisa cobertura nos code reviews) |
| **Quem consome (agente)** | **Claude Code** — gera o arquivo `tests/integration/<nome>.test.ts` completo a partir dos cenários fornecidos pelo QA; inclui cenários de documentos contraditórios conforme a `domain/testing-patterns` |
| **Frequência** | **Alta** — um arquivo de teste por endpoint criado (estimado: 1:1 com `create-rag-endpoint`, ou seja, 3–5 vezes no projeto) |

---

### `artifact/create-react-card`

| Campo | Detalhe |
|---|---|
| **Nome** | Create React Card |
| **Frase-ativação** | "Crie um card de resposta no painel web" · "Novo componente de feedback para o usuário" · "Adicionar card React para exibir X" |
| **Quem cria** | **Dev Frontend** — invoca com tipo do card e props; **Claude Code** gera o componente e o CSS module |
| **Quem consome (papel)** | Dev Frontend (invoca e revisa); Product Specialist (valida se o card atende ao requisito de UX); QA (testa o comportamento visual e os callbacks) |
| **Quem consome (agente)** | **Claude Code** — gera `<NomeCard>.tsx` e `<NomeCard>.module.css` seguindo `domain/react-components`; **Copilot** — pode sugerir variações do JSX durante a revisão |
| **Frequência** | **Média** — escopo limitado ao painel web e ao Teams bot (estimado: 3–4 cards no projeto: ResponseCard, FeedbackCard, e variantes de estado) |

---

### `artifact/create-endpoint-doc`

| Campo | Detalhe |
|---|---|
| **Nome** | Create Endpoint Documentation |
| **Frase-ativação** | "Documente o endpoint X" · "Gere o README técnico deste módulo" · "Adicionar documentação com exemplo de curl" |
| **Quem cria** | **Dev Backend** (após implementar o endpoint) ou **Tech Lead** (em endpoints críticos); **Claude Code** gera o rascunho |
| **Quem consome (papel)** | Dev Backend (revisão e manutenção); Product Specialist (consulta para entender o contrato); Delivery Manager (referência em demos e handoffs) |
| **Quem consome (agente)** | **Claude Code** — gera `src/functions/<nome>/README.md` com schema de entrada/saída, códigos de erro e exemplo de chamada; usado também por outros agentes que precisam entender um endpoint antes de gerar testes ou integrações |
| **Frequência** | **Média** — um README por endpoint (estimado: 3–5 documentações no projeto, geradas após cada implementação de endpoint) |

---

### `artifact/create-product-spec`

| Campo | Detalhe |
|---|---|
| **Nome** | Create Product Spec |
| **Frase-ativação** | "Especifique a feature X" · "Crie o SDD para este requisito" · "Gere requirements, plan e tasks para esta demanda" |
| **Quem cria** | **Product Specialist** — fornece o problema, os requisitos e os critérios de aceite; **Claude Code** estrutura nos três arquivos do template |
| **Quem consome (papel)** | Product Specialist (revisa e assina); Dev Backend/Frontend (referência durante implementação); QA (extrai cenários de teste a partir dos critérios de aceite); Delivery Manager (extrai tasks e estimativas para o planejamento) |
| **Quem consome (agente)** | **Claude Code** — gera `specs/<feature>/requirements.md`, `plan.md` e `tasks.md` em uma única execução; o `plan.md` gerado referencia ADRs existentes, fazendo a skill consumir indiretamente o contexto do `docs/adr/` |
| **Frequência** | **Média** — uma spec por feature no início do ciclo de desenvolvimento (estimado: 4–6 specs no projeto: pipeline-ingestão, query-endpoint, feedback-api, teams-bot, painel-web, e possíveis features futuras) |

---

## Tabela-resumo

| Skill | Nível | Cria | Consome (papel) | Agentes | Frequência |
|---|---|---|---|---|---|
| `typescript-conventions` | Foundation | Tech Lead | Dev Backend, Dev Frontend, QA | Claude Code, Copilot | Implícita |
| `error-handling` | Foundation | Tech Lead | Dev Backend, QA | Claude Code, Copilot | Alta |
| `logging` | Foundation | Tech Lead | Dev Backend, QA | Claude Code, Copilot | Alta |
| `env-config` | Foundation | Tech Lead | Dev Backend, Delivery Manager | Claude Code | Média |
| `project-structure` | Foundation | Tech Lead | Todos os papéis | Claude Code, Copilot | Alta |
| `azure-functions-endpoint` | Domain | Tech Lead | Dev Backend, Tech Lead | Claude Code, Copilot | Alta |
| `rag-pipeline` | Domain | Tech Lead + Dev Backend AI | Dev Backend AI, QA, Product Specialist | Claude Code | Alta |
| `testing-patterns` | Domain | QA + Tech Lead | Dev Backend, Dev Frontend, QA | Claude Code | Alta |
| `react-components` | Domain | Tech Lead / Dev Frontend | Dev Frontend, QA | Claude Code, Copilot | Média |
| `azure-ai-search-integration` | Domain | Tech Lead + Dev Backend AI | Dev Backend AI, QA | Claude Code | Alta |
| `create-rag-endpoint` | Artifact | Dev Backend AI + Claude Code | Dev Backend AI, Tech Lead, QA | Claude Code | Alta |
| `create-integration-test` | Artifact | QA + Claude Code | QA, Dev Backend, Tech Lead | Claude Code | Alta |
| `create-react-card` | Artifact | Dev Frontend + Claude Code | Dev Frontend, Product Specialist, QA | Claude Code, Copilot | Média |
| `create-endpoint-doc` | Artifact | Dev Backend + Claude Code | Dev Backend, Product Specialist, Delivery Manager | Claude Code | Média |
| `create-product-spec` | Artifact | Product Specialist + Claude Code | Product Specialist, Dev, QA, Delivery Manager | Claude Code | Média |

---

## Padrões observados

**Skills Foundation são criadas por um papel, consumidas por todos.**
O Tech Lead concentra a autoria de todas as 5 Foundation skills. Isso é intencional: convenções globais precisam de uma fonte única de verdade. A consequência é que mudanças nelas têm impacto em cascata em toda a hierarquia.

**Skills Domain são criadas por papel + domínio, consumidas por papel adjacente.**
`rag-pipeline` e `azure-ai-search-integration` exigem co-autoria de Tech Lead e Dev AI porque combinam decisão arquitetural com conhecimento técnico de implementação. Skills como `testing-patterns` exigem o QA como co-autor porque os cenários de teste são conhecimento de domínio do QA, não só do Tech Lead.

**Skills Artifact têm Claude Code como co-criador.**
Todo Artifact skill é executado em colaboração humano + Claude Code: o humano fornece os inputs (nome, cenários, tipo), o Claude Code gera o scaffold. Isso reflete o modelo de uso real do projeto.

**Claude Code é o consumidor universal de todas as skills.**
Diferente dos papéis humanos (que consomem apenas as skills relevantes ao seu domínio), o Claude Code potencialmente aplica qualquer skill ao gerar código, documentação ou testes. Por isso as Foundation skills precisam estar sempre carregadas no contexto do agente (via `AGENTS.md`).
