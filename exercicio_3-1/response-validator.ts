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
    .replace(/[\u0300-\u036f]/g, "")
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
