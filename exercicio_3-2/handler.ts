import { CosmosClient } from "@azure/cosmos";
import { app, HttpRequest, HttpResponseInit } from "@azure/functions";
import { ZodError, z } from "zod";
import { logger } from "../../shared/logger";
import { FeedbackRequest, FeedbackRequestSchema } from "./validator";

const FeedbackEnvSchema = z.object({
  COSMOS_CONNECTION_STRING: z.string().min(1),
  COSMOS_DATABASE_NAME: z.string().min(1).default("novatech"),
  COSMOS_FEEDBACK_CONTAINER_NAME: z.string().min(1).default("feedbacks"),
});

const feedbackEnv = FeedbackEnvSchema.parse({
  COSMOS_CONNECTION_STRING: process.env.COSMOS_CONNECTION_STRING,
  COSMOS_DATABASE_NAME: process.env.COSMOS_DATABASE_NAME,
  COSMOS_FEEDBACK_CONTAINER_NAME: process.env.COSMOS_FEEDBACK_CONTAINER_NAME,
});

const cosmosClient = new CosmosClient(feedbackEnv.COSMOS_CONNECTION_STRING);
const feedbackContainer = cosmosClient
  .database(feedbackEnv.COSMOS_DATABASE_NAME)
  .container(feedbackEnv.COSMOS_FEEDBACK_CONTAINER_NAME);

type FeedbackEntity = FeedbackRequest & {
  id: string;
  timestamp: string;
};

function validationErrorResponse(error: ZodError): HttpResponseInit {
  const field = error.issues[0]?.path.join(".") ?? "request";
  const message = error.issues[0]?.message ?? "invalid input";

  return {
    status: 400,
    jsonBody: {
      error: "invalid_request",
      field,
      message,
    },
  };
}

function toFeedbackEntity(payload: FeedbackRequest): FeedbackEntity {
  const timestamp = new Date().toISOString();

  return {
    id: `${payload.queryId}-${timestamp}`,
    ...payload,
    timestamp,
  };
}

export async function feedbackHandler(
  request: HttpRequest,
): Promise<HttpResponseInit> {
  const body = await request.json();
  const parsed = FeedbackRequestSchema.safeParse(body);

  if (!parsed.success) {
    logger.warn(
      { issues: parsed.error.flatten().fieldErrors },
      "Feedback request validation failed",
    );
    return validationErrorResponse(parsed.error);
  }

  const feedback = toFeedbackEntity(parsed.data);

  try {
    await feedbackContainer.items.create(feedback);
    logger.info(
      { queryId: feedback.queryId, rating: feedback.rating },
      "Feedback persisted",
    );

    return {
      status: 200,
      jsonBody: { status: "ok" },
    };
  } catch (error) {
    logger.error(
      {
        err: error,
        queryId: feedback.queryId,
      },
      "Failed to persist feedback",
    );

    return {
      status: 500,
      jsonBody: {
        error: "internal_error",
        message: "Unable to persist feedback",
      },
    };
  }
}

app.http("feedback", {
  methods: ["POST"],
  handler: feedbackHandler,
});
