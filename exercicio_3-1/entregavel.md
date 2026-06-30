# Code Review — `response-validator.ts`

**Arquivo revisado:** `src/services/response-validator.ts`
**Data:** 2026-06-30
**Revisor:** Claude Code (Sonnet 4.6)

---

## Contexto

O Copilot gerou o arquivo `response-validator.ts` responsável por:

- Validar a estrutura de saída do LLM via schema Zod
- Aplicar guardrails de segurança (ex: detectar respostas sobre devolução de carga perigosa sem a negativa obrigatória)
- Retornar um fallback seguro quando a validação falha

---

## Problemas Identificados e Corrigidos

### Problema 1 — Dead code: check redundante de `source_document` (linha 71)

**Severidade:** Média — falsa sensação de segurança, código enganoso

**Código original:**
```typescript
const validated = parsed.data;

if (!validated.source_document.trim()) {
  logFailure("missing_source_document");
  return SAFE_FALLBACK_RESPONSE;
}
```

**Por que é um bug:**
O schema Zod define `source_document` como `.string().trim().min(1)`. O método `.trim()` no Zod é um **transform** — ele modifica o valor durante o parse. Após um `safeParse` bem-sucedido, `validated.source_document` já é garantidamente uma string não-vazia e sem espaços nas bordas. O `if` nunca será `true`, portanto o bloco de fallback nunca dispara.

**Código corrigido:**
```typescript
const validated = parsed.data;

// bloco removido — Zod .trim().min(1) já garante a invariante
```

---

### Problema 2 — Regex de "devolução" incompleta (linha 37)

**Severidade:** Alta — guardrail deixa passar respostas inválidas

**Código original:**
```typescript
const mentionsReturn =
  /(devolucao|devolver|devolvida|devolvido|devolucoes)/.test(
    normalizedAnswer,
  );
```

**Por que é um bug:**
A regex enumera formas fixas do verbo "devolver", mas deixa de fora conjugações comuns:

| Forma omitida | Exemplo de frase |
|---|---|
| `devolve` | "a empresa **devolve** cargas perigosas" |
| `devolva` | "solicite que **devolva** a carga" |
| `devolvendo` | "estão **devolvendo** a carga perigosa" |
| `devolverá` | "o cliente **devolverá** a mercadoria" |
| `devolverem` | "ao **devolverem** o produto..." |

O guardrail falharia silenciosamente nessas frases — a resposta indevida passaria pela validação.

**Código corrigido:**
```typescript
// Stem-based match cobre todas as conjugações: devolve, devolva, devolvendo, devolverá, etc.
const mentionsReturn = /\bdevolv\w*/.test(normalizedAnswer);
```

A âncora `\b` evita falsos positivos em palavras que comecem com "devolv" por coincidência, e `\w*` captura qualquer sufixo conjugado.

---

### Problema 3 — Regex de "carga perigosa" não tolera modificadores (linha 33)

**Severidade:** Média — guardrail não dispara para variações linguísticas naturais

**Código original:**
```typescript
const mentionsDangerousCargo = /carga(s)? perigosa(s)?/.test(
  normalizedAnswer,
);
```

**Por que é um bug:**
A regex exige que "carga" e "perigosa" sejam palavras adjacentes. Qualquer modificador intermediário quebra o match:

- `"carga muito perigosa"` → ❌ não detectado
- `"carga extremamente perigosa"` → ❌ não detectado
- `"cargas altamente perigosas"` → ❌ não detectado

**Código corrigido:**
```typescript
// Permite uma palavra opcional entre "carga" e "perigosa"
const mentionsDangerousCargo = /cargas?\s+(?:\w+\s+)?perigosas?/.test(
  normalizedAnswer,
);
```

O grupo `(?:\w+\s+)?` é não-capturante e opcional — aceita um modificador entre os termos sem capturá-lo.

---

## Diff Completo

```diff
 function mentionsDangerousCargoAndReturn(answer: string): boolean {
   const normalizedAnswer = normalizeText(answer);
-  const mentionsDangerousCargo = /carga(s)? perigosa(s)?/.test(
+  // Allow optional word(s) between "carga" and "perigosa" (e.g. "carga muito perigosa")
+  const mentionsDangerousCargo = /cargas?\s+(?:\w+\s+)?perigosas?/.test(
     normalizedAnswer,
   );
-  const mentionsReturn =
-    /(devolucao|devolver|devolvida|devolvido|devolucoes)/.test(
-      normalizedAnswer,
-    );
+  // Stem-based match catches all conjugations: devolve, devolva, devolvendo, devolverá, etc.
+  const mentionsReturn = /\bdevolv\w*/.test(normalizedAnswer);
 
   return mentionsDangerousCargo && mentionsReturn;
 }
 
 ...
 
   const validated = parsed.data;
 
-  if (!validated.source_document.trim()) {
-    logFailure("missing_source_document");
-    return SAFE_FALLBACK_RESPONSE;
-  }
-
   if (
```

---

## Estado Final do Arquivo

```typescript
import { z } from "zod";
import { logger } from "../shared/logger";

export const structuredOutputSchema = z
  .object({
    answer: z.string().trim().min(1, "answer is required"),
    source_document: z.string().trim().min(1, "source_document is required"),
    confidence_score: z
      .number()
      .min(0, "confidence_score must be >= 0")
      .max(1, "confidence_score must be <= 1"),
  })
  .strict();

export type StructuredOutput = z.infer<typeof structuredOutputSchema>;

export const SAFE_FALLBACK_RESPONSE: StructuredOutput = {
  answer:
    "Nao foi possivel validar a resposta com seguranca. Encaminhe o caso para revisao humana no atendimento.",
  source_document: "POL-001",
  confidence_score: 0,
};

function normalizeText(input: string): string {
  return input
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();
}

function mentionsDangerousCargoAndReturn(answer: string): boolean {
  const normalizedAnswer = normalizeText(answer);
  // Allow optional word(s) between "carga" and "perigosa" (e.g. "carga muito perigosa")
  const mentionsDangerousCargo = /cargas?\s+(?:\w+\s+)?perigosas?/.test(
    normalizedAnswer,
  );
  // Stem-based match catches all conjugations: devolve, devolva, devolvendo, devolverá, etc.
  const mentionsReturn = /\bdevolv\w*/.test(normalizedAnswer);

  return mentionsDangerousCargo && mentionsReturn;
}

function hasRequiredNegative(answer: string): boolean {
  const normalizedAnswer = normalizeText(answer);

  return /(nao pode|nao e possivel|impossivel|nao sao elegiveis|nao e elegivel|nao podem)/.test(
    normalizedAnswer,
  );
}

function logFailure(reason: string, details?: unknown): void {
  logger.warn({ reason, details }, "Response blocked by validation guardrail");
}

export function validateAndGuardResponse(
  rawResponse: unknown,
): StructuredOutput {
  const parsed = structuredOutputSchema.safeParse(rawResponse);

  if (!parsed.success) {
    logFailure(
      "structured_output_schema_validation_failed",
      parsed.error.flatten(),
    );
    return SAFE_FALLBACK_RESPONSE;
  }

  const validated = parsed.data;

  if (
    mentionsDangerousCargoAndReturn(validated.answer) &&
    !hasRequiredNegative(validated.answer)
  ) {
    logFailure("dangerous_cargo_return_without_negative", {
      answer: validated.answer,
      source_document: validated.source_document,
    });
    return SAFE_FALLBACK_RESPONSE;
  }

  return validated;
}
```

---

## Resumo

| # | Problema | Impacto | Status |
|---|----------|---------|--------|
| 1 | Dead code: `!validated.source_document.trim()` sempre falso após Zod parse | Código enganoso | ✅ Corrigido |
| 2 | Regex de devolução não cobre `devolve`, `devolva`, `devolvendo`, `devolverá` | Guardrail falha silenciosamente | ✅ Corrigido |
| 3 | Regex de carga perigosa não aceita modificador entre os termos | Guardrail falha para variações naturais | ✅ Corrigido |
