# Fluxo atual do MVP sequencial de monitoramento

**Registro de trabalho — 20 de outubro de 2026**

Este documento explica, em linguagem direta, o fluxo implementado até agora, os termos usados e a configuração que estamos usando como referência. O objetivo é sinalizar situações que merecem atenção humana; o sistema ainda não confirma se uma ave morreu.

## Origem das imagens

As imagens foram coletadas por **Guilherme Tuchanski Rocha na granja do pai**. A coleta foi feita com a câmera fixa, em capturas aproximadamente a cada 30 segundos. Os arquivos ficam no computador em `Desktop/granja2`; esse caminho é local e não faz parte do repositório.

O nome dos arquivos segue o padrão `screenshot_<timestamp_em_milissegundos>_<contador>.png`. O programa lê o horário do nome, organiza as fotos em ordem cronológica e ignora arquivos que não seguem esse padrão.

Na análise registrada em `outputs/granja2-roi-06-review-7min/`, foram processadas 297 imagens, entre aproximadamente 9h08 e 11h38 no horário de São Paulo. A mediana do intervalo foi de 30 segundos; houve uma lacuna máxima de 90 segundos. A sequência não contém todos os números de captura, então o total processado foi 297, embora o lote tenha sido descrito como cerca de 300 imagens.

Um lote anterior foi afetado por um pop-up que esbranquiçou as imagens. A nova coleta deve ser conferida visualmente para garantir iluminação e enquadramento estáveis antes de ser usada como validação.

## Fluxo de processamento

```text
Fotos e horários
      ↓
Ordenação cronológica
      ↓
Detector de aves já treinado
      ↓
Filtro da região de interesse (ROI)
      ↓
Associação das caixas entre capturas
      ↓
Estimativa de movimento e tempo aparente parado
      ↓
Candidato de imobilidade para revisão humana
      ↓
Imagens anotadas + tracks.csv + report.json
```

### 1. Detecção

O detector existente localiza aves e produz uma **bounding box** para cada detecção. Bounding box é o retângulo que delimita a ave na imagem. O detector analisa cada foto de forma independente; ele não sabe, sozinho, se uma caixa na próxima foto representa a mesma ave.

O classificador `healthy/dead` não é usado neste fluxo sequencial. O resultado temporal é baseado em imobilidade aparente, e não em uma classificação de óbito.

### 2. Região de interesse (ROI)

ROI significa *Region of Interest*, ou **região de interesse**. É a parte da imagem que queremos considerar para a análise temporal.

A ROI atual é `0,0.60,1,1`. As coordenadas são normalizadas de 0 a 1 na ordem `x1,y1,x2,y2`: ela cobre toda a largura (`x=0` a `x=1`) e a faixa dos 60% até a base (`y=0.60` a `y=1`). Portanto, o rastreamento considera os 40% inferiores da imagem, onde as aves aparecem maiores e mais visíveis.

O detector ainda processa a imagem inteira. Depois da detecção, o programa mantém somente caixas cujo **centro** esteja dentro da ROI. Assim, o recorte reduz quais detecções entram no rastreamento; ele não altera a foto original nem o modelo detector.

### 3. Associação e movimento

O programa tenta associar cada caixa a uma caixa de uma captura próxima, usando distância entre centros e sobreposição dos retângulos. Quando consegue, atribui um ID temporário e forma uma **trajetória**.

O ID não identifica biologicamente uma ave. Em uma cena densa, o rastreador pode perder uma caixa, trocar a associação para uma ave vizinha ou criar outra trajetória para a mesma ave. Por isso, “mesma trajetória” é uma estimativa computacional de que se trata da mesma ave, não uma garantia.

O movimento é calculado pela mudança do centro da caixa, normalizada pela diagonal da caixa anterior. Para a configuração atual, uma mudança de até `0.15` diagonais é tratada como pouca movimentação entre observações.

### 4. Candidato de imobilidade

Quando uma trajetória acumula o tempo configurado com pouca movimentação, ela passa ao estado `stationary_candidate` (**candidato de imobilidade**). O critério atual é **7 minutos**, com pelo menos quatro observações estacionárias. O tempo creditado por intervalo é limitado a 30 segundos, mesmo se uma captura chegar atrasada.

Esse estado significa apenas que a caixa associada à trajetória pareceu pouco móvel nas fotos disponíveis. A ave pode estar dormindo, a caixa pode ter sido associada incorretamente, ou pode ter ocorrido movimento entre duas fotos. O alerta precisa de verificação humana e não confirma óbito.

## Configuração de referência

Os valores abaixo descrevem a última análise de `granja2`. Alguns vêm de `config.json`; os parâmetros temporais e a ROI são informados ao comando.

| Item | Valor atual | Significado |
|---|---:|---|
| Entrada | `Desktop/granja2` | Pasta local com as capturas do usuário |
| Dispositivo | CPU | Execução do detector na CPU |
| Tamanho de inferência | 640 px | Tamanho de entrada usado pelo detector |
| Confiança mínima | 0,25 | Limiar do detector para aceitar uma caixa |
| IoU do detector | 0,70 | Limiar de sobreposição usado na supressão de caixas duplicadas pelo detector |
| Máximo por imagem | 1.500 caixas | Limite de detecções por captura |
| ROI | `0,0.60,1,1` | Toda a largura e os 40% inferiores da imagem |
| Intervalo nominal | 30 s | Crédito máximo de tempo entre observações associadas |
| Pouco movimento | até 0,15 diagonais | Limite de movimento do centro da caixa entre duas observações |
| Limite temporal | 7 min | Duração para passar a candidato nesta execução |
| Observações mínimas | 4 | Mínimo de observações com pouco movimento |
| Distância máxima para associação | 0,75 diagonais | Limite de distância entre centros para considerar uma associação |
| Sobreposição mínima alternativa | IoU 0,05 | Sobreposição que também pode permitir associação |
| Capturas ausentes toleradas | 1 | Quantidade de quadros perdidos tolerada antes de encerrar uma trajetória |
| Pausa para nova sessão | 3 min | Pausas maiores separam blocos e não conectam trajetórias entre eles |
| Visualização | somente candidatos, sem rótulos | Muda as imagens anotadas; não muda a análise nem as contagens |

O valor de `0.70` acima é o IoU usado pelo detector. O `0.05` é outro IoU, usado pelo associador de trajetórias; eles têm funções diferentes.

## Resultado da última execução

Com ROI de 60% e limiar de 7 minutos, o relatório registrou:

- 297 fotos processadas;
- 155.001 detecções antes do filtro da ROI e 96.494 depois;
- 7.711 trajetórias criadas;
- 17 trajetórias com evento candidato e 17 eventos candidatos;
- 7.305 trajetórias encerradas como perdidas.

No mesmo lote, 5 minutos produziram 103 trajetórias candidatas e 104 eventos; 10 minutos não produziram candidatos. Sete minutos é, portanto, o **limiar provisório de trabalho** que gerou um volume menor para revisão. Essa comparação não prova que 7 minutos seja o valor ideal: precisamos verificar visualmente se os candidatos correspondem a aves reais acompanhadas de forma contínua.

Os arquivos estão em `outputs/granja2-roi-06-review-7min/`:

- `frames/`: imagens anotadas. Com `--candidates-only`, só aparecem caixas que já atingiram o estado candidato; com `--hide-labels`, os textos ficam ocultos.
- `tracks.csv`: observações por imagem, com ID temporário, coordenadas, confiança, movimento, tempo estacionário e estado.
- `report.json`: parâmetros, horários, resumo e lista das trajetórias e eventos.

## Comando usado

```bash
.venv/bin/python analyze_sequence.py \
  --images-dir "/Users/tuchanski/Desktop/granja2" \
  --output "outputs/granja2-roi-06-review-7min" \
  --device cpu \
  --roi 0,0.60,1,1 \
  --stationary-minutes 7 \
  --candidates-only \
  --hide-labels
```

## Próximas verificações

1. Conferir se a iluminação e o enquadramento permanecem estáveis nas novas capturas.
2. Abrir as imagens próximas aos 17 eventos e verificar se cada caixa continua sobre a mesma ave.
3. Conferir no `tracks.csv` quando cada trajetória começou, quando foi perdida e por quanto tempo acumulou pouca movimentação.
4. Manter 7 minutos como configuração experimental até fazer essa revisão. Se a associação trocar de ave ou se perder, o resultado temporal ainda não é confiável para alertas automáticos.

## Glossário

- **Detecção:** caixa que o modelo localizou em uma foto.
- **Bounding box:** retângulo em torno de uma detecção.
- **ROI:** região da imagem incluída na análise temporal.
- **Trajetória:** sequência de caixas associadas pelo programa e identificadas por um ID temporário.
- **Imobilidade aparente:** pouca mudança observada entre as caixas ao longo das fotos; não significa ausência completa de movimento.
- **Candidato:** trajetória que ultrapassou o tempo configurado e precisa de revisão humana.
- **IoU:** medida da sobreposição entre duas caixas; varia de 0 (sem sobreposição) a 1 (sobreposição total).
