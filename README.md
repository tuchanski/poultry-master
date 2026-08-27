# poultry-master

## Aplicação de visão computacional na detecção de aves potencialmente mortas em granjas avícolas

## 1. Stakeholders prioritários

Os principais stakeholders do projeto são:

- Produtores e proprietários de granjas avícolas, que precisam acompanhar a mortalidade das aves.
- Funcionários responsáveis pelo manejo e inspeção das aves, que atualmente precisam identificar manualmente animais mortos.
- Gestores da produção, que podem utilizar os registros para acompanhar ocorrências de mortalidade dentro da granja.

O stakeholder prioritário será o produtor ou funcionário responsável pelo monitoramento das aves.

## 2. Necessidades principais

As principais necessidades identificadas são:

- Identificar aves potencialmente mortas com maior rapidez.
- Reduzir a dependência exclusiva de inspeções manuais.
- Facilitar o monitoramento de uma determinada área da granja.
- Registrar automaticamente possíveis ocorrências.
- Fornecer uma forma simples de verificar onde e quando uma possível ave morta foi identificada.

## 3. Escopo

O projeto irá:

- Utilizar uma câmera fixa para monitorar uma área específica da granja.
- Coletar imagens reais das aves.
- Criar e rotular um dataset próprio.
- Treinar um modelo de visão computacional, como o YOLO.
- Identificar aves em situações visualmente compatíveis com mortalidade.
- Registrar as detecções realizadas pelo modelo.
- Avaliar o desempenho utilizando métricas como precisão, recall, F1-score e mAP.

## 4. Fora do escopo

Nesta primeira versão, o projeto não irá:

- Monitorar toda a granja.
- Utilizar múltiplas câmeras.
- Utilizar sensores de temperatura, umidade ou outros sensores ambientais.
- Prever futuras mortes com base em condições ambientais.
- Desenvolver um segundo modelo de machine learning.
- Realizar diagnóstico veterinário.
- Garantir que uma ave está realmente morta apenas pela imagem.
- Automatizar a retirada das aves.
- Desenvolver uma solução comercial completa.

O objetivo é desenvolver uma prova de conceito de detecção visual.

## 5. Requisitos funcionais

- **RF01 — Captura de imagens:** receber imagens provenientes de uma câmera posicionada na área monitorada.
- **RF02 — Detecção de aves:** identificar aves presentes nas imagens.
- **RF03 — Identificação de possíveis aves mortas:** classificar ou detectar aves que apresentem características visuais compatíveis com mortalidade.
- **RF04 — Registro da ocorrência:** registrar quando uma possível ave morta for identificada.
- **RF05 — Indicação visual:** indicar na imagem onde a ave potencialmente morta foi localizada.
- **RF06 — Armazenamento de informações:** armazenar informações básicas da detecção, como data, horário e resultado obtido pelo modelo.

## 6. Requisitos não funcionais

- **RNF01 — Precisão:** apresentar desempenho suficiente para demonstrar a viabilidade da solução.
- **RNF02 — Facilidade de uso:** apresentar os resultados de forma simples e compreensível.
- **RNF03 — Desempenho:** analisar uma imagem em tempo adequado para permitir o monitoramento frequente da área.
- **RNF04 — Confiabilidade:** associar um nível de confiança às detecções realizadas.
- **RNF05 — Privacidade:** utilizar e armazenar as imagens somente para os objetivos definidos pelo projeto.
- **RNF06 — Reprodutibilidade:** documentar o treinamento e os testes para que os resultados possam ser reproduzidos.

## 7. Critérios de aceitação

O projeto será considerado funcional quando:

- A câmera conseguir capturar imagens adequadas da área escolhida.
- Existir um dataset com imagens rotuladas de aves.
- O modelo conseguir executar a detecção em imagens que não participaram do treinamento.
- O sistema conseguir indicar visualmente uma possível ave morta.
- As ocorrências puderem ser registradas.
- O modelo apresentar métricas de desempenho mensuráveis.
- Os resultados permitirem avaliar se a utilização de visão computacional é viável nesse contexto.

Como o projeto ainda está no início, não é necessário definir agora uma precisão mínima arbitrária, como 90%. O próprio experimento servirá para descobrir qual desempenho é possível obter.

## 8. Priorização do MVP

### Essencial

- Definir uma área da granja para monitoramento.
- Instalar ou utilizar uma câmera fixa.
- Coletar imagens.
- Criar e rotular o dataset.
- Treinar o modelo YOLO.
- Detectar aves potencialmente mortas.
- Avaliar as métricas do modelo.

### Desejável caso haja tempo

- Salvar automaticamente as detecções.
- Criar uma interface simples.
- Apresentar histórico de ocorrências.
- Gerar um alerta quando houver uma detecção.

### Fora do MVP

- Várias câmeras.
- Aplicativo mobile.
- Sensores ambientais.
- Previsão de mortalidade.
- Monitoramento completo da granja.
- Automação física.

## 9. Dúvidas que ainda precisam de validação externa

Alguns pontos ainda precisam ser validados com produtores, funcionários da granja e/ou literatura científica:

- Qual é o melhor local para posicionar a câmera?
- Qual tamanho de área uma única câmera consegue monitorar adequadamente?
- Existem diferenças visuais suficientes entre uma ave morta e uma ave apenas deitada ou descansando?
- Com que frequência ocorrem mortes na área escolhida?
- Será possível obter imagens suficientes de aves mortas para criar o dataset?
- A iluminação da granja permite utilizar uma câmera convencional ou será necessária uma câmera com infravermelho?
- Qual resolução e ângulo de câmera são mais adequados?
- Quanto tempo normalmente leva para um funcionário identificar uma ave morta atualmente?
- Qual taxa de falsos positivos seria aceitável para que o sistema seja útil na prática?

## Resultado esperado

Ao final dessa primeira etapa, o projeto deixa de ser apenas a ideia de “usar IA para identificar aves mortas” e passa a ter um objetivo testável:

> Desenvolver e avaliar um sistema de visão computacional capaz de utilizar imagens de uma área delimitada de uma granja para identificar aves potencialmente mortas, verificando a viabilidade da solução por meio de métricas de desempenho do modelo.