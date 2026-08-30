# 🐔 poultry-master

## Aplicação de visão computacional na detecção de aves potencialmente mortas em granjas avícolas

## 1. Stakeholders prioritários

Os principais stakeholders do projeto são:

* Produtores e proprietários de granjas avícolas, que precisam acompanhar a mortalidade das aves.
* Funcionários responsáveis pelo manejo e inspeção das aves, que atualmente precisam identificar manualmente animais mortos.
* Gestores da produção, que podem utilizar os registros para acompanhar ocorrências de mortalidade dentro da granja.

O stakeholder prioritário será o produtor ou funcionário responsável pelo monitoramento das aves.

## 2. Necessidades principais

As principais necessidades identificadas são:

* Identificar aves potencialmente mortas com maior rapidez.
* Reduzir a dependência exclusiva de inspeções manuais.
* Auxiliar o monitoramento visual das aves.
* Registrar automaticamente possíveis ocorrências.
* Fornecer uma forma simples de verificar possíveis casos identificados pelo sistema.

## 3. Escopo

O projeto irá:

* Utilizar um dataset público de imagens de aves para o desenvolvimento e treinamento do modelo.
* Analisar e preparar as imagens e suas respectivas classes ou anotações.
* Treinar um modelo de visão computacional, como o YOLO.
* Identificar aves em situações visualmente compatíveis com mortalidade.
* Avaliar o desempenho do modelo utilizando métricas como precisão, recall, F1-score e mAP.
* Caso seja viável, realizar testes adicionais com imagens reais de uma granja para avaliar a capacidade de generalização do modelo.

## 4. Fora do escopo

Nesta primeira versão, o projeto não irá:

* Criar um dataset completo próprio.
* Monitorar toda a granja em tempo real.
* Utilizar múltiplas câmeras.
* Utilizar sensores de temperatura, umidade ou outros sensores ambientais.
* Prever futuras mortes com base em condições ambientais.
* Desenvolver um segundo modelo de machine learning.
* Realizar diagnóstico veterinário.
* Garantir que uma ave está realmente morta apenas pela imagem.
* Automatizar a retirada das aves.
* Desenvolver uma solução comercial completa.

O objetivo é desenvolver uma prova de conceito de detecção visual.

## 5. Requisitos funcionais

* **RF01 — Entrada de imagens:** receber imagens de aves provenientes do dataset utilizado ou de imagens externas para teste.
* **RF02 — Detecção de aves:** identificar aves presentes nas imagens.
* **RF03 — Identificação de possíveis aves mortas:** classificar ou detectar aves que apresentem características visuais compatíveis com mortalidade.
* **RF04 — Indicação visual:** indicar na imagem onde a ave potencialmente morta foi localizada.
* **RF05 — Registro do resultado:** armazenar informações básicas das detecções realizadas pelo modelo.

## 6. Requisitos não funcionais

* **RNF01 — Precisão:** apresentar desempenho suficiente para permitir a avaliação da viabilidade da solução.
* **RNF02 — Facilidade de uso:** apresentar os resultados de forma simples e compreensível.
* **RNF03 — Desempenho:** processar as imagens em tempo adequado para permitir futuras aplicações de monitoramento.
* **RNF04 — Confiabilidade:** associar um nível de confiança às detecções realizadas.
* **RNF05 — Reprodutibilidade:** documentar o treinamento e os testes para que os resultados possam ser reproduzidos.

## 7. Critérios de aceitação

O projeto será considerado funcional quando:

* O dataset escolhido possuir quantidade e qualidade suficientes de imagens para realização do experimento.
* As imagens e anotações puderem ser utilizadas no treinamento do modelo.
* O modelo conseguir executar a detecção em imagens que não participaram do treinamento.
* O sistema conseguir indicar visualmente uma possível ave morta.
* O modelo apresentar métricas de desempenho mensuráveis.
* Os resultados permitirem avaliar a viabilidade da utilização de visão computacional nesse contexto.

Como o projeto ainda está em fase experimental, não será definida inicialmente uma precisão mínima arbitrária. O próprio experimento será utilizado para determinar qual desempenho pode ser obtido.

## 8. Priorização do MVP

### Essencial

* Selecionar e analisar o dataset.
* Preparar os dados para treinamento.
* Treinar o modelo YOLO.
* Detectar aves potencialmente mortas.
* Avaliar as métricas do modelo.

### Desejável caso haja tempo

* Testar o modelo com imagens reais de uma granja.
* Salvar automaticamente as detecções.
* Criar uma interface simples.
* Apresentar histórico de ocorrências.
* Gerar um alerta quando houver uma detecção.

### Fora do MVP

* Coleta de um dataset completo próprio.
* Monitoramento contínuo por câmera em uma granja.
* Várias câmeras.
* Aplicativo mobile.
* Sensores ambientais.
* Previsão de mortalidade.
* Monitoramento completo da granja.
* Automação física.

## 9. Dúvidas que ainda precisam de validação

Alguns pontos ainda precisam ser validados por meio da análise do dataset, experimentos e literatura científica:

* O dataset possui quantidade suficiente de imagens de aves potencialmente mortas?
* Existem diferenças visuais suficientes entre uma ave morta e uma ave apenas deitada ou descansando?
* As classes e anotações disponíveis no dataset são adequadas para o objetivo do projeto?
* O modelo consegue generalizar para imagens que não pertencem ao dataset utilizado no treinamento?
* Qual resolução das imagens é mais adequada para a detecção?
* Quais situações geram maior quantidade de falsos positivos?
* Qual taxa de falsos positivos seria aceitável para que o sistema seja útil na prática?
* Imagens reais de uma granja apresentam características suficientemente semelhantes às imagens utilizadas no treinamento?

## Resultado esperado

Ao final do projeto, espera-se obter uma prova de conceito capaz de utilizar imagens de aves para identificar situações visualmente compatíveis com mortalidade e avaliar a viabilidade da abordagem por meio de métricas de desempenho do modelo.

> Desenvolver e avaliar um sistema de visão computacional capaz de identificar aves potencialmente mortas em imagens, verificando a viabilidade da solução por meio de métricas de desempenho do modelo.
