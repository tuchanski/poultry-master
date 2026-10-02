# Primeira rodada de melhorias — 01/10/2026

Não houve retreinamento nem alteração de `config.json` ou dos pesos. Foram usados os 80 recortes de saúde já vistos pelo classificador e as 171 imagens da **validação** do PIO. O teste reservado não foi consultado nesta rodada.

## 1. Recortes manuais versus automáticos

O classificador acertou o rótulo de origem em **79 dos 80 recortes manuais**: 39/40 `dead` e 40/40 `healthy`. Isso é diagnóstico sobre treino, não acurácia em imagens independentes.

Para comparar recortes da mesma ave, procuramos a detecção com maior sobreposição com a caixa revisada e exigimos IoU ≥ 0,5. Essa escolha usa a anotação manual e serve apenas ao diagnóstico; o programa real não dispõe dessa informação. Outras detecções da foto não recebem automaticamente o rótulo da ave revisada.

| Resolução do detector | Aves revisadas com caixa correspondente | Acertos manuais nesses casos | Acertos automáticos nesses casos |
| --- | ---: | ---: | ---: |
| 640 (atual) | 1/80 | 1/1 | 1/1 |
| 320 (experimental) | 61/80 | 60/61 | 60/61 |

Em 320, houve correspondência para 33/40 aves `dead` e 28/40 `healthy`. As demais não tiveram uma caixa com sobreposição suficiente; isso inclui detecções parciais, não apenas ausência total de caixas. A resolução 320 foi uma hipótese exploratória motivada pelo resultado inicial ruim e não foi avaliada em dados novos.

**Interpretação:** localizar a ave inteira nas fotos de saúde é um problema importante. Reduzir a resolução melhorou essa correspondência nos exemplos revisados, mas não resolveu os falsos positivos. O desempenho nos recortes conhecidos também não valida o classificador nos recortes diferentes do PIO.

Na inspeção do fluxo completo em 320:

- `mati_rgb_109.jpg`: as caixas passaram a envolver melhor as duas aves visíveis, mas ainda houve caixas no chão; total de 8 previsões.
- `sehat_rgb_10.jpg`: houve uma caixa correspondente à ave revisada, mas também dezenas de caixas em outras regiões; total de 64 previsões, 45 delas `dead`.

Por isso, **não adotamos 320 como configuração geral**. Correspondência melhor com a caixa revisada não equivale a contagem ou classificação global confiável. Essas duas fotos também foram usadas no treinamento.

## 2. Ajustes na validação do PIO

Comparadas seis combinações, com resolução 640 e limite de 1.500 caixas. A precisão e o recall abaixo usam pareamento guloso por confiança, sem repetir uma anotação, com IoU ≥ 0,5. São métricas nesse limiar fixo; não são AP nem o ponto selecionado pela avaliação anterior da Ultralytics.

| Confiança | IoU de NMS | Precisão | Recall | F1 | Erro absoluto médio de contagem |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0,25 | 0,70 — atual | 70,49% | 79,06% | 74,53% | 21,31 |
| 0,40 | 0,70 | 84,04% | 71,10% | 77,03% | 17,92 |
| 0,55 | 0,70 | 92,59% | 59,25% | 72,26% | 30,19 |
| 0,25 | 0,50 | 77,77% | 78,28% | 78,02% | **15,01** |
| 0,40 | 0,50 | 87,84% | 70,68% | **78,33%** | 18,12 |
| 0,55 | 0,50 | 93,93% | 59,16% | 72,59% | 30,87 |

A combinação **confiança 0,25 e NMS 0,50** é a candidata para melhorar contagem: erro absoluto médio caiu aproximadamente 29,6%, com recall 0,77 ponto percentual menor. O erro médio com sinal passou de +10,09 para +0,55 aves por imagem. Médias próximas de zero podem esconder erros que se compensam; por isso também usamos o erro absoluto.

O maior F1 ocorreu em confiança 0,40 e NMS 0,50, mas com mais aves perdidas e pior contagem. Aumentar a confiança indiscriminadamente não resolve os dois objetivos. Esses resultados foram selecionados na validação e ainda não constituem confirmação independente da melhoria.

## 3. Como experimentar sem perder a configuração atual

Dois arquivos novos, na raiz do projeto:

- `config.pio-ajustado.json`: confiança 0,25, NMS 0,50, resolução 640. Candidato selecionado por contagem na validação PIO.
- `config.fotos-proximas-experimental.json`: resolução 320, confiança 0,25 e NMS 0,70. Somente para investigar as fotos de saúde; ainda apresenta muitos falsos positivos.

```powershell
.venv/Scripts/python.exe analyze.py --config config.pio-ajustado.json --image "caminho/para/foto.jpg" --output outputs/experimento-pio-01
```

Substitua o caminho pela foto desejada e use pasta nova. Não escolha fotos do teste reservado para continuar ajustando parâmetros. Nenhum dos arquivos muda os pesos. Para voltar ao comportamento original, execute `analyze.py` sem `--config`.

## 4. Reprodução e artefatos

```powershell
.venv/Scripts/python.exe scripts/diagnose_models.py --output outputs/diagnosis/round-02
.venv/Scripts/python.exe scripts/diagnose_models.py --health-only --health-imgsz 320 --output outputs/diagnosis/health-320-v2
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

GPU 0 é o padrão do diagnóstico; `--device cpu` permite CPU. Os comandos exigem pastas novas. Resultados desta rodada:

- `outputs/diagnosis/round-01`: comparações de recortes, grade completa, contagens por imagem e hashes dos modelos e manifestos.
- `outputs/diagnosis/health-320`: comparação dos recortes em resolução 320.
- `outputs/diagnosis/demo-health-320-dead` e `demo-health-320-healthy`: imagens anotadas e relatórios completos inspecionados.

Os 19 testes passaram, incluindo pareamento sem duplicar a mesma ave, caixas parciais e listas vazias. Não foram alterados rótulos, decisões manuais, pesos ou resultados anteriores.

## 5. Próximo trabalho indicado pelos resultados

Para melhorar as fotos de saúde, precisamos adaptar o detector a esse tipo de enquadramento. As caixas atuais marcam somente uma ave por foto; não devem ser convertidas diretamente em um dataset de detecção completo quando existem outras aves sem anotação. É preciso revisar **todas as aves** das fotos escolhidas e incluir exemplos de fundo sem aves quando apropriado.

Para o classificador, obter recortes representativos das fotos de granja com rótulo individual confiável, incluindo animais saudáveis descansando e exemplos confirmados de `dead`. Separar grupos reais antes de treinamento e avaliação. Os 80 exemplos atuais não permitem demonstrar generalização simplesmente treinando por mais épocas.

A primeira rodada trouxe uma configuração candidata para o PIO e evidência de que as caixas nas fotos de saúde são um gargalo. Não demonstra que a classificação de mortalidade ficou confiável.
