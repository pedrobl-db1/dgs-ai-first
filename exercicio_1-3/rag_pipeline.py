from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import chromadb
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional runtime dependency
    SentenceTransformer = None


DOC_FILES = {
    "POL-001": "POL-001-politica-devolucao.md",
    "PROC-042": "PROC-042-frete-especial-v1.md",
    "PROC-042-v2": "PROC-042-v2-frete-especial-revisado.md",
    "SLA-2024": "SLA-2024-tabela-sla-clientes.md",
    "FAQ": "FAQ-atendimento.md",
}


def estimate_tokens(text: str) -> int:
    # Practical approximation for planning (pt-BR prose): ~0.75 words/token
    words = max(1, len(text.split()))
    return int(words / 0.75)


@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: Dict[str, Any]


class NovaTechRAGPipeline:
    def __init__(
        self,
        project_root: Path,
        persist_dir: Path,
        collection_name: str = "novatech_rag",
        embedding_model: str = "all-MiniLM-L6-v2",
        embedding_backend: str = "local-hash",
    ) -> None:
        self.project_root = project_root
        self.persist_dir = persist_dir
        self.embedding_model_name = embedding_model
        self.embedding_backend = embedding_backend

        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.model = None
        self.local_vectorizer = None

        if self.embedding_backend == "sbert":
            if SentenceTransformer is None:
                raise RuntimeError(
                    "sentence-transformers nao esta disponivel. "
                    "Use backend local-hash ou instale a dependencia."
                )
            self.model = SentenceTransformer(embedding_model)
        elif self.embedding_backend == "local-hash":
            # Offline embedding fallback for reliable classroom execution.
            self.local_vectorizer = HashingVectorizer(
                n_features=1024,
                alternate_sign=False,
                norm="l2",
                ngram_range=(1, 2),
            )
        else:
            raise ValueError("embedding_backend deve ser 'local-hash' ou 'sbert'")

    def _encode_texts(self, texts: List[str]) -> List[List[float]]:
        if self.embedding_backend == "sbert" and self.model is not None:
            return self.model.encode(texts, normalize_embeddings=True).tolist()

        if self.local_vectorizer is None:
            raise RuntimeError("Vectorizer local nao inicializado")

        matrix = self.local_vectorizer.transform(texts)
        dense = matrix.toarray().astype(np.float32)
        return dense.tolist()

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def load_documents(self) -> Dict[str, str]:
        docs: Dict[str, str] = {}
        for doc_id, file_name in DOC_FILES.items():
            file_path = self.project_root / file_name
            if not file_path.exists():
                raise FileNotFoundError(f"Documento nao encontrado: {file_path}")
            docs[doc_id] = self._normalize_text(file_path.read_text(encoding="utf-8"))
        return docs

    @staticmethod
    def _iter_sections(markdown_text: str) -> Iterable[Tuple[str, str]]:
        lines = markdown_text.split("\n")
        current_title = "intro"
        buffer: List[str] = []

        for line in lines:
            if line.startswith("## ") or line.startswith("### "):
                if buffer:
                    yield current_title, "\n".join(buffer).strip()
                    buffer = []
                current_title = line.lstrip("# ").strip()
            else:
                buffer.append(line)

        if buffer:
            yield current_title, "\n".join(buffer).strip()

    @staticmethod
    def _chunk_words(text: str, max_words: int = 380, overlap_words: int = 60) -> List[str]:
        words = text.split()
        if not words:
            return []
        if len(words) <= max_words:
            return [text]

        chunks: List[str] = []
        step = max_words - overlap_words
        for start in range(0, len(words), step):
            end = start + max_words
            snippet = words[start:end]
            if not snippet:
                continue
            chunks.append(" ".join(snippet))
            if end >= len(words):
                break
        return chunks

    def build_chunks(self, docs: Dict[str, str]) -> List[Chunk]:
        all_chunks: List[Chunk] = []

        for doc_id, text in docs.items():
            section_index = 0
            for section_title, section_body in self._iter_sections(text):
                section_index += 1
                section_text = section_body.strip()
                if not section_text:
                    continue

                fragments = self._chunk_words(section_text)
                for idx, frag in enumerate(fragments, start=1):
                    chunk_id = f"{doc_id}__S{section_index:02d}__C{idx:02d}"
                    metadata = {
                        "doc_id": doc_id,
                        "section": section_title,
                        "chunk_index": idx,
                        "token_estimate": estimate_tokens(frag),
                        "source_type": "informal" if doc_id == "FAQ" else "formal",
                        "version_hint": "v2" if doc_id == "PROC-042-v2" else ("v1" if doc_id == "PROC-042" else "official"),
                    }
                    all_chunks.append(Chunk(chunk_id=chunk_id, text=frag, metadata=metadata))

        return all_chunks

    def ingest(self) -> Dict[str, Any]:
        docs = self.load_documents()
        chunks = self.build_chunks(docs)

        if self.collection.count() > 0:
            # Rebuild local PoC index from scratch for reproducible tests.
            existing = self.collection.get(include=[])
            if existing.get("ids"):
                self.collection.delete(ids=existing["ids"])

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        embeddings = self._encode_texts(documents)

        self.collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)

        total_tokens = sum(m.get("token_estimate", 0) for m in metadatas)
        return {
            "documents_ingested": len(docs),
            "chunks_ingested": len(chunks),
            "estimated_tokens": total_tokens,
            "embedding_model": self.embedding_model_name,
            "persist_dir": str(self.persist_dir),
        }

    def search(self, question: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self._encode_texts([question])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["distances", "documents", "metadatas"],
        )

        rows: List[Dict[str, Any]] = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for cid, ctext, meta, dist in zip(ids, docs, metas, distances):
            similarity = 1.0 / (1.0 + float(dist))
            rows.append(
                {
                    "chunk_id": cid,
                    "document": ctext,
                    "metadata": meta,
                    "distance": float(dist),
                    "similarity": round(similarity, 4),
                    "gabarito_alias": map_chunk_to_reference_alias(meta, ctext),
                }
            )
        return rows

    @staticmethod
    def build_prompt(
        system_prompt: str,
        question: str,
        retrieved_chunks: List[Dict[str, Any]],
    ) -> str:
        blocks: List[str] = []
        blocks.append("[SYSTEM PROMPT]")
        blocks.append(system_prompt.strip())
        blocks.append("")
        blocks.append("[CONTEXT CHUNKS]")

        for i, item in enumerate(retrieved_chunks, start=1):
            meta = item["metadata"]
            alias = item.get("gabarito_alias") or "N/A"
            source = f"{meta.get('doc_id')} | {meta.get('section')} | alias={alias}"
            blocks.append(f"Chunk {i} - {source}")
            blocks.append(item["document"])
            blocks.append("")

        blocks.append("[USER QUESTION]")
        blocks.append(question)
        blocks.append("")
        blocks.append("Responda seguindo as regras do SYSTEM PROMPT.")
        return "\n".join(blocks)


def map_chunk_to_reference_alias(metadata: Dict[str, Any], text: str) -> str:
    doc_id = metadata.get("doc_id", "")
    section = (metadata.get("section", "") or "").lower()
    lower = text.lower()

    if doc_id == "POL-001":
        if "3.1" in section or "prazo geral" in section:
            return "POL-001-A"
        if "3.2" in section or "exce" in section:
            return "POL-001-B"
        if "3.3" in section or "procedimento" in section:
            return "POL-001-C"
        if "3.5" in section or "custos" in section:
            return "POL-001-D"

    if doc_id == "PROC-042":
        if "2.1" in section or "multiplicadores" in section:
            return "PROC-042-B"
        if "se" in section and "formula" in section or "fator de peso" in lower:
            return "PROC-042-A"
        if "prazo" in section:
            return "PROC-042-C"

    if doc_id == "PROC-042-v2":
        if "2.1" in section or "multiplicadores" in section:
            return "PROC-042v2-B"
        if "disposi" in section:
            return "PROC-042v2-E"
        if "condi" in section:
            return "PROC-042v2-D"
        if "prazo" in section:
            return "PROC-042v2-C"
        if "fator de peso" in lower or "formula" in section:
            return "PROC-042v2-A"

    if doc_id == "SLA-2024":
        if "classifica" in section:
            return "SLA-2024-A"
        if "incidente" in section and "critico" in section:
            return "SLA-2024-D"
        if "penalidades" in section:
            return "SLA-2024-E"
        if "tabela" in section or "slas" in section:
            if "30min" in lower or "incidentes criticos" in lower:
                return "SLA-2024-C"
            return "SLA-2024-B"

    if doc_id == "FAQ":
        if "item 3" in section:
            return "FAQ-03"
        if "item 8" in section:
            return "FAQ-08"
        if "item 15" in section:
            return "FAQ-15"
        if "item 32" in section:
            return "FAQ-32"
        if "item 38" in section:
            return "FAQ-38"

    return "UNMAPPED"


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG pipeline PoC - NovaTech")
    parser.add_argument("command", choices=["ingest", "ask"], help="Action to run")
    parser.add_argument("--question", help="Question for ask mode")
    parser.add_argument("--top-k", type=int, default=5, help="Number of retrieved chunks")
    parser.add_argument(
        "--embedding-backend",
        choices=["local-hash", "sbert"],
        default="local-hash",
        help="Embedding backend (default: local-hash for offline execution)",
    )
    args = parser.parse_args()

    this_dir = Path(__file__).resolve().parent
    project_root = this_dir.parent
    persist_dir = this_dir / "chroma_db"
    prompt_file = this_dir / "data" / "system_prompt.txt"

    pipeline = NovaTechRAGPipeline(
        project_root=project_root,
        persist_dir=persist_dir,
        embedding_backend=args.embedding_backend,
    )

    if args.command == "ingest":
        summary = pipeline.ingest()
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return

    if args.command == "ask":
        if not args.question:
            raise ValueError("Use --question no modo ask")
        if pipeline.collection.count() == 0:
            print("Colecao vazia. Executando ingestao primeiro...")
            pipeline.ingest()

        chunks = pipeline.search(args.question, top_k=args.top_k)
        prompt = pipeline.build_prompt(
            system_prompt=_load_text(prompt_file),
            question=args.question,
            retrieved_chunks=chunks,
        )

        print("\n=== RETRIEVAL ===")
        for row in chunks:
            meta = row["metadata"]
            print(
                f"- {row['chunk_id']} | alias={row['gabarito_alias']} | "
                f"doc={meta.get('doc_id')} | sim={row['similarity']}"
            )

        print("\n=== PROMPT MONTADO ===\n")
        print(prompt)


if __name__ == "__main__":
    main()
