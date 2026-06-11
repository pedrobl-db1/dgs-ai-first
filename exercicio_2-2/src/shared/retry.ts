import { logger } from "./logger";

interface RetryOptions {
  maxAttempts?: number;
  baseDelayMs?: number;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

export async function withRetry<T>(
  fn: () => Promise<T>,
  opts: RetryOptions = {},
): Promise<T> {
  const maxAttempts = opts.maxAttempts ?? 3;
  const baseDelayMs = opts.baseDelayMs ?? 200;

  let lastError: unknown;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const delayMs =
      attempt < maxAttempts ? baseDelayMs * 2 ** (attempt - 1) : 0;

    logger.info(
      {
        attempt,
        maxAttempts,
        delayMs,
      },
      "Executing retriable operation",
    );

    try {
      return await fn();
    } catch (error) {
      lastError = error;

      if (attempt >= maxAttempts) {
        break;
      }

      logger.warn(
        {
          attempt,
          maxAttempts,
          delayMs,
          err: error,
        },
        "Retriable operation failed, waiting before next attempt",
      );

      await sleep(delayMs);
    }
  }

  throw lastError;
}
