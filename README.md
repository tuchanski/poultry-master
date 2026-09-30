# poultry-master

## Aplicação de visão computacional na identificação de aves potencialmente mortas em granjas avícolas

Projeto proposto para a disciplina **Projeto Transformador I**, do curso de Ciência da Computação da PUCPR.

A proposta é desenvolver uma solução de apoio ao monitoramento de granjas avícolas utilizando visão computacional para identificar individualmente as aves presentes em uma imagem, contabilizá-las e analisar sua condição aparente.

Em granjas avícolas, a identificação de aves mortas normalmente depende da inspeção realizada pelos funcionários durante o manejo. Em ambientes com grande quantidade de animais, essa atividade exige acompanhamento constante e pode demandar tempo significativo.

O projeto busca avaliar se técnicas de visão computacional podem auxiliar esse processo, identificando individualmente as aves presentes no ambiente e indicando possíveis casos de mortalidade para posterior verificação humana.

## Proposta

O sistema será composto por duas etapas principais de visão computacional.

A primeira etapa será responsável pela **detecção das aves presentes na imagem**, localizando cada animal individualmente por meio de bounding boxes.

A partir das detecções será possível realizar a **contagem automática das aves presentes na imagem**.

A segunda etapa será responsável pela **classificação da condição aparente de cada ave detectada**, considerando três categorias:

* Saudável (`healthy`)
* Doente (`sick`)
* Morta (`dead`)

Apesar de considerar as três classes, o principal foco do projeto será avaliar a capacidade do sistema de identificar corretamente aves pertencentes à classe `dead`.

A solução não tem como objetivo realizar diagnóstico veterinário nem determinar com certeza absoluta a condição de uma ave exclusivamente por meio de uma imagem. O sistema será desenvolvido como uma ferramenta de apoio ao monitoramento, indicando ocorrências que possam exigir verificação por um funcionário.

## Fluxo do sistema

O funcionamento geral do Poultry Master seguirá o seguinte fluxo:

```text
FOTO
  ↓
DETECÇÃO DAS INSTÂNCIAS
  ↓
CONTAGEM DAS AVES
  ↓
EXTRAÇÃO INDIVIDUAL DOS OBJETOS
  ↓
CLASSIFICAÇÃO
  ↓
MÉTRICAS
  ↓
RELATÓRIO
```

Inicialmente, uma imagem da granja será processada por um modelo de detecção de objetos responsável por localizar individualmente todas as aves visíveis.

A quantidade de objetos detectados será utilizada para determinar o número aproximado de aves presentes na imagem.

Cada região detectada será então recortada individualmente e enviada ao modelo de classificação.

O classificador deverá determinar a condição aparente de cada ave entre:

```text
healthy
sick
dead
```

Ao final do processamento serão calculadas métricas relacionadas às aves encontradas na imagem.

Entre elas:

* total de aves detectadas;
* quantidade de aves classificadas como saudáveis;
* quantidade de aves classificadas como doentes;
* quantidade de aves classificadas como potencialmente mortas;
* percentual de cada classificação;
* nível de confiança das classificações.

Essas informações poderão posteriormente ser utilizadas para geração de relatórios de acompanhamento.

Um possível resultado seria:

```text
Aves detectadas: 127

Healthy: 118
Sick: 6
Dead: 3

Possíveis aves mortas: 2,36%
```

## Objetivos funcionais

1. **Identificar individualmente todas as instâncias de aves presentes em uma imagem, quando houver aves visíveis.**

2. **Classificar cada ave identificada como saudável, doente ou potencialmente morta, quando houver informação visual suficiente para realizar a classificação.**

3. **Gerar métricas e registros a partir das aves identificadas e classificadas, permitindo acompanhar quantitativos e possíveis ocorrências de mortalidade.**

## Datasets

O projeto utilizará dois conjuntos de dados distintos, pois as etapas de detecção e classificação possuem objetivos diferentes.

### Detecção de aves — PIO

Para o treinamento do modelo responsável pela detecção das aves será utilizado o dataset **PIO — Poultry Images for Object Detection**, apresentado no trabalho:

**PIO, A Large-Scale Dataset for Broiler Chicken Detection under Real Poultry Farming Conditions**

https://pmc.ncbi.nlm.nih.gov/articles/PMC13223325/

O PIO possui **1.487 imagens** capturadas em instalações avícolas comerciais e experimentais, contendo um total de **327.289 instâncias de frangos anotadas manualmente**.

As imagens apresentam condições encontradas em ambientes reais de produção, incluindo variações de:

* iluminação;
* densidade de aves;
* tamanho e estágio de crescimento dos animais;
* posicionamento das aves;
* condições do ambiente.

As anotações são disponibilizadas na forma de **bounding boxes no formato YOLO**, permitindo utilizar o dataset diretamente para treinamento de modelos de detecção de objetos.

Nesta etapa, será utilizado um modelo da família **YOLO** para aprender a localizar individualmente cada ave presente na imagem.

O modelo terá inicialmente apenas uma classe:

```text
chicken
```

O objetivo dessa etapa não será determinar a condição da ave, mas localizar corretamente cada indivíduo para que ele possa ser contado e posteriormente analisado pelo classificador.

### Classificação da condição da ave

Para o treinamento do segundo modelo será utilizado o dataset público:

**Chicken Health Images Dataset — RGB and Thermal**

https://www.kaggle.com/datasets/ekosupriyanto/chicken-health-images-dataset-rgb-and-thermal

O conjunto contém imagens de aves divididas nas categorias:

```text
healthy
sick
dead
```

O dataset também possui imagens RGB e térmicas.

Para o MVP serão utilizadas inicialmente apenas as **imagens RGB**, reduzindo a complexidade da solução.

As imagens serão organizadas e separadas entre conjuntos de treinamento, validação e teste.

O modelo de classificação receberá como entrada a região correspondente a uma única ave previamente identificada pelo modelo de detecção e deverá retornar sua condição aparente e o nível de confiança da previsão.

## Imagens próprias da granja

Além dos datasets públicos, poderão ser coletadas imagens em uma granja real para avaliar o funcionamento do sistema no ambiente em que a solução poderia ser utilizada.

Essas imagens serão importantes principalmente para verificar a capacidade de generalização do detector, já que diferenças de iluminação, posicionamento da câmera, estrutura do galpão e densidade das aves podem influenciar o desempenho do modelo.

Caso necessário, parte dessas imagens poderá ser anotada e utilizada para realizar **fine-tuning** do modelo de detecção.

As imagens próprias também poderão formar um conjunto de teste separado, permitindo comparar o desempenho obtido nos datasets públicos com o desempenho em um ambiente real diferente daquele utilizado durante o treinamento.

## Pipeline de treinamento

O projeto será dividido inicialmente em dois pipelines independentes.

### 1. Detecção

```text
PIO Dataset
    ↓
Preparação dos dados
    ↓
Treinamento do YOLO
    ↓
Detecção individual das aves
    ↓
Bounding boxes
```

O objetivo será treinar um modelo capaz de localizar cada ave presente em uma imagem contendo múltiplos animais.

### 2. Classificação

```text
Chicken Health Images Dataset
            ↓
Preparação das imagens
            ↓
Treinamento do classificador
            ↓
healthy / sick / dead
```

Após o treinamento independente dos dois modelos, eles serão integrados em um único pipeline.

```text
Imagem da granja
       ↓
Detector YOLO
       ↓
Bounding boxes
       ↓
Contagem das aves
       ↓
Recorte individual
       ↓
Classificador
       ↓
healthy / sick / dead
       ↓
Cálculo das métricas
       ↓
Relatório
```

## Métricas

O projeto trabalhará com dois tipos diferentes de métricas.

### Métricas dos modelos

As métricas dos modelos serão utilizadas para avaliar tecnicamente o desempenho dos algoritmos utilizados.

#### Detector

O modelo de detecção poderá ser avaliado por meio de:

* Precision;
* Recall;
* mAP@50;
* mAP@50-95;
* IoU.

Também será analisada visualmente a capacidade do modelo de identificar aves em situações como:

* alta densidade de animais;
* sobreposição entre aves;
* diferentes condições de iluminação;
* aves parcialmente visíveis;
* diferentes regiões do galpão.

#### Classificador

O modelo responsável pela classificação poderá ser avaliado utilizando:

* acurácia;
* precisão;
* recall;
* F1-score;
* matriz de confusão.

Será dada atenção especial ao desempenho da classe `dead`.

Os falsos negativos serão especialmente relevantes, pois representam situações em que uma ave potencialmente morta não é identificada pelo sistema.

Também serão analisados falsos positivos, como situações em que uma ave saudável deitada ou descansando seja classificada incorretamente como morta.

### Métricas operacionais

Além das métricas utilizadas para avaliar os modelos de inteligência artificial, o sistema poderá gerar informações relacionadas ao ambiente analisado.

Exemplos:

* quantidade total de aves detectadas;
* quantidade de aves saudáveis;
* quantidade de aves doentes;
* quantidade de aves potencialmente mortas;
* percentual de aves em cada categoria;
* confiança média das classificações;
* histórico de ocorrências.

Essas informações poderão servir como base para relatórios de acompanhamento da granja.

## Relatórios

A etapa final do pipeline será responsável por organizar os resultados do processamento de forma compreensível para o usuário.

Um relatório poderá apresentar informações como:

```text
Data: 18/09/2026
Imagem analisada: granja_01.jpg

Total de aves detectadas: 127

Healthy: 118 (92,91%)
Sick: 6 (4,72%)
Dead: 3 (2,36%)

Possíveis ocorrências de mortalidade: 3
```

Também poderão ser armazenadas informações como:

* data e horário da análise;
* imagem processada;
* quantidade de aves detectadas;
* resultados das classificações;
* níveis de confiança;
* possíveis ocorrências de mortalidade.

No MVP, o relatório poderá ser apresentado de maneira simples, sem necessidade de uma plataforma completa de monitoramento.

## MVP

O MVP deverá ser capaz de receber uma imagem contendo múltiplas aves e:

1. detectar individualmente as aves presentes;
2. contabilizar as aves detectadas;
3. extrair individualmente cada região detectada;
4. classificar cada ave entre `healthy`, `sick` ou `dead`;
5. apresentar a classe prevista e o nível de confiança;
6. calcular métricas relacionadas à imagem analisada;
7. apresentar um relatório simples com os resultados;
8. indicar possíveis ocorrências de aves mortas para verificação.

O processamento poderá inicialmente ser realizado sobre imagens estáticas, sem necessidade de integração em tempo real com câmeras.

## Fora do escopo inicial

Para reduzir a complexidade do projeto, inicialmente não fazem parte do MVP:

* diagnóstico de doenças específicas;
* análise veterinária;
* utilização obrigatória de imagens térmicas;
* processamento contínuo de vídeo em tempo real;
* rastreamento da mesma ave entre diferentes frames;
* identificação individual permanente de cada animal;
* funcionamento embarcado diretamente em câmeras;
* cobertura automática de toda a extensão de um galpão;
* sistema completo de alertas em tempo real.

## Evoluções futuras

Após a validação do MVP, algumas possíveis evoluções incluem:

* utilização de vídeo em tempo real;
* captura automática de imagens por câmeras instaladas na granja;
* geração automática de alertas;
* armazenamento de histórico de ocorrências;
* dashboard para acompanhamento;
* geração de relatórios históricos;
* comparação entre imagens RGB e térmicas;
* rastreamento de aves ao longo do tempo;
* monitoramento de diferentes regiões do galpão;
* utilização de imagens próprias para fine-tuning dos modelos;
* avaliação do sistema em diferentes granjas.

## Estado atual

O projeto encontra-se na etapa de definição e preparação do pipeline de visão computacional.

A primeira etapa do [plano do MVP](docs/plano-mvp.md) foi auditada: os requisitos foram alinhados, os datasets foram obtidos e suas estruturas, licenças e amostras foram verificadas. O [inventário e as pendências](docs/experimentos.md) registram duplicatas entre treino e validação do PIO, caixas sem área e a necessidade de revisar recortes individuais no dataset de saúde antes do treinamento.

Foram definidos dois problemas principais de inteligência artificial:

* **detecção individual das aves presentes em uma imagem;**
* **classificação da condição aparente de cada ave detectada.**

Para a etapa de detecção foi identificado o dataset público **PIO**, contendo imagens de ambientes reais de produção e anotações individuais de aves.

Para a etapa de classificação será utilizado o **Chicken Health Images Dataset — RGB and Thermal**, inicialmente considerando apenas imagens RGB.

A arquitetura proposta seguirá o fluxo:

```text
Foto → Detecção → Contagem → Classificação → Métricas → Relatório
```

As próximas etapas incluem a preparação dos datasets, treinamento dos primeiros modelos, avaliação individual de cada etapa e posteriormente a integração dos modelos em um único pipeline.
