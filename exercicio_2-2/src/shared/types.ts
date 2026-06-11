export interface QueryRequest {
  question: string;
}

export interface QueryResponse {
  answer: string;
  source_document: string;
}

export interface Chunk {
  id: string;
  content: string;
  source_document: string;
  score?: number;
}

export interface SearchResult {
  chunks: Chunk[];
}
