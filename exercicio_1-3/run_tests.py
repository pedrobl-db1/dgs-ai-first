from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from rag_pipeline import NovaTechRAGPipeline


def evaluate_case(retrieved_aliases: List[str], expected_aliases: List[str]) -> Dict[str, Any]:
    matched = [a for a in retrieved_aliases if a in expected_aliases]
    missing = [a for a in expected_aliases if a not in retrieved_aliases]
    precision = len(matched) / max(1, len(retrieved_aliases))
    recall = len(matched) / max(1, len(expected_aliases))
    return {
        "matched": matched,
        "missing": missing,
        "precision_at_k": round(precision, 3),
        "recall": round(recall, 3),
    }


def render_markdown(results: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("# Resultados de Teste - Exercicio 1.3")
    lines.append("")
    lines.append("## Resumo")

    avg_recall = sum(r["evaluation"]["recall"] for r in results) / max(1, len(results))
    avg_precision = sum(r["evaluation"]["precision_at_k"] for r in results) / max(1, len(results))

    lines.append(f"- Casos executados: {len(results)}")
    lines.append(f"- Recall medio: {avg_recall:.3f}")
    lines.append(f"- Precision@k media: {avg_precision:.3f}")
    lines.append("")

    lines.append("## Casos")
    for r in results:
        lines.append("")
        lines.append(f"### {r['id']} - {r['question']}")
        lines.append(f"- Esperado (gabarito): {', '.join(r['expected'])}")
        lines.append(f"- Recuperado (aliases): {', '.join(r['retrieved_aliases'])}")
        lines.append(f"- Matched: {', '.join(r['evaluation']['matched']) if r['evaluation']['matched'] else 'nenhum'}")
        lines.append(f"- Missing: {', '.join(r['evaluation']['missing']) if r['evaluation']['missing'] else 'nenhum'}")
        lines.append(f"- Recall: {r['evaluation']['recall']}")
        lines.append(f"- Precision@k: {r['evaluation']['precision_at_k']}")
        lines.append("- Top chunks:")
        for item in r["retrieved"]:
            meta = item["metadata"]
            lines.append(
                f"  - {item['chunk_id']} | alias={item['gabarito_alias']} | "
                f"doc={meta.get('doc_id')} | secao={meta.get('section')} | sim={item['similarity']}"
            )

    lines.append("")
    lines.append("## Analise de problemas observados")
    lines.append("1. Possivel mistura de versoes PROC-042 e PROC-042-v2 em perguntas de frete quando chunks antigos aparecem no top-k.")
    lines.append("2. FAQ informal pode subir no ranking para perguntas criticas e competir com documento normativo.")
    lines.append("3. Mapeamento de aliases por heuristica pode errar em secoes com conteudo muito amplo (ex.: SLA secao 2).")
    lines.append("")
    lines.append("## Propostas de correcao")
    lines.append("1. Aplicar re-ranking por metadado de vigencia para priorizar versao mais recente e filtrar versao antiga quando apropriado.")
    lines.append("2. Inserir peso de confiabilidade por tipo de fonte (formal > FAQ) no score final de retrieval.")
    lines.append("3. Ajustar chunking para separar tabelas de SLA em chunks menores por subtabela (chamados gerais vs incidentes criticos).")

    return "\n".join(lines)


def main() -> None:
    this_dir = Path(__file__).resolve().parent
    project_root = this_dir.parent
    persist_dir = this_dir / "chroma_db"

    test_file = this_dir / "data" / "test_cases.json"
    output_file = this_dir / "resultados-testes.md"

    cases = json.loads(test_file.read_text(encoding="utf-8"))

    pipeline = NovaTechRAGPipeline(project_root=project_root, persist_dir=persist_dir)

    if pipeline.collection.count() == 0:
        print("Colecao vazia. Executando ingestao...")
        summary = pipeline.ingest()
        print(json.dumps(summary, indent=2, ensure_ascii=False))

    results: List[Dict[str, Any]] = []
    for case in cases:
        question = case["question"]
        expected = case["expected_chunks"]
        retrieved = pipeline.search(question, top_k=5)
        aliases = [item["gabarito_alias"] for item in retrieved]
        evaluation = evaluate_case(aliases, expected)

        results.append(
            {
                "id": case["id"],
                "question": question,
                "expected": expected,
                "retrieved": retrieved,
                "retrieved_aliases": aliases,
                "evaluation": evaluation,
            }
        )

    report_md = render_markdown(results)
    output_file.write_text(report_md, encoding="utf-8")

    print(f"Relatorio gerado em: {output_file}")


if __name__ == "__main__":
    main()
