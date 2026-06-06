# Exercício 1.3 - Pipeline RAG (PoC)

Este diretório contém os artefatos solicitados para a tarefa 1.3 do papel Desenvolvedor.

## Arquivos

- `rag_pipeline.py`: pipeline mínimo com ingestão, chunking, embeddings, armazenamento no ChromaDB, busca semântica e montagem de prompt.
- `run_tests.py`: executa 5 perguntas do gabarito (Anexo B), compara chunks recuperados e gera relatório.
- `requirements.txt`: dependencias Python da PoC.
- `data/system_prompt.txt`: prompt base com guardrails.
- `data/test_cases.json`: perguntas de teste e chunks esperados.
- `resultados-testes.md`: relatório gerado após executar os testes.

Backend de embeddings:

- Padrão: `local-hash` (offline, sem download de modelo).
- Opcional: `sbert` com `sentence-transformers` (`all-MiniLM-L6-v2`).

## Estratégia de chunking adotada

- Chunking por seção de markdown (`##` / `###`) para preservar semântica do documento.
- Subdivisão por tamanho quando necessário: ~380 palavras por chunk com overlap de 60 palavras.
- Justificativa:
  - Perguntas de atendimento costumam mirar regras específicas por seção (prazo, exceções, SLA, multiplicadores).
  - Chunking por seção reduz risco de cortar regras no meio da resposta.
  - Overlap mitiga perda de contexto em fronteiras de chunk.

## Como executar

1. Criar ambiente virtual (opcional):

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

2. Instalar dependências:

```powershell
pip install -r requirements.txt
```

3. Ingerir documentos (Anexo A em arquivos markdown na raiz do workspace):

```powershell
python rag_pipeline.py ingest
```

Opcional (backend SBERT):

```powershell
pip install sentence-transformers
python rag_pipeline.py ingest --embedding-backend sbert
```

4. Testar retrieval com 5 perguntas do gabarito:

```powershell
python run_tests.py
```

5. Gerar prompt completo para usar no Claude manualmente:

```powershell
python rag_pipeline.py ask --question "Frete para 600kg para Manaus?" --top-k 5
```

## Como usar com Claude (manual)

1. Rode o comando `ask` para a pergunta desejada.
2. Copie o bloco `=== PROMPT MONTADO ===`.
3. Cole no Claude e avalie:
   - se a resposta está correta,
   - se citou fontes,
   - se respeitou os guardrails.

## Observações sobre o exercício

- O script de testes mede qualidade de retrieval (nao mede qualidade de geracao do LLM).
- O mapeamento para aliases do gabarito do Anexo B é heurístico.
- Para uso em produção, incluir re-ranking com metadados de vigência e confiabilidade de fonte.
