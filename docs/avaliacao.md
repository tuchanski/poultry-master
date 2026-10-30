# Avaliação do detector PIO

O detector foi avaliado no teste reservado do PIO. Essas métricas não validam o acompanhamento sequencial nem a regra de imobilidade aparente.

## Detector no teste reservado

Avaliação em 01/10/2026, com os pesos existentes, sem retreinamento ou ajuste pelo teste. Foram utilizadas 188 imagens com 45.337 caixas anotadas, separadas por grupos conhecidos e hashes na preparação. Essa separação não comprova independência entre animais nem elimina possíveis imagens quase iguais.

| Métrica | Resultado |
| --- | ---: |
| Precisão | 90,40% |
| Recall | 86,08% |
| mAP@50 | 93,41% |
| mAP@50–95 | 62,35% |

Entrada 640, IoU de NMS 0,7, máximo de 1.500 detecções, lote de avaliação 8 e confiança mínima 0,001 para construir as curvas de avaliação. A precisão e o recall reportados pela biblioteca correspondem ao ponto escolhido na curva, não necessariamente ao limiar 0,25 usado na aplicação. Esses valores medem apenas a detecção nas imagens PIO.

A contagem foi medida separadamente com confiança 0,25, fixada antes do teste:

| Medida de contagem | Resultado |
| --- | ---: |
| Total anotado | 45.337 |
| Total detectado | 52.821 |
| Erro absoluto médio por imagem | 39,85 aves |
| Erro médio com sinal (detectado − anotado) | +39,81 aves |
| Imagens que atingiram o limite de detecções | 0 |

A tendência é superestimar a contagem. O pior caso foi `C-W3-0011.jpg`: 446 detecções para 305 caixas anotadas, diferença de 141. A inspeção de cenas densas mostrou caixas sobrepostas e regiões ambíguas; o erro de contagem sozinho não distingue falsos positivos de falsos negativos que se compensam.

Execução em Windows 11, RTX 4070 Ti SUPER, PyTorch 2.8.0+cu128 e Ultralytics 8.3.203. A avaliação e a passagem de contagem levaram 22,797 segundos, excluindo o carregamento inicial do modelo.

Reprodução, a partir da raiz do projeto:

```powershell
.venv/Scripts/python.exe scripts/evaluate.py --device 0 --output outputs/evaluation/detector-test-v2
```

Também aceita `--device cpu`. A saída precisa ser nova. O script salva `summary.json`, `counts.csv` e gráficos e exemplos da biblioteca em `validation/`. Apesar do nome desse subdiretório, o conjunto solicitado é explicitamente **test**. Os resultados originais estão em `outputs/evaluation/detector-test`. Variações numéricas entre CPU/GPU podem alterar caixas próximas aos limiares; não ajustar parâmetros repetidamente nesse teste.

## Validação sequencial

Os testes automatizados exercitam associação, tempo creditado entre observações,
perda de trajetórias, novas sessões e geração dos resultados com detecções
controladas. Não medem desempenho em granja real.

Para avaliar o fluxo em campo, revise a correspondência das caixas nas capturas,
os eventos em `report.json` e as observações em `tracks.csv`. Um candidato
representa imobilidade aparente e exige verificação humana.
