import pino from "pino";

type EnvMap = Record<string, string | undefined>;

const env =
  (globalThis as { process?: { env?: EnvMap } }).process?.env ?? ({} as EnvMap);

export const logger = pino({
  level: env.LOG_LEVEL ?? "info",
});
