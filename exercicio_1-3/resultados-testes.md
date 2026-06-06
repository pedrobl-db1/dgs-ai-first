# Resultados de Teste - Exercicio 1.3

## Resumo
- Casos executados: 5
- Recall medio: 0.300
- Precision@k media: 0.080

## Casos

### TC-01 - Qual o prazo de devolucao?
- Esperado (gabarito): POL-001-A, POL-001-B
- Recuperado (aliases): PROC-042-C, PROC-042v2-C, UNMAPPED, SLA-2024-C, PROC-042v2-D
- Matched: nenhum
- Missing: POL-001-A, POL-001-B
- Recall: 0.0
- Precision@k: 0.0
- Top chunks:
  - PROC-042__S05__C01 | alias=PROC-042-C | doc=PROC-042 | secao=3. Prazo de entrega para frete especial | sim=0.4104
  - PROC-042-v2__S05__C01 | alias=PROC-042v2-C | doc=PROC-042-v2 | secao=3. Prazo de entrega para frete especial | sim=0.3974
  - POL-001__S01__C01 | alias=UNMAPPED | doc=POL-001 | secao=intro | sim=0.3919
  - SLA-2024__S03__C01 | alias=SLA-2024-C | doc=SLA-2024 | secao=2. Tabela de SLAs | sim=0.3917
  - PROC-042-v2__S06__C01 | alias=PROC-042v2-D | doc=PROC-042-v2 | secao=4. Condições especiais | sim=0.3902

### TC-02 - Posso devolver carga perigosa?
- Esperado (gabarito): POL-001-B
- Recuperado (aliases): UNMAPPED, POL-001-A, UNMAPPED, POL-001-D, PROC-042-C
- Matched: nenhum
- Missing: POL-001-B
- Recall: 0.0
- Precision@k: 0.0
- Top chunks:
  - SLA-2024__S04__C01 | alias=UNMAPPED | doc=SLA-2024 | secao=3. Definição de incidente crítico | sim=0.3613
  - POL-001__S06__C01 | alias=POL-001-A | doc=POL-001 | secao=3.2. Exceções ao prazo geral | sim=0.356
  - POL-001__S03__C01 | alias=UNMAPPED | doc=POL-001 | secao=2. Escopo | sim=0.3549
  - POL-001__S09__C01 | alias=POL-001-D | doc=POL-001 | secao=3.5. Custos de devolução | sim=0.3546
  - PROC-042__S05__C01 | alias=PROC-042-C | doc=PROC-042 | secao=3. Prazo de entrega para frete especial | sim=0.3463

### TC-03 - Qual o SLA do cliente Gold?
- Esperado (gabarito): SLA-2024-B
- Recuperado (aliases): POL-001-D, UNMAPPED, POL-001-C, UNMAPPED, POL-001-A
- Matched: nenhum
- Missing: SLA-2024-B
- Recall: 0.0
- Precision@k: 0.0
- Top chunks:
  - POL-001__S09__C01 | alias=POL-001-D | doc=POL-001 | secao=3.5. Custos de devolução | sim=0.4046
  - SLA-2024__S06__C01 | alias=UNMAPPED | doc=SLA-2024 | secao=5. Medição e reportes | sim=0.3827
  - POL-001__S07__C01 | alias=POL-001-C | doc=POL-001 | secao=3.3. Procedimento de devolução | sim=0.3789
  - SLA-2024__S01__C01 | alias=UNMAPPED | doc=SLA-2024 | secao=intro | sim=0.368
  - POL-001__S06__C01 | alias=POL-001-A | doc=POL-001 | secao=3.2. Exceções ao prazo geral | sim=0.3663

### TC-04 - Frete para 600kg para Manaus?
- Esperado (gabarito): PROC-042v2-B, PROC-042v2-A
- Recuperado (aliases): PROC-042-C, POL-001-D, UNMAPPED, PROC-042v2-C, PROC-042v2-A
- Matched: PROC-042v2-A
- Missing: PROC-042v2-B
- Recall: 0.5
- Precision@k: 0.2
- Top chunks:
  - PROC-042__S05__C01 | alias=PROC-042-C | doc=PROC-042 | secao=3. Prazo de entrega para frete especial | sim=0.3921
  - POL-001__S09__C01 | alias=POL-001-D | doc=POL-001 | secao=3.5. Custos de devolução | sim=0.3892
  - FAQ__S11__C01 | alias=UNMAPPED | doc=FAQ | secao=Item 45 — "O cliente quer desconto no frete. Posso dar?" | sim=0.3873
  - PROC-042-v2__S05__C01 | alias=PROC-042v2-C | doc=PROC-042-v2 | secao=3. Prazo de entrega para frete especial | sim=0.3826
  - PROC-042-v2__S03__C01 | alias=PROC-042v2-A | doc=PROC-042-v2 | secao=2. Fórmula de cálculo | sim=0.3813

### TC-05 - Qual o multiplicador para o Sudeste?
- Esperado (gabarito): PROC-042v2-B
- Recuperado (aliases): PROC-042-C, PROC-042-B, PROC-042v2-B, PROC-042v2-C, PROC-042-A
- Matched: PROC-042v2-B
- Missing: nenhum
- Recall: 1.0
- Precision@k: 0.2
- Top chunks:
  - PROC-042__S05__C01 | alias=PROC-042-C | doc=PROC-042 | secao=3. Prazo de entrega para frete especial | sim=0.3923
  - PROC-042__S04__C01 | alias=PROC-042-B | doc=PROC-042 | secao=2.1. Multiplicadores regionais | sim=0.3832
  - PROC-042-v2__S04__C01 | alias=PROC-042v2-B | doc=PROC-042-v2 | secao=2.1. Multiplicadores regionais (atualizados em novembro/2023) | sim=0.3832
  - PROC-042-v2__S05__C01 | alias=PROC-042v2-C | doc=PROC-042-v2 | secao=3. Prazo de entrega para frete especial | sim=0.3827
  - PROC-042__S03__C01 | alias=PROC-042-A | doc=PROC-042 | secao=2. Fórmula de cálculo | sim=0.3653

## Analise de problemas observados
1. Possivel mistura de versoes PROC-042 e PROC-042-v2 em perguntas de frete quando chunks antigos aparecem no top-k.
2. FAQ informal pode subir no ranking para perguntas criticas e competir com documento normativo.
3. Mapeamento de aliases por heuristica pode errar em secoes com conteudo muito amplo (ex.: SLA secao 2).

## Propostas de correcao
1. Aplicar re-ranking por metadado de vigencia para priorizar versao mais recente e filtrar versao antiga quando apropriado.
2. Inserir peso de confiabilidade por tipo de fonte (formal > FAQ) no score final de retrieval.
3. Ajustar chunking para separar tabelas de SLA em chunks menores por subtabela (chamados gerais vs incidentes criticos).
