# 🐔 poultry-master

## Aplicação de visão computacional na classificação de aves potencialmente mortas em granjas avícolas

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

* Utilizar um dataset público de imagens de aves dividido nas classes saudável, doente e morta.
* Utilizar inicialmente imagens RGB para manter o escopo da solução simples.
* Analisar e preparar as imagens para treinamento.
* Treinar um modelo de visão computacional, como o YOLO em modo de classificação.
* Classificar imagens de aves entre as categorias saudável, doente e morta.
* Dar maior atenção à identificação da classe correspondente a aves mortas.
* Avaliar o desempenho do modelo utilizando métricas como precisão, recall, F1-score e matriz de confusão.
* Caso seja viável, realizar testes adicionais com imagens reais de uma granja para avaliar a capacidade de generalização do modelo.

## 4. Fora do escopo

Nesta primeira versão, o projeto não irá:

* Criar um dataset completo próprio.
* Utilizar imagens térmicas como requisito do MVP.
* Monitorar toda a granja em tempo real.
* Utilizar múltiplas câmeras.
* Utilizar sensores de temperatura, umidade ou outros sensores ambientais.
* Prever futuras mortes com base em condições ambientais.
* Desenvolver um segundo modelo de machine learning.
* Realizar diagnóstico veterinário.
* Garantir que uma ave está realmente morta apenas pela imagem.
* Automatizar a retirada das aves.
* Desenvolver uma solução comercial completa.

O objetivo é desenvolver uma prova de conceito de classificação visual.

## 5. Requisitos funcionais

* **RF01 — Entrada de imagens:** receber imagens RGB de aves provenientes do dataset utilizado ou de imagens externas para teste.
* **RF02 — Classificação da condição da ave:** classificar a imagem entre as categorias saudável, doente ou morta.
* **RF03 — Identificação de possível mortalidade:** identificar quando uma imagem apresentar características compatíveis com a classe de ave morta.
* **RF04 — Exibição do resultado:** apresentar a classe prevista pelo modelo e seu respectivo nível de confiança.
* **RF05 — Registro do resultado:** armazenar informações básicas das classificações realizadas pelo modelo.

## 6. Requisitos não funcionais

* **RNF01 — Precisão:** apresentar desempenho suficiente para permitir a avaliação da viabilidade da solução.
* **RNF02 — Facilidade de uso:** apresentar os resultados de forma simples e compreensível.
* **RNF03 — Desempenho:** processar as imagens em tempo adequado para permitir futuras aplicações de monitoramento.
* **RNF04 — Confiabilidade:** associar um nível de confiança às classificações realizadas.
* **RNF05 — Reprodutibilidade:** documentar o treinamento e os testes para que os resultados possam ser reproduzidos.

## 7. Critérios de aceitação

O projeto será considerado funcional quando:

* O dataset escolhido possuir quantidade e qualidade suficientes de imagens para realização do experimento.
* As imagens puderem ser utilizadas no treinamento do modelo.
* O modelo conseguir classificar imagens que não participaram do treinamento.
* O sistema conseguir distinguir entre imagens de aves saudáveis, doentes e mortas.
* O desempenho específico da classe de aves mortas puder ser mensurado.
* O modelo apresentar métricas de desempenho mensuráveis.
* Os resultados permitirem avaliar a viabilidade da utilização de visão computacional nesse contexto.

Como o projeto ainda está em fase experimental, não será definida inicialmente uma precisão mínima arbitrária. O próprio experimento será utilizado para determinar qual desempenho pode ser obtido.

## 8. Priorização do MVP

### Essencial

* Selecionar e analisar o dataset.
* Utilizar as imagens RGB das classes saudável, doente e morta.
* Preparar os dados para treinamento.
* Treinar o modelo de classificação.
* Classificar imagens entre saudável, doente e morta.
* Avaliar as métricas gerais e, principalmente, o desempenho da classe de aves mortas.

### Desejável caso haja tempo

* Testar o modelo com imagens reais de uma granja.
* Comparar o desempenho utilizando imagens RGB e térmicas.
* Salvar automaticamente os resultados.
* Criar uma interface simples.
* Apresentar histórico de ocorrências.
* Gerar um alerta quando uma imagem for classificada como possível ave morta.

### Fora do MVP

* Coleta de um dataset completo próprio.
* Detecção individual de múltiplas aves por bounding boxes.
* Monitoramento contínuo por câmera em uma granja.
* Várias câmeras.
* Aplicativo mobile.
* Sensores ambientais.
* Previsão de mortalidade.
* Monitoramento completo da granja.
* Automação física.

## 9. Dúvidas que ainda precisam de validação

Alguns pontos ainda precisam ser validados por meio da análise do dataset, experimentos e literatura científica:

* O dataset possui quantidade equilibrada de imagens entre as classes saudável, doente e morta?
* Existem diferenças visuais suficientes entre aves mortas, doentes e aves saudáveis apenas deitadas ou descansando?
* Qual desempenho o modelo consegue atingir especificamente na classe de aves mortas?
* Quais situações geram maior quantidade de falsos positivos e falsos negativos?
* O modelo consegue generalizar para imagens que não pertencem ao dataset utilizado no treinamento?
* Imagens reais de uma granja apresentam características suficientemente semelhantes às imagens utilizadas no treinamento?
* A utilização de imagens térmicas melhora significativamente o desempenho em relação ao uso apenas de imagens RGB?

## Resultado esperado

Ao final do projeto, espera-se obter uma prova de conceito capaz de classificar imagens de aves entre as categorias saudável, doente e morta, com foco na identificação de aves potencialmente mortas, avaliando a viabilidade da abordagem por meio de métricas de desempenho do modelo.

> Desenvolver e avaliar um sistema de visão computacional capaz de classificar imagens de aves e identificar casos visualmente compatíveis com mortalidade, verificando a viabilidade da solução por meio de métricas de desempenho do modelo.
>

## Dataset utilizado

O projeto utilizará o dataset público **Chicken Health Images Dataset - RGB and Thermal**, disponível no Kaggle:

https://www.kaggle.com/datasets/ekosupriyanto/chicken-health-images-dataset-rgb-and-thermal

O dataset contém imagens de aves classificadas nas categorias **healthy**, **sick** e **dead**, incluindo imagens RGB e térmicas. Inicialmente, o projeto utilizará apenas as imagens RGB para manter o escopo do MVP mais simples.

