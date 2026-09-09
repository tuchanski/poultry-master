# poultry-master

## Aplicação de visão computacional na identificação de aves potencialmente mortas em granjas avícolas

Projeto proposto para a disciplina **Projeto Transformador I**, do curso de Ciência da Computação da PUCPR.

A proposta é desenvolver uma solução de apoio ao monitoramento de granjas avícolas utilizando visão computacional para identificar aves que apresentem características visualmente compatíveis com mortalidade.

Em granjas avícolas, a identificação de aves mortas normalmente depende da inspeção realizada pelos funcionários durante o manejo. Em ambientes com grande quantidade de animais, essa atividade exige acompanhamento constante e pode demandar tempo significativo.

O projeto busca avaliar se técnicas de visão computacional podem auxiliar esse processo, analisando imagens de aves e indicando possíveis casos de mortalidade para posterior verificação humana.

## Proposta

O sistema utilizará imagens de aves para classificar sua condição aparente entre três categorias:

* **Saudável**
* **Doente**
* **Morta**

Apesar de considerar as três classes, o principal foco do projeto será avaliar a capacidade do modelo de identificar corretamente aves pertencentes à classe **morta**.

A solução não tem como objetivo realizar diagnóstico veterinário nem determinar com certeza absoluta se uma ave está morta exclusivamente pela imagem. O sistema será desenvolvido como uma ferramenta de apoio ao monitoramento, indicando ocorrências que possam exigir verificação por um funcionário.

Inicialmente, o projeto utilizará imagens RGB e será desenvolvido como uma prova de conceito utilizando um dataset público.

Caso os resultados sejam satisfatórios, poderão ser realizados testes adicionais utilizando imagens reais de uma granja, permitindo avaliar a capacidade de generalização do modelo em um ambiente diferente daquele utilizado durante o treinamento.

## Dataset e treinamento

O projeto utilizará o dataset público **Chicken Health Images Dataset - RGB and Thermal**, disponível no Kaggle:

https://www.kaggle.com/datasets/ekosupriyanto/chicken-health-images-dataset-rgb-and-thermal

O conjunto contém imagens de aves classificadas nas categorias **healthy**, **sick** e **dead**, incluindo imagens RGB e térmicas.

Para o MVP, serão utilizadas inicialmente apenas as imagens RGB, reduzindo a complexidade da solução.

As imagens serão analisadas e preparadas para treinamento, incluindo a organização das classes e a separação dos dados entre treinamento, validação e teste.

Será utilizado um modelo de visão computacional voltado à classificação de imagens, inicialmente considerando abordagens como o **YOLO em modo de classificação**.

## Utilização do sistema

Uma imagem fornecida ao sistema será processada pelo modelo, que deverá retornar a condição prevista da ave e o nível de confiança da classificação.

Quando uma imagem apresentar características compatíveis com uma ave morta, a ocorrência poderá ser registrada para posterior verificação.

Em evoluções futuras, esse processo poderá ser integrado a câmeras instaladas em uma granja, permitindo realizar análises periódicas das imagens capturadas.

A partir dessas classificações, também seria possível manter um histórico de possíveis ocorrências de mortalidade e auxiliar produtores e funcionários no acompanhamento das aves.

## Validação

O modelo será validado utilizando imagens que não tenham participado do processo de treinamento.

O desempenho será analisado por meio de métricas como:

* acurácia;
* precisão;
* recall;
* F1-score;
* matriz de confusão.

Além das métricas gerais, será dada atenção especial ao desempenho da classe **morta**.

Os falsos negativos serão particularmente importantes, pois representam situações em que uma ave morta não é identificada pelo sistema.

Também serão analisados falsos positivos, como situações em que uma ave saudável deitada ou descansando possa ser classificada incorretamente como morta.

Caso seja possível obter imagens reais de uma granja, elas poderão ser utilizadas como um teste adicional para verificar a generalização do modelo.

## Evoluções futuras

Após a validação do MVP, algumas possíveis evoluções incluem:

* utilização de imagens reais de uma granja;
* comparação entre imagens RGB e térmicas;
* captura periódica de imagens por câmeras;
* geração automática de alertas;
* armazenamento de histórico de ocorrências;
* criação de uma interface para acompanhamento das classificações;
* utilização de detecção de objetos para analisar múltiplas aves em uma mesma imagem;
* monitoramento de diferentes regiões de um galpão.

Essas funcionalidades não fazem parte do escopo inicial e dependerão dos resultados obtidos durante o desenvolvimento da prova de conceito.

## Estado atual

O projeto está em fase de definição e validação inicial.

O foco atual está na análise do dataset, definição do pipeline de treinamento, escolha da abordagem de visão computacional e realização dos primeiros experimentos de classificação.
