# Avaliação e demonstração do MVP

O fluxo funcional está implementado: imagem → detecção → recortes → classificação binária → imagem anotada e JSON. Os resultados atuais **não validam o uso operacional para identificar mortalidade**. A detecção foi avaliada no teste reservado do PIO; a avaliação independente do classificador continua pendente.

## Detector no teste reservado

Avaliação em 01/10/2026, com os pesos existentes, sem retreinamento ou ajuste pelo teste. Foram utilizadas 188 imagens com 45.337 caixas anotadas, separadas por grupos conhecidos e hashes na preparação. Essa separação não comprova independência entre animais nem elimina possíveis imagens quase iguais.

| Métrica | Resultado |
| --- | ---: |
| Precisão | 90,40% |
| Recall | 86,08% |
| mAP@50 | 93,41% |
| mAP@50–95 | 62,35% |

Entrada 640, IoU de NMS 0,7, máximo de 1.500 detecções, lote de avaliação 8 e confiança mínima 0,001 para construir as curvas de avaliação. A precisão e o recall reportados pela biblioteca correspondem ao ponto escolhido na curva, não necessariamente ao limiar 0,25 usado na aplicação. Não usar esses valores como acurácia do classificador ou como desempenho integrado.

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

## Classificador e identificação de mortalidade

Os 80 recortes aprovados foram usados no treino demonstrativo, sem grupos de captura conhecidos. Não existe teste independente revisado para calcular acurácia, recall/F1 de `dead` ou matriz de confusão do classificador. Esses números não foram calculados sobre o treino para substituir a avaliação ausente.

Nas fotos do PIO não existem rótulos individuais `healthy`/`dead`. A demonstração integrada é qualitativa: há muitas previsões `dead`, mas não podemos quantificar os falsos positivos ou confirmar óbitos. Também não há base anotada suficiente para contar aves mortas que o detector deixou de encontrar. Portanto, a identificação integrada de mortalidade permanece **não validada**.

## Roteiro de demonstração

Siga o [guia de preparação](preparacao-dados.md) para instalar o ambiente e obter os datasets. O [guia de treinamento](treinamento.md) descreve os checkpoints e os dois treinamentos. Pesos, dados e decisões manuais não são versionados no Git: preserve os CSVs de revisão e os pesos com seus metadados. Um clone novo não contém os modelos ajustados nem as aprovações manuais.

Com os pesos existentes neste workspace:

```powershell
.venv/Scripts/python.exe scripts/check_environment.py
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe analyze.py --image data/prepared/pio/images/test/C-W3-0001.jpg --output outputs/minha-demo-final
```

Abra `annotated.jpg` e `report.json` na pasta escolhida. Mostre os identificadores, caixas, confidências separadas, contagens, versões dos modelos e aviso de verificação humana. Esta foto pertence ao teste do detector e não tem rótulos individuais de saúde. Não apresentá-la como validação do classificador.

A execução registrada em `outputs/demo-final-test` levou **4,453 segundos em CPU AMD Ryzen 7 5700X3D**, para uma foto de 1920×1080: 344 caixas, 106 previsões `healthy` e 238 `dead`. O tempo inclui carregamento dos pesos, inferência e gravação da imagem; é uma medição única, não um benchmark. Na passagem separada em GPU, a contagem foi 343; ambas superestimaram as 303 anotações. Há sobreposição de textos em cenas densas; o JSON permite consultar cada resultado. As 238 previsões não significam 238 aves mortas.

Como segundo exemplo, o [guia de análise](analise.md) usa uma foto de saúde vista no treinamento. Ela demonstra a execução, mas contém falsos positivos de detecção no chão e recortes parciais. Esses erros não devem ser omitidos na apresentação.

## Situação da entrega

Os 16 testes automatizados passaram. Foram conferidos os fluxos reais, resumo coerente, preservação da imagem original, ausência de detecções, recortes nas bordas, associação das classes, falhas de classificação, entrada inválida, pesos ausentes e pasta de saída existente.

O MVP está concluído como **demonstração funcional de dois modelos**, conforme o escopo que admite avaliação independente pendente. Para avançar além disso, obter imagens e rótulos individuais representativos da granja, identificar grupos de captura, revisar erros do detector e treinar/avaliar o classificador com separação independente. Novos ajustes precisam de validação própria; o teste já utilizado não deve virar conjunto de seleção de parâmetros.
