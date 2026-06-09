# MCP Servers Mapping — NovaTech Assistant

## Visão Geral

O projeto NovaTech requer 6 MCP servers para cobrir todo o fluxo de desenvolvimento e operação do assistente RAG. Dois já existem como servidores públicos prontos para uso; quatro precisam ser configurados com atenção a credenciais e permissões; um precisará ser construído internamente.

### Tabela Resumo

| #   | Server            | Disponibilidade                                     | Consome API              | Papéis que Consomem           |
| --- | ----------------- | --------------------------------------------------- | ------------------------ | ----------------------------- |
| 1   | `github`          | Público (`@modelcontextprotocol/server-github`)     | GitHub REST API          | Dev, Tech Lead, QA            |
| 2   | `filesystem`      | Público (`@modelcontextprotocol/server-filesystem`) | Local (sem API)          | Todos                         |
| 3   | `azure-ai-search` | Build interno                                       | Azure AI Search REST API | Pipeline Agent, Query Agent   |
| 4   | `azure-openai`    | Build interno                                       | Azure OpenAI REST API    | Pipeline Agent, Eval Agent    |
| 5   | `azure-devops`    | Comunidade (`@microsoft/mcp-server-azure-devops`)   | Azure DevOps REST API    | Tech Lead, Product Specialist |
| 6   | `confluence`      | Comunidade (`@mcp-server/confluence`)               | Confluence REST API      | Todos (read-only)             |

---

## 1. GitHub MCP Server

**Pacote:** `@modelcontextprotocol/server-github`  
**Disponibilidade:** Público, mantido pela Anthropic  
**Repositório alvo:** `db1/novatech-assistant`

### O que expõe

**Tools (ações)**
| Tool | Descrição |
|------|-----------|
| `get_file_contents` | Lê arquivo ou diretório do repositório |
| `search_code` | Busca código por padrão (regex, literal) |
| `create_or_update_file` | Cria ou atualiza arquivo via commit |
| `create_pull_request` | Abre PR com título, body e base branch |
| `create_issue` | Registra issue com labels e assignee |
| `list_issues` | Lista issues com filtros (label, assignee, state) |
| `add_issue_comment` | Adiciona comentário em issue ou PR |
| `get_pull_request` | Detalhe de PR (diff, status de checks) |
| `merge_pull_request` | Merge de PR aprovado |
| `list_commits` | Histórico de commits de um branch ou arquivo |

**Resources (dados read-only)**
| Resource URI | Descrição |
|-------------|-----------|
| `github://db1/novatech-assistant/blob/{branch}/{path}` | Conteúdo de arquivo em branch específico |
| `github://db1/novatech-assistant/tree/{branch}` | Árvore de diretórios |
| `github://db1/novatech-assistant/pulls?state=open` | PRs abertas |
| `github://db1/novatech-assistant/issues?state=open` | Issues abertas |

**Prompts**

- Nenhum prompt nativo — o `@modelcontextprotocol/server-github` não expõe prompts. Templates de PR/issue devem viver em `/prompts/` do repositório.

### Quem consome

| Papel / Agente  | Uso principal                                          |
| --------------- | ------------------------------------------------------ |
| Dev Agent       | Ler código existente, criar PR, buscar padrões no repo |
| Tech Lead Agent | Revisar PRs, validar specs, consultar ADRs             |
| QA Agent        | Ler tests/, criar issues de bug, rastrear regressões   |
| Pipeline Agent  | Ler arquivos de spec e skills para contexto de geração |

### Permissões mínimas (least privilege)

Escopo do GitHub Personal Access Token (PAT) ou GitHub App:

| Permissão       | Nível        | Justificativa                                   |
| --------------- | ------------ | ----------------------------------------------- |
| `contents`      | Read + Write | Leitura de arquivos e criação de commits        |
| `pull_requests` | Read + Write | Criar e mergear PRs                             |
| `issues`        | Read + Write | Criar e comentar issues                         |
| `metadata`      | Read         | Obrigatório para GitHub Apps                    |
| `checks`        | Read         | Consultar status de CI                          |
| `actions`       | **Negado**   | Não é necessário disparar workflows manualmente |
| `admin`         | **Negado**   | Zero acesso a configurações de repositório      |
| `secrets`       | **Negado**   | Agentes não devem tocar em segredos             |

> **Recomendação:** usar GitHub App com permissões por repositório, não PAT de usuário. O token deve ser rotacionado via Azure Key Vault.

---

## 2. Filesystem MCP Server

**Pacote:** `@modelcontextprotocol/server-filesystem`  
**Disponibilidade:** Público, mantido pela Anthropic  
**Escopo:** Diretórios específicos do repositório clonado localmente

### O que expõe

**Tools (ações)**
| Tool | Descrição |
|------|-----------|
| `read_file` | Lê conteúdo de arquivo local |
| `read_multiple_files` | Lê múltiplos arquivos em batch |
| `write_file` | Escreve/sobrescreve arquivo |
| `create_directory` | Cria diretório |
| `list_directory` | Lista arquivos em diretório |
| `move_file` | Move ou renomeia arquivo |
| `search_files` | Busca arquivos por padrão glob |
| `get_file_info` | Metadados (tamanho, data de modificação) |

**Resources**

- Todos os arquivos dentro dos caminhos autorizados são expostos como resources com URI `file://{absolute_path}`.

**Prompts**

- Nenhum nativo.

### Quem consome

| Papel / Agente           | Diretórios necessários                         |
| ------------------------ | ---------------------------------------------- |
| Dev Agent                | `./src`, `./tests`, `./specs`                  |
| Tech Lead Agent          | `./specs`, `./docs`, `./skills`, `./AGENTS.md` |
| Product Specialist Agent | `./specs`, `./prompts`                         |
| Pipeline Agent           | `./src/pipeline`, `./specs/pipeline-ingestao`  |
| Eval Agent               | `./prompts/eval`                               |

### Permissões mínimas (least privilege)

O servidor aceita uma lista de caminhos raiz autorizados no momento da inicialização. Fora desses caminhos, nenhuma operação é permitida.

```
Autorizado:   ./src, ./specs, ./skills, ./docs, ./prompts, ./tests
Bloqueado:    ./.github (workflows de CI), ./infra (Bicep com configs de infra)
Bloqueado:    ../ (qualquer path fora do repositório)
```

> **Atenção:** o diretório `./infra/` contém parâmetros de ambiente (`dev.bicepparam`, `prod.bicepparam`). Expô-lo aumenta o risco de vazamento de nomes de recursos Azure. Manter bloqueado até necessidade explícita.

---

## 3. Azure AI Search MCP Server

**Disponibilidade:** **Construir internamente**  
**Motivo:** Não existe servidor MCP público oficial para Azure AI Search. O servidor da Microsoft cobre Azure Cognitive Services genérico, sem suporte a Vector Search e Hybrid Search que o projeto requer.

### O que expõe

**Tools (ações)**
| Tool | Descrição |
|------|-----------|
| `search_documents` | Busca vetorial/híbrida por query + embedding |
| `get_document` | Recupera documento por ID |
| `index_document` | Insere ou atualiza documento no índice |
| `delete_document` | Remove documento por ID do índice |
| `list_indexes` | Lista índices disponíveis |
| `get_index_stats` | Estatísticas do índice (contagem, tamanho) |

**Resources**
| Resource URI | Descrição |
|-------------|-----------|
| `azure-search://indexes` | Lista de índices ativos |
| `azure-search://indexes/{name}/schema` | Schema do índice (campos, tipos) |
| `azure-search://indexes/{name}/stats` | Estatísticas do índice |

**Prompts**

- `search-with-filter`: Template para busca com filtro por `source_type` e `date_range`.
- `hybrid-search`: Template combinando busca vetorial + keyword com parâmetros `alpha` (peso semântico).

### Quem consome

| Papel / Agente           | Tools utilizadas                      | Tipo de acesso              |
| ------------------------ | ------------------------------------- | --------------------------- |
| Pipeline Agent           | `index_document`, `delete_document`   | Read + Write                |
| Query Agent (handler.ts) | `search_documents`, `get_document`    | Read-only                   |
| Eval Agent               | `search_documents`, `get_index_stats` | Read-only                   |
| Tech Lead Agent          | `list_indexes`, `get_index_stats`     | Read-only (observabilidade) |

### Permissões mínimas (least privilege)

Duas identidades gerenciadas distintas (Azure Managed Identity):

| Identidade          | Role Azure AI Search            | Escopo                        |
| ------------------- | ------------------------------- | ----------------------------- |
| `mi-pipeline-agent` | `Search Index Data Contributor` | Apenas índice `novatech-docs` |
| `mi-query-agent`    | `Search Index Data Reader`      | Apenas índice `novatech-docs` |
| `mi-eval-agent`     | `Search Index Data Reader`      | Apenas índice `novatech-docs` |

> **Nunca** usar a `Admin API Key` no servidor MCP. Usar sempre chaves de query ou Managed Identity.

---

## 4. Azure OpenAI MCP Server

**Disponibilidade:** **Construir internamente**  
**Motivo:** O objetivo principal é geração de embeddings para o pipeline de ingestão e execução de avaliações de prompt — fluxos que o servidor OpenAI público não cobre com o grau de controle necessário (deployment name, api-version, endpoint customizado).

### O que expõe

**Tools (ações)**
| Tool | Descrição |
|------|-----------|
| `generate_completion` | Gera resposta dado um prompt (chat completions) |
| `generate_embeddings` | Gera embedding vetorial de um texto |
| `count_tokens` | Conta tokens de um texto sem fazer inferência |
| `list_deployments` | Lista deployments disponíveis no endpoint |

**Resources**
| Resource URI | Descrição |
|-------------|-----------|
| `azure-openai://deployments` | Lista de modelos deployados |
| `azure-openai://deployments/{name}/info` | Informações do deployment (modelo, versão, limites) |

**Prompts**

- `rag-completion`: Template padrão do projeto para RAG — injeta `{system_prompt}`, `{chunks}` e `{user_query}`.
- `eval-judge`: Template para avaliação de resposta — modelo atua como juiz comparando resposta gerada vs. golden answer.

### Quem consome

| Papel / Agente  | Tools utilizadas                      | Deployment necessário                       |
| --------------- | ------------------------------------- | ------------------------------------------- |
| Pipeline Agent  | `generate_embeddings`                 | `text-embedding-ada-002`                    |
| Query Agent     | `generate_completion`                 | `gpt-4o`                                    |
| Eval Agent      | `generate_completion`, `count_tokens` | `gpt-4o` (juiz), `gpt-4o-mini` (referência) |
| Prompt Engineer | `generate_completion`, `count_tokens` | Qualquer deployment                         |

### Permissões mínimas (least privilege)

| Identidade          | Role Azure OpenAI         | Deployments acessíveis          |
| ------------------- | ------------------------- | ------------------------------- |
| `mi-pipeline-agent` | `Cognitive Services User` | Apenas `text-embedding-ada-002` |
| `mi-query-agent`    | `Cognitive Services User` | Apenas `gpt-4o`                 |
| `mi-eval-agent`     | `Cognitive Services User` | `gpt-4o`, `gpt-4o-mini`         |

> **Rate limiting:** o servidor deve implementar retry com exponential backoff e expor o header `Retry-After` como metadado de erro para que agentes possam aguardar sem loop infinito.

---

## 5. Azure DevOps MCP Server

**Pacote:** `@microsoft/mcp-server-azure-devops` (comunidade/Microsoft, validar versão estável)  
**Disponibilidade:** Servidor de comunidade — avaliar antes de adotar em produção  
**Alternativa:** Construir wrapper mínimo sobre a API REST do ADO se o pacote não atender.

### O que expõe

**Tools (ações)**
| Tool | Descrição |
|------|-----------|
| `list_work_items` | Lista work items com filtros (sprint, assignee, type) |
| `get_work_item` | Detalhe de work item por ID |
| `create_work_item` | Cria task, bug ou user story |
| `update_work_item` | Atualiza estado, assignee ou campos customizados |
| `add_comment` | Adiciona comentário a um work item |
| `list_sprints` | Lista sprints do board |
| `get_sprint` | Detalhe de sprint (capacity, work items) |

**Resources**
| Resource URI | Descrição |
|-------------|-----------|
| `devops://novatech/boards/current-sprint` | Work items da sprint ativa |
| `devops://novatech/boards/backlog` | Backlog priorizado |

**Prompts**

- `create-bug-from-test-failure`: Template para criar bug a partir de falha de teste (injeta stack trace e contexto do agente).
- `sprint-summary`: Template para resumo de sprint — lista work items por estado.

### Quem consome

| Papel / Agente           | Tools utilizadas                                    | Acesso              |
| ------------------------ | --------------------------------------------------- | ------------------- |
| Tech Lead Agent          | `list_work_items`, `get_sprint`, `update_work_item` | Read + Write        |
| Product Specialist Agent | `create_work_item`, `list_work_items`               | Read + Write        |
| QA Agent                 | `create_work_item` (bugs), `add_comment`            | Write (apenas bugs) |
| Dev Agent                | `get_work_item`, `list_work_items`                  | Read-only           |

### Permissões mínimas (least privilege)

PAT Azure DevOps com escopos mínimos:

| Escopo           | Nível        | Justificativa                     |
| ---------------- | ------------ | --------------------------------- |
| `vso.work_write` | Read + Write | Criar e atualizar work items      |
| `vso.work`       | Read         | Listar work items e sprints       |
| `vso.project`    | Read         | Acesso ao projeto `NovaTech`      |
| `vso.build`      | **Negado**   | Agentes não disparam builds       |
| `vso.release`    | **Negado**   | Agentes não gerenciam releases    |
| `vso.code`       | **Negado**   | Código fica no GitHub, não no ADO |

> O PAT deve ser scoped para a organização `db1` e projeto `NovaTech` apenas, nunca para toda a organização.

---

## 6. Confluence MCP Server

**Pacote:** `@mcp-server/confluence` (comunidade — avaliar alternativas como `@atlassian/mcp-confluence`)  
**Disponibilidade:** Servidor de comunidade  
**Acesso:** **Read-only** — documentação de negócio da NovaTech  
**Espaços relevantes:** `~NovaTech` (documentação de produto), `~Policies` (políticas e compliance)

### O que expõe

**Tools (ações — todas read-only)**
| Tool | Descrição |
|------|-----------|
| `search_pages` | Busca páginas por texto (CQL) |
| `get_page` | Retorna conteúdo de página por ID ou título |
| `get_page_children` | Lista sub-páginas de uma página |
| `list_spaces` | Lista espaços autorizados |
| `get_space` | Metadados de um espaço |

> **Nenhuma tool de escrita** deve ser exposta. O servidor deve ser configurado em modo read-only explícito.

**Resources**
| Resource URI | Descrição |
|-------------|-----------|
| `confluence://spaces/NovaTech/pages` | Todas as páginas do espaço NovaTech |
| `confluence://spaces/Policies/pages` | Políticas e compliance |
| `confluence://pages/{id}` | Página específica por ID |

**Prompts**

- `find-policy`: Template para buscar política por tema (injeta `{topic}` na query CQL).
- `summarize-spec`: Template para resumir especificação de produto encontrada no Confluence.

### Quem consome

| Papel / Agente           | Uso principal                                   |
| ------------------------ | ----------------------------------------------- |
| Todos os agentes         | Consultar definições de negócio e políticas     |
| Product Specialist Agent | Validar requisitos contra documentação NovaTech |
| QA Agent                 | Consultar critérios de aceite documentados      |
| Pipeline Agent           | Verificar categorias de documentos a ingerir    |

### Permissões mínimas (least privilege)

Token de API Confluence (Atlassian API Token):

| Permissão            | Configuração                                                  |
| -------------------- | ------------------------------------------------------------- |
| Tipo de acesso       | Read-only (somente leitura)                                   |
| Espaços autorizados  | `NovaTech`, `Policies` (whitelist explícita)                  |
| Espaços bloqueados   | `HR`, `Finance`, `Executive`, todos os pessoais (`~username`) |
| Operações de escrita | **Completamente bloqueadas** no servidor                      |

> Usar um service account Confluence dedicado (`svc-novatech-ai@empresa.com`), não a conta pessoal de um desenvolvedor. Isso garante que o token possa ser revogado sem impactar o usuário.

> **Variáveis de ambiente:** nenhuma credencial deve estar hard-coded no `mcp.json`. Todas as variáveis `${...}` devem ser providas via Azure Key Vault referenciadas em `.env.local` (git-ignored) ou via secrets do ambiente de CI/CD.

---

## Servidores Internos a Construir

### Prioridade e esforço estimado

| Server            | Prioridade                              | Esforço  | Responsável sugerido |
| ----------------- | --------------------------------------- | -------- | -------------------- |
| `azure-ai-search` | Alta — bloqueante para pipeline         | 3–5 dias | Dev Sênior + Eng. IA |
| `azure-openai`    | Alta — bloqueante para pipeline e evals | 2–3 dias | Dev Sênior           |

### Estrutura sugerida para servers internos

```
tools/
└── mcp-servers/
    ├── azure-ai-search/
    │   ├── src/
    │   │   ├── index.ts          # Entrypoint (stdio transport)
    │   │   ├── tools.ts          # Definições das tools
    │   │   ├── resources.ts      # Definições dos resources
    │   │   └── client.ts         # Wrapper do SDK @azure/search-documents
    │   ├── package.json
    │   └── tsconfig.json
    └── azure-openai/
        ├── src/
        │   ├── index.ts
        │   ├── tools.ts
        │   ├── prompts.ts        # Templates RAG e eval
        │   └── client.ts         # Wrapper do SDK @azure/openai
        ├── package.json
        └── tsconfig.json
```

---

## Matriz de Permissões por Papel

| MCP Server        |      Dev Agent      |      Tech Lead       | Product Specialist |  QA Agent   |   Pipeline Agent   |     Eval Agent     |
| ----------------- | :-----------------: | :------------------: | :----------------: | :---------: | :----------------: | :----------------: |
| `github`          |         R+W         |         R+W          |         R          |     R+W     |         R          |         R          |
| `filesystem`      | R+W (`src`,`tests`) | R+W (`specs`,`docs`) |   R+W (`specs`)    | R (`tests`) | R (`src/pipeline`) | R (`prompts/eval`) |
| `azure-ai-search` |          —          |      R (stats)       |         —          |      —      |        R+W         |         R          |
| `azure-openai`    |          —          |          —           |         —          |      —      |   R (embeddings)   |        R+W         |
| `azure-devops`    |          R          |         R+W          |        R+W         |  W (bugs)   |         —          |         —          |
| `confluence`      |          R          |          R           |         R          |      R      |         R          |         —          |

**Legenda:** R = Read, W = Write, R+W = Read + Write, — = sem acesso

---

## Decisões e Justificativas

### Por que não usar um único server genérico para Azure?

O SDK do Azure é amplo demais. Um server genérico exporia recursos desnecessários (Storage, Key Vault, AKS) violando o princípio de least privilege e aumentando a superfície de ataque. Servers específicos por serviço permitem escopos de credencial mínimos.

### Por que o `azure-ai-search` precisa ser construído?

O Azure AI Search usa uma API REST proprietária com suporte a Vector Search (HNSW), Hybrid Search (RRF) e Semantic Ranker. Nenhum servidor MCP público implementa esses recursos com parâmetros configuráveis (`k`, `select`, `filter`, `semanticConfiguration`). Construir internamente garante suporte completo ao modelo de busca do projeto.

### Por que separar embeddings (OpenAI MCP) do query endpoint?

O query endpoint (`src/functions/query/handler.ts`) usa o SDK diretamente via `src/services/completion.ts`. O MCP server de OpenAI é destinado a agentes auxiliares (Pipeline Agent para geração de embeddings, Eval Agent para avaliação de respostas). Misturar os dois criaria acoplamento desnecessário e dificultaria o controle de rate limits por papel.

### Por que Confluence é read-only e não tem tool de escrita?

O Confluence da NovaTech é a fonte de verdade da documentação de negócio. Permitir que agentes de IA escrevam nele sem aprovação humana criaria risco de contaminação da documentação oficial. Toda geração de conteúdo deve passar por revisão humana antes de ser publicada no Confluence.
