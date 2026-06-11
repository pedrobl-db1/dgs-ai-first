# Pré Code Review - Revisão Crítica

## Validação aceita pergunta em branco

- Arquivo: src/functions/query/validator.ts
- Problema: o schema atual usa `z.string().min(1).max(1000)`, o que permite entradas como " " (apenas espaços).

```javascript
export const QueryRequestSchema = z.object({
  question: z.string().min(1).max(1000),
});
```

- Risco: chamadas desnecessárias ao fluxo de search/completion, consumo de custo e respostas sem valor para o usuário.
- Ajuste recomendado: aplicar `trim()` antes de `min(1)`.

```javascript
export const QueryRequestSchema = z.object({
  question: z.string().trim().min(1).max(1000),
});
```

## Exposição de nomes internos de variáveis de ambiente

- Arquivo: src/shared/config.ts
- Problema: o erro lançado no carregamento do modulo inclui o nome exato da variável ausente (`Missing required environment variable: <NOME>`).

```javascript
function getRequiredEnv(name: string): string {
  const value = env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }

  return value;
}
```

- Risco: em logs centralizados, esse comportamento revela detalhes internos da configuração do serviço, aumentando superfície de recon para atacantes.
- Ajuste recomendado: retornar mensagem generica para logs externos e registrar detalhe tecnico apenas em canal interno seguro (debug/observabilidade protegida).

```javascript
function getRequiredEnv(name: string): string {
  const value = env[name];
  if (!value) {
    throw new Error("Application configuration is invalid");
  }

  return value;
}
```
