---
name: foundation/typescript-conventions
description: Define standard TypeScript conventions for NovaTech Assistant, including strict typing, module organization, naming, and practical DO/DON'T guidance for any generated .ts/.tsx artifact.
---

# Skill: foundation/typescript-conventions

## Contexto

Esta skill define as convencoes obrigatorias de TypeScript para todo o projeto NovaTech Assistant.
Ela e aplicada implicitamente por qualquer geracao de codigo `.ts` e serve como baseline para skills de Domain e Artifact.

Objetivos principais:

- Garantir tipagem estrita e previsivel.
- Evitar ambiguidade de contratos entre modulos.
- Manter legibilidade e consistencia entre backend, pipeline, bot, web e testes.

## Escopo

Aplica-se a:

- `src/**/*.ts`
- `tests/**/*.ts`
- `src/web/src/**/*.ts` e `src/web/src/**/*.tsx`

Nao cobre convencoes de negocio (erros, logging, contratos HTTP), que sao tratadas em skills especificas.

## Regras Prescritivas

### 1) Configuracao base obrigatoria

- O codigo deve respeitar `tsconfig.json` com `target: ES2022` e `strict: true`.
- Nenhum artefato pode depender de comportamento de tipagem frouxa para funcionar.

### 2) `type` vs `interface`

- Use `type` por padrao para DTOs, aliases, unions, intersections e tipos internos.
- Use `interface` apenas quando houver necessidade real de extensao/merge contratual.
- Em componentes React, `interface` para props e permitido por clareza semantica.

### 3) Proibicao de `any` explicito

- `any` explicito e proibido.
- Prefira `unknown` + narrowing, generics, tipos discriminados ou utilitarios (`Record`, `Partial`, `Pick`, etc.).

### 4) Tipagem de fronteira

- Toda fronteira externa (HTTP, arquivo, AI/Search SDK, input de usuario) entra como `unknown` ou tipo validado.
- Nunca confiar diretamente em dado externo sem validacao/parsing.

### 5) Convencoes de export

- Preferir named exports.
- `default export` e permitido somente quando o modulo expuser uma unica entidade principal e isso melhorar a leitura.
- Nao duplicar export da mesma entidade no mesmo modulo.

### 6) Imports e organizacao de modulos

- Nao usar barrel files, exceto `index.ts` de camada quando explicitamente necessario.
- Imports devem ser estaveis e explicitos (evitar caminhos opacos que escondem origem).
- Evitar import ciclico entre modulos.

### 7) Nomenclatura

- Tipos, interfaces, enums e classes: `PascalCase`.
- Funcoes, variaveis, metodos e propriedades: `camelCase`.
- Constantes globais e env keys: `SCREAMING_SNAKE_CASE`.
- Arquivos TypeScript: `kebab-case.ts` (exceto componentes React em `PascalCase.tsx`).

### 8) Assinaturas explicitas

- Funcoes publicas devem declarar tipo de retorno explicitamente.
- Parametros e retorno de funcoes assicronas devem ser tipados (`Promise<T>`).
- Evitar inferencia implicita em APIs publicas.

### 9) Null safety

- Tratar explicitamente `null`/`undefined`.
- Evitar non-null assertion (`!`) salvo em pontos controlados e documentados.

### 10) Enums e unions

- Preferir union de literais para estados simples.
- Usar `enum` somente quando houver ganho claro de interoperabilidade/legibilidade.

## DO / DON'T (Exemplos)

### Exemplo 1: `any` vs `unknown` + narrowing

DO:

```ts
type QueryPayload = {
  question: string;
};

export function parseQueryPayload(input: unknown): QueryPayload {
  if (typeof input !== "object" || input === null || !("question" in input)) {
    throw new Error("Payload invalido");
  }

  const question = (input as { question: unknown }).question;
  if (typeof question !== "string" || question.trim().length === 0) {
    throw new Error("Campo question invalido");
  }

  return { question };
}
```

DON'T:

```ts
export function parseQueryPayload(input: any) {
  return { question: input.question };
}
```

### Exemplo 2: `type` por padrao

DO:

```ts
type SearchChunk = {
  id: string;
  source: string;
  score: number;
  content: string;
};

type SearchResult = SearchChunk[];
```

DON'T:

```ts
interface SearchChunk {
  id: string;
  source: string;
  score: number;
  content: string;
}

interface SearchResult extends Array<SearchChunk> {}
```

### Exemplo 3: `interface` para props de React

DO:

```tsx
interface ResponseCardProps {
  answer: string;
  sources: string[];
  onFeedbackSubmit: (rating: "up" | "down") => void;
}

export function ResponseCard(props: ResponseCardProps) {
  return <section>{props.answer}</section>;
}
```

DON'T:

```tsx
type ResponseCardProps = any;

export const ResponseCard = (props: ResponseCardProps) => {
  return <section>{props.answer}</section>;
};
```

### Exemplo 4: exports e imports explicitos

DO:

```ts
// src/services/search.ts
export type SearchQuery = {
  text: string;
};

export async function searchDocuments(query: SearchQuery): Promise<string[]> {
  return [query.text];
}
```

```ts
// src/functions/query/handler.ts
import { searchDocuments, type SearchQuery } from "../../services/search";

export async function handler(): Promise<void> {
  const query: SearchQuery = { text: "prazo de entrega" };
  await searchDocuments(query);
}
```

DON'T:

```ts
// src/services/index.ts
export * from "./search";
export * from "./completion";
export * from "./prompt-builder";
```

```ts
// src/functions/query/handler.ts
import { searchDocuments } from "../../services";
```

## Anti-padroes (evitar sempre)

- Uso de `any` para contornar erro de compilacao.
- Cast em cadeia (`as unknown as TipoFinal`) sem validacao real.
- API publica sem tipo de retorno explicito.
- `default export` misturado com multiplos named exports sem criterio.
- Barrel global (`src/index.ts`) que esconde dependencias reais da camada.
- Ignorar nulos com `!` em vez de tratar o fluxo.
- Tipos gigantes e acoplados a tudo ("God types") ao inves de tipos menores por modulo.

## Checklist rapido para geracao de codigo

- Nenhum `any` explicito foi introduzido.
- Tipos de entrada externa foram validados ou narrowed.
- APIs publicas tem assinatura de retorno explicita.
- Imports sao diretos e sem barrel indevido.
- Convencoes de nome e organizacao de tipo foram respeitadas.
