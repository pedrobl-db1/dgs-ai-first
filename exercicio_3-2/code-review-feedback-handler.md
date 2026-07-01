# Revisão de Código — `feedback-handler.ts`

**Revisores:** Pedro Lima e Claude
**Data:** 2026-07-01  
**Status:** ❌ Bloqueado — não aprovado para merge

---

## Revisão do Desenvolvedor (Pedro Lima)

Pontos identificados na leitura inicial do código:

- **`console.log`** — uso direto proibido pelo AGENTS.md; deve ser substituído por `pino`.
- **Dados pessoais no log** — `attendantEmail` está sendo serializado e logado, violando a regra de privacidade do projeto.
- **`require` dinâmico** — `require('@azure/cosmos')` dentro do corpo da função; imports devem ser estáticos no topo do arquivo.
- **Cast `as any`** — o body da requisição é tipado como `any`, contornando o TypeScript strict mode.

---

## Contexto

Revisão do módulo de feedback gerado pelo Copilot, solicitada pelo Tech Lead antes do merge. O código foi avaliado contra as regras definidas no `AGENTS.md` do projeto e boas práticas gerais de qualidade.

---

## Violações das regras do AGENTS.md (Revisão do Claude)

### 1. `console.log` em vez de `pino`

**Linha:** 11  
**Severidade:** Bloqueante

```typescript
console.log("Feedback recebido:", JSON.stringify(feedback));
```

**Regra violada:** _"pino para logging (nunca console.log)"_

`console.log` não produz logs estruturados, não tem níveis de severidade e não se integra ao pipeline de observabilidade do projeto. Deve ser substituído pelo logger `pino` já configurado no projeto.

---

### 2. Dado pessoal exposto no log

**Linha:** 11  
**Severidade:** Bloqueante

O objeto `feedback` inclui o campo `attendantEmail` e é serializado integralmente via `JSON.stringify` antes de ser logado.

**Regra violada:** _"Nunca logar dados pessoais (e-mail, nome)"_

Além de violar a convenção do projeto, pode representar risco de conformidade (LGPD). Mesmo após corrigir para `pino`, o campo de e-mail não pode aparecer no payload do log.

---

### 3. `require` dinâmico dentro da função

**Linhas:** 13–14  
**Severidade:** Bloqueante

```typescript
const { CosmosClient } = require("@azure/cosmos");
```

**Regra violada:** _"Imports estáticos no topo (nunca require dinâmico)"_

O `require` está no corpo da função e é executado a cada requisição recebida. O import deve ser estático, declarado no topo do arquivo:

```typescript
import { CosmosClient } from "@azure/cosmos";
```

---

### 4. Ausência de validação com Zod

**Linhas:** 4–10  
**Severidade:** Bloqueante

```typescript
const body = await request.json() as any;
const feedback = {
  queryId: body.queryId,
  rating: body.rating,
  ...
};
```

**Regra violada:** _"Zod para validação de input"_

Nenhum schema valida o body antes do uso. Campos ausentes, com tipo incorreto ou com valores fora do domínio esperado (ex: `rating` fora do intervalo permitido) são persistidos no banco sem nenhuma rejeição.

---

### 5. Cast `as any`

**Linha:** 4  
**Severidade:** Bloqueante

```typescript
const body = (await request.json()) as any;
```

**Regra violada:** _"TypeScript strict mode"_

O cast para `any` desabilita completamente a verificação de tipos para o objeto mais crítico da função — o body da requisição. Em modo strict, isso é inaceitável. A solução correta é usar Zod para inferir o tipo a partir do schema validado.

---

## Problemas adicionais de qualidade (Revisão do Claude)

### 6. Ausência de tratamento de erro

**Severidade:** Alta

Não há `try/catch` em nenhum ponto da função. Uma falha na conexão com o CosmosDB ou na operação de escrita resulta em uma exceção não tratada, sem log estruturado do erro e sem resposta controlada ao cliente.

**Correção esperada:** envolver a operação de persistência em `try/catch`, logar o erro com `pino` (sem dados pessoais) e retornar status `500` com body JSON descritivo.

---

### 7. `CosmosClient` instanciado por requisição

**Severidade:** Média

```typescript
const client = new CosmosClient(process.env.COSMOS_CONNECTION_STRING);
```

Uma nova instância do cliente é criada a cada invocação da Azure Function. O `CosmosClient` deve ser instanciado uma única vez no escopo do módulo e reutilizado entre requisições, o que é a prática recomendada pela Microsoft para Azure Functions.

---

### 8. Variável de ambiente sem validação

**Severidade:** Média

`process.env.COSMOS_CONNECTION_STRING` é passada diretamente ao `CosmosClient` sem verificação. Se a variável não estiver definida no ambiente, o SDK lança um erro opaco difícil de diagnosticar.

**Correção esperada:** validar a presença e o formato da variável na inicialização do módulo, preferencialmente via Zod com `z.string().min(1)`.

---

## Tabela de resumo

| #   | Problema                      | Severidade | Viola AGENTS.md |
| --- | ----------------------------- | :--------: | :-------------: |
| 1   | `console.log` em vez de pino  | Bloqueante |       Sim       |
| 2   | E-mail exposto no log         | Bloqueante |       Sim       |
| 3   | `require` dinâmico            | Bloqueante |       Sim       |
| 4   | Sem validação Zod             | Bloqueante |       Sim       |
| 5   | Cast `as any`                 | Bloqueante |       Sim       |
| 6   | Sem `try/catch`               |    Alta    |       Não       |
| 7   | `CosmosClient` por requisição |   Média    |       Não       |
| 8   | Env var sem validação         |   Média    |       Não       |

---

## Recomendação

**Merge bloqueado.** O código viola simultaneamente todas as convenções críticas definidas no `AGENTS.md`. Não se trata de ajustes pontuais — o arquivo precisa ser reescrito seguindo as convenções do projeto antes de retornar para revisão.
