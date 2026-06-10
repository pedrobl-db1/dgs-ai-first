# MCP Servers — Mapeamento de Necessidades do Projeto NovaTech

## 1. Visão Geral

O Model Context Protocol (MCP) padroniza como o modelo de IA se conecta a ferramentas externas. Cada server expõe três primitivas:

| Primitiva | Descrição | Exemplo neste projeto |
|-----------|-----------|----------------------|
| **Tools** | Ações que o modelo pode invocar (efeitos colaterais possíveis) | `write_file`, `git_log` |
| **Resources** | Dados que o modelo pode ler (sem efeito colateral) | conteúdo de `docs/novatech/` |
| **Prompts** | Templates reutilizáveis para contextualizar tarefas | templates de revisão de ADR |

---

## 2. Mapeamento: Necessidade → Server

### 2.1 `filesystem` — Código, specs e skills (leitura/escrita)

**Necessidade:** O assistente precisa ler e editar código-fonte, specs SDD e skills do projeto.

| Item | Detalhe |
|------|---------|
| **Server** | `@modelcontextprotocol/server-filesystem` |
| **Pastas incluídas** | `./src`, `./specs`, `./skills`, `./prompts`, `./tests`, `./infra` |
| **Modo** | Leitura **e** escrita |
| **Quem consome** | Dev (geração de código, tasks), Tech Lead (revisão de specs), QA (geração de testes) |
| **Tools expostos** | `read_file`, `write_file`, `create_directory`, `list_directory`, `move_file`, `search_files` |
| **Resources expostos** | Listagem de arquivos nas pastas configuradas |

**Justificativa de least privilege:** Apenas as pastas de artefatos editáveis pelo time são incluídas. `docs/novatech/` e `data/retrieval-corpus/` são intencionalmente excluídas desta instância porque são fontes de leitura somente (ver instâncias 2.2 e 2.3). `AGENTS.md` e `README.md` na raiz ficam acessíveis indiretamente via `./src` não — eles são cobertos adicionando a raiz do repositório quando necessário, mas o escopo padrão mantém o foco em artefatos de desenvolvimento.

---

### 2.2 `filesystem-docs` — Documentação de negócio da NovaTech (somente leitura)

**Necessidade:** O assistente precisa consultar políticas, SLAs, FAQs e procedimentos da NovaTech para gerar respostas contextualizadas. Esses documentos não devem ser modificados.

| Item | Detalhe |
|------|---------|
| **Server** | `@modelcontextprotocol/server-filesystem` (segunda instância) |
| **Pastas incluídas** | `./docs/novatech/` |
| **Modo** | **Somente leitura** — alcançado limitando o escopo a uma pasta sem arquivos de saída e sem dar ao modelo instruções para escrever aqui |
| **Quem consome** | Pipeline RAG (contexto de retrieval), Dev (referência durante implementação), QA (validação de respostas) |
| **Tools expostos** | `read_file`, `list_directory`, `search_files` |
| **Resources expostos** | Todos os documentos em `docs/novatech/` como resources nomeados |

**Justificativa de least privilege:** Separar esta instância da instância de escrita (`filesystem`) torna explícito — para o modelo e para o time — que estes documentos são a fonte da verdade do negócio e não devem ser alterados via IA. Se o escopo fosse unificado em uma única instância com acesso a tudo, um prompt malformado poderia sobrescrever uma política de devolução ou um SLA. A separação funciona como barreira de intenção: o model context torna claro que este server é de consulta.

---

### 2.3 `filesystem-corpus` — Corpus de chunks para recuperação (somente leitura)

**Necessidade:** O assistente simula o Azure AI Search lendo chunks pré-indexados em `data/retrieval-corpus/`. Esses arquivos representam o índice vetorial e nunca devem ser sobrescritos via IA durante o desenvolvimento.

| Item | Detalhe |
|------|---------|
| **Server** | `@modelcontextprotocol/server-filesystem` (terceira instância) |
| **Pastas incluídas** | `./data/retrieval-corpus/` |
| **Modo** | **Somente leitura** |
| **Quem consome** | Serviço de busca (`src/services/search.ts`) em modo local/dev, testes de integração |
| **Tools expostos** | `read_file`, `list_directory`, `search_files` |
| **Resources expostos** | Chunks como resources individuais endereçáveis por ID |

**Justificativa de least privilege:** O corpus é gerado pelo pipeline de ingestão (`src/pipeline/`) e não pelo assistente em tempo de query. Permitir escrita aqui abriria a possibilidade de o modelo "injetar" chunks fabricados no corpus, corrompendo os resultados do RAG. A instância separada sinaliza esta invariante arquitetural.

---

### 2.4 `git` — Histórico, diff e branches do repositório

**Necessidade:** O assistente precisa consultar histórico de commits, diffs e branches para contextualizar decisões (ex: "qual foi a última mudança no `chunker.ts`?", "este ADR já foi revisado?").

| Item | Detalhe |
|------|---------|
| **Server** | `mcp-server-git` |
| **Repositório** | `.` (raiz do repositório local) |
| **Modo** | Somente leitura (operações `git log`, `git diff`, `git show`, `git status`) |
| **Quem consome** | Tech Lead (revisão de histórico), Dev (contexto de mudanças), Delivery Manager (rastreabilidade) |
| **Tools expostos** | `git_log`, `git_diff`, `git_show`, `git_status`, `git_branch` |
| **Resources expostos** | Nenhum resource persistente — o state é derivado do repositório em tempo real |

**Justificativa de least privilege:** O server `mcp-server-git` por padrão não expõe operações destrutivas (`git reset`, `git push`, `git commit`) como tools do servidor MCP — ele é orientado a leitura. Isso é suficiente para as necessidades de contexto do assistente. Operações de escrita no git continuam sendo feitas pelo desenvolvedor no terminal, preservando o controle humano sobre o histórico.

---

### 2.5 `memory` — Memória persistente de decisões e linguagem ubíqua

**Necessidade:** O assistente precisa lembrar decisões arquiteturais recorrentes, a linguagem ubíqua do domínio (ex: "chunk", "corpus", "embedding", "RAG", "NovaTech Assistant") e contextos que não mudam entre sessões.

| Item | Detalhe |
|------|---------|
| **Server** | `@modelcontextprotocol/server-memory` |
| **Backend** | Grafo local (Knowledge Graph) em memória persistida em disco |
| **Quem consome** | Todos os papéis — o grafo é compartilhado entre sessões do projeto |
| **Tools expostos** | `create_entities`, `create_relations`, `add_observations`, `search_nodes`, `read_graph`, `open_nodes` |
| **Resources expostos** | O grafo completo como resource consultável |

**Casos de uso concretos:**
- Registrar que "Azure OpenAI foi escolhido no ADR-0001 por motivos de conformidade corporativa" — evita reperguntar a cada sessão.
- Mapear entidades de domínio: `Chunk → gerado_por → Pipeline`, `Query → resolvida_por → SearchService`.
- Persistir decisões de `tsconfig`, versões de dependências e convenções de nome acordadas pelo time.

**Justificativa de least privilege:** O server `memory` opera em um grafo isolado do repositório. Ele não tem acesso ao filesystem, não pode ler código nem documentos — apenas armazena e recupera entidades e relações que o modelo explicitamente persiste. Isso evita que o grafo se torne um espelho desordenado do repo, mantendo-o focado em conhecimento não derivável do código.

---

## 3. Tabela Resumo

| Necessidade | Server | Pastas/Escopo | Modo | Primitivas principais |
|-------------|--------|--------------|------|-----------------------|
| Código, specs, skills, prompts, testes, infra | `filesystem` | `./src ./specs ./skills ./prompts ./tests ./infra` | R/W | `write_file`, `read_file`, `search_files` |
| Documentação de negócio (NovaTech) | `filesystem-docs` | `./docs/novatech/` | Read-only | `read_file`, `search_files` |
| Corpus de chunks (retrieval simulado) | `filesystem-corpus` | `./data/retrieval-corpus/` | Read-only | `read_file`, `list_directory` |
| Histórico e branches do repositório | `git` | `.` (repo local) | Read-only | `git_log`, `git_diff`, `git_show` |
| Decisões persistentes e linguagem ubíqua | `memory` | Grafo local isolado | R/W (grafo) | `create_entities`, `search_nodes`, `read_graph` |

---

## 4. Por que instâncias separadas para read-only?

O `server-filesystem` não tem um flag nativo `--read-only` na linha de comando — a separação em instâncias distintas (com nomes semânticos `filesystem-docs` e `filesystem-corpus`) serve a três propósitos:

1. **Intenção explícita no JSON:** O nome do server comunica ao modelo e ao time que aquelas pastas são de consulta. O model context instrui o assistente a não escrever nesses paths.
2. **Superfície de ataque reduzida:** Se um server é comprometido ou um prompt adversarial força uma escrita, o dano fica contido à instância de escrita (`filesystem`), não se propagando ao corpus nem à documentação.
3. **Auditabilidade:** Logs de acesso MCP ficam segregados por instância — é possível identificar rapidamente se houve tentativa de escrita nas pastas protegidas.

---

## 5. Diagrama de consumo

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude / Agente IA                        │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
  filesystem  filesystem  filesystem   git       memory
  (R/W)       -docs(R)    -corpus(R)  (R)        (R/W grafo)
       │          │          │          │
  ./src       ./docs/     ./data/     repo
  ./specs     novatech/   retrieval-  local
  ./skills               corpus/
  ./prompts
  ./tests
  ./infra
```

---

## 6. Notas de manutenção

- Os nomes de pacote (`@modelcontextprotocol/server-filesystem`, `mcp-server-git`, `@modelcontextprotocol/server-memory`) podem evoluir. Consulte o README do repositório oficial `modelcontextprotocol/servers` antes de atualizar versões.
- O server `everything` (incluído no exemplo do Anexo C) é útil para explorar primitivas MCP durante aprendizado, mas não foi incluído na config de produção pois não cobre nenhuma necessidade real do projeto — seu uso indiscriminado aumentaria a superfície sem benefício concreto.
- Ao rodar `npx -y` em CI/CD, os packages são baixados na primeira execução. Para ambientes sem internet, pre-instale e remova o flag `-y`.
