# Análise de fotos sequenciais

O comando `analyze_sequence.py` processa fotos da mesma câmera em ordem temporal, reaproveita o detector já configurado e associa caixas entre capturas. O classificador `healthy/dead` não é usado para emitir candidatos. Ele aceita um CSV com timestamps ou, para as capturas atuais, uma pasta com nomes no padrão `screenshot_<timestamp_ms>_<contador>.png`.

## Usar a pasta de capturas atual

Os nomes `screenshot_1792451738112_1.png` contêm o horário Unix em milissegundos e um contador da captura. Passe a pasta diretamente; não precisa criar o CSV. Para fotos a cada 30 segundos, esse é o intervalo padrão:

```bash
.venv/bin/python analyze_sequence.py --images-dir "/Users/tuchanski/Desktop/granja" --output "outputs/granja-001" --device cpu
```

O programa extrai os horários dos nomes e ordena as imagens. Os timestamps são interpretados como instantes UTC; a ordem temporal continua correta independentemente do fuso local. Capturas fora do padrão são ignoradas. Pausas superiores a três minutos iniciam sessões novas, sem associar trajetórias entre blocos.

Uma execução curta serve para conferir o formato e a ordem das imagens. Para avaliar candidatos com o limiar padrão de cinco minutos, capture por mais tempo e mantenha iluminação e enquadramento estáveis.

## Preparar o manifesto

Crie um CSV UTF-8 com as colunas `image` e `timestamp`. O horário deve ser ISO 8601 com fuso; caminhos relativos são resolvidos a partir da pasta do CSV.

```csv
image,timestamp
frames/frame-001.jpg,2026-10-19T10:00:00-03:00
frames/frame-002.jpg,2026-10-19T10:01:00-03:00
frames/frame-003.jpg,2026-10-19T10:02:00-03:00
```

Use fotos do mesmo enquadramento e resolução. O programa ordena as linhas pelo horário e rejeita horários repetidos, imagens ausentes, dimensões diferentes e horários sem fuso.

## Executar

No Windows:

```powershell
.venv/Scripts/python.exe analyze_sequence.py --manifest "data/sequencia/sequence.csv" --output "outputs/sequencia-001"
```

No macOS:

```bash
.venv/bin/python analyze_sequence.py --manifest "data/sequencia/sequence.csv" --output "outputs/sequencia-001" --device cpu
```

A pasta de saída precisa ser nova. O detector é carregado de `config.json`; pesos e metadados correspondentes precisam estar em `models/`.

Para focar as aves mais próximas nesta câmera, a região de trabalho escolhida começa em 60% da altura e vai até a borda inferior. O comando abaixo também gera imagens mais limpas para revisão, mostrando apenas caixas candidatas e ocultando os rótulos:

```bash
.venv/bin/python analyze_sequence.py --images-dir "/Users/tuchanski/Desktop/granja" --output "outputs/granja-revisao" --device cpu --roi 0,0.60,1,1 --candidates-only --hide-labels
```

O ROI é opcional e usa coordenadas normalizadas em relação à imagem completa (`x1,y1,x2,y2`). Uma caixa entra se seu centro estiver dentro da região. Ajuste o limite se quiser acompanhar aves em outra parte da imagem. As opções de visualização alteram somente as imagens anotadas, não as detecções, trajetórias ou contagens.

## Parâmetros temporais

- `--stationary-minutes`: duração aparente mínima antes de sinalizar; padrão `5`.
- `--nominal-interval-seconds`: crédito máximo por observação; padrão `30`.
- `--session-gap-minutes`: pausa que inicia uma nova sessão; padrão `3`.
- `--confidence`: substitui o limiar de confiança do detector definido em `config.json`.
- `--roi`: filtra detecções pelo centro da caixa dentro de uma região normalizada; padrão sem recorte.
- `--candidates-only`: nas imagens anotadas, desenha somente as caixas no estado de candidato.
- `--hide-labels`: nas imagens anotadas, oculta os textos sobre as caixas.
- `--motion-threshold-diagonals`: movimento normalizado máximo para considerar observação estacionária; padrão `0.15`.
- `--max-center-distance-diagonals`: distância máxima padrão para associação de caixas.
- `--association-min-iou`: sobreposição mínima alternativa para associação; padrão `0.05`.
- `--max-missed-frames`: capturas ausentes toleradas antes de encerrar a trajetória; padrão `1`.
- `--minimum-stationary-observations`: mínimo de observações estacionárias; padrão `4`.

Esses valores são parâmetros iniciais de demonstração, não foram validados em granja. O horário real do manifesto determina o tempo decorrido; o crédito por intervalo é limitado pelo intervalo nominal para que uma foto ausente não conte como vários minutos de imobilidade.

## Arquivos gerados

- `frames/`: fotos anotadas; por padrão mostram todas as caixas e rótulos. As opções de visualização podem restringir a exibição a candidatos e ocultar os rótulos.
- `tracks.csv`: uma linha por observação, incluindo caixa, confiança, movimento normalizado, duração acumulada e estado.
- `report.json`: parâmetros, versão/hash do detector, ordem das fotos, resumo e eventos candidatos.

`stationary_candidate` significa somente que a trajetória apresentou pouca movimentação nas observações disponíveis. `lost` significa que a detecção não foi reencontrada dentro da tolerância; não indica imobilidade. Uma previsão candidata exige verificação humana e não confirma óbito. Câmera móvel, aves sobrepostas, oscilações do detector e movimentos que ocorram entre capturas podem gerar erros.
