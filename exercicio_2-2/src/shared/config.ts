type EnvMap = Record<string, string | undefined>;

const env =
  (globalThis as { process?: { env?: EnvMap } }).process?.env ?? ({} as EnvMap);

function getRequiredEnv(name: string): string {
  const value = env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }

  return value;
}

export const AZURE_OPENAI_ENDPOINT = getRequiredEnv("AZURE_OPENAI_ENDPOINT");
export const AZURE_OPENAI_API_KEY = getRequiredEnv("AZURE_OPENAI_API_KEY");
export const AZURE_OPENAI_EMBEDDING_DEPLOYMENT = getRequiredEnv(
  "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
);
export const AZURE_OPENAI_COMPLETION_DEPLOYMENT = getRequiredEnv(
  "AZURE_OPENAI_COMPLETION_DEPLOYMENT",
);
export const AZURE_SEARCH_ENDPOINT = getRequiredEnv("AZURE_SEARCH_ENDPOINT");
export const AZURE_SEARCH_API_KEY = getRequiredEnv("AZURE_SEARCH_API_KEY");
export const AZURE_SEARCH_INDEX_NAME = getRequiredEnv(
  "AZURE_SEARCH_INDEX_NAME",
);

export const SYSTEM_PROMPT_PATH =
  env.SYSTEM_PROMPT_PATH ?? "./prompts/system-prompt.md";

export const CONTEXT_BUDGET = {
  systemTokens: 4096,
  chunksTokens: 8192,
} as const;
