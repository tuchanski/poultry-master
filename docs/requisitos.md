# Requisitos do Projeto

## 1. Problema e contexto

Em granjas avícolas, a identificação de aves mortas depende principalmente da inspeção visual realizada pelos funcionários responsáveis pelo manejo.

Em ambientes com uma grande quantidade de aves, acompanhar individualmente todos os animais pode ser uma tarefa trabalhosa. Uma ave morta também pode não ser identificada imediatamente, principalmente dependendo de sua posição, da densidade de animais e das condições de visualização dentro do galpão.

O projeto busca avaliar a utilização de visão computacional como ferramenta de apoio a esse processo, analisando imagens de aves e classificando sua condição aparente entre saudável, doente e morta.

O objetivo principal é verificar se características visuais presentes nas imagens podem ser utilizadas para identificar aves potencialmente mortas e indicar essas ocorrências para posterior verificação humana.

## 2. Stakeholders

**Produtores e proprietários de granjas avícolas:** interessados em acompanhar ocorrências de mortalidade e as condições gerais das aves.

**Funcionários responsáveis pelo manejo:** realizam a inspeção dos animais e podem utilizar o sistema como ferramenta de apoio para localizar possíveis aves mortas.

**Gestores da produção:** podem utilizar registros produzidos pelo sistema para acompanhar ocorrências ao longo do tempo.

**Especialistas da área avícola ou veterinária:** podem auxiliar na interpretação dos resultados e na validação de situações relevantes para o monitoramento das aves.

**Equipe responsável pelo sistema:** responsável pelo desenvolvimento, treinamento, validação e manutenção da solução.

Para o MVP, os stakeholders prioritários serão os produtores e funcionários responsáveis pelo acompanhamento das aves.

## 3. Necessidades identificadas

**Identificação de possíveis aves mortas:** auxiliar na localização de aves que apresentem características visualmente compatíveis com mortalidade.

**Redução da dependência exclusiva da inspeção manual:** oferecer uma ferramenta complementar ao processo realizado pelos funcionários.

**Classificação da condição aparente:** diferenciar aves aparentemente saudáveis, doentes e mortas.

**Apresentação de confiança:** informar o nível de confiança associado à classificação realizada pelo modelo.

**Registro das ocorrências:** permitir que as classificações sejam armazenadas para posterior consulta.

**Verificação humana:** permitir que as ocorrências indicadas pelo modelo sejam verificadas por um responsável.

## 4. Escopo e não escopo

O escopo inicial será focado na classificação de imagens individuais de aves utilizando visão computacional.

**Dentro do escopo:** utilização de imagens RGB, classificação entre saudável, doente e morta, apresentação da classe prevista e do nível de confiança, avaliação do modelo e registro básico dos resultados.

**Fora do escopo inicial:** monitoramento contínuo de toda uma granja, utilização de múltiplas câmeras, diagnóstico veterinário, previsão futura de mortalidade, utilização de sensores ambientais e automação da retirada das aves.

## 5. Requisitos funcionais

**RF01:** receber imagens RGB de aves para análise.

**RF02:** processar a imagem utilizando o modelo de visão computacional.

**RF03:** classificar a condição aparente da ave entre saudável, doente ou morta.

**RF04:** informar o nível de confiança associado à classificação.

**RF05:** identificar quando a classificação realizada corresponder à classe de possível ave morta.

**RF06:** registrar informações básicas da análise realizada.

**RF07:** permitir a consulta dos resultados registrados.

**RF08:** permitir a utilização de imagens externas ao dataset para testes do modelo.

## 6. Requisitos não funcionais

**RNF01:** o sistema deve apresentar o resultado da classificação em tempo adequado para permitir futuras aplicações de monitoramento.

**RNF02:** o sistema deve registrar a versão do modelo utilizada em cada classificação.

**RNF03:** os resultados devem ser apresentados de forma simples e compreensível.

**RNF04:** o processo de treinamento e avaliação deve ser documentado de forma que os experimentos possam ser reproduzidos.

**RNF05:** o sistema deve informar a confiança da previsão sem apresentar a classificação como um diagnóstico definitivo.

## 7. Regras de negócio

**RN01:** toda imagem válida analisada deve receber uma das classificações definidas: saudável, doente ou morta.

**RN02:** uma classificação como morta deve ser interpretada como indicação de uma ave potencialmente morta e não como confirmação definitiva de óbito.

**RN03:** ocorrências classificadas como possíveis aves mortas devem ser consideradas candidatas à verificação humana.

**RN04:** o foco da avaliação do modelo deve considerar especialmente o desempenho da classe correspondente às aves mortas.

## 8. Critérios de aceitação

Os critérios de aceitação foram definidos para os requisitos considerados essenciais para o MVP.

**CA-RF01:** ao receber uma imagem RGB válida, o sistema deve conseguir carregar e processar o conteúdo.

**CA-RF02:** o sistema deve conseguir executar o modelo de visão computacional sobre a imagem recebida.

**CA-RF03:** ao final da análise, o sistema deve retornar exatamente uma das três classes definidas: saudável, doente ou morta.

**CA-RF04:** o resultado deve apresentar o nível de confiança associado à classificação.

**CA-RF05:** quando a classe prevista for morta, o sistema deve indicar que existe uma possível ocorrência de mortalidade.

O desempenho do modelo deverá ser avaliado utilizando um conjunto de teste separado dos dados utilizados no treinamento.

Serão utilizadas métricas como acurácia, precisão, recall, F1-score e matriz de confusão, incluindo análise específica da classe correspondente às aves mortas.

## 9. Priorização do MVP

A priorização dos requisitos foi realizada utilizando o método MoSCoW.

**Must have:** RF01, RF02, RF03, RF04 e RF05.

**Should have:** RF06.

**Could have:** RF07 e RF08.

**Won't have now:** monitoramento contínuo da granja, múltiplas câmeras, aplicativo mobile, sensores ambientais, previsão de mortalidade, diagnóstico veterinário e automação física.

## 10. Riscos, dúvidas e requisitos ainda abertos

**Distribuição do dataset:** ainda é necessário verificar se existe quantidade adequada e equilíbrio de imagens entre as classes saudável, doente e morta.

**Diferença visual entre as classes:** deve ser avaliado se existem características suficientes para diferenciar uma ave morta de uma ave saudável deitada ou descansando.

**Falsos negativos:** existe o risco de aves mortas não serem identificadas pelo modelo, o que reduz a utilidade da solução como ferramenta de apoio.

**Falsos positivos:** aves saudáveis ou doentes podem apresentar posições semelhantes às de uma ave morta e serem classificadas incorretamente.

**Generalização do modelo:** existe o risco de o desempenho diminuir quando forem utilizadas imagens com iluminação, ângulos, câmeras ou ambientes diferentes daqueles presentes no dataset.

**Imagens reais da granja:** ainda precisa ser avaliado se imagens obtidas em condições reais apresentam características semelhantes às utilizadas durante o treinamento.

**Imagens térmicas:** deverá ser investigado posteriormente se a utilização da modalidade térmica apresenta ganho significativo em relação às imagens RGB.

**Forma de análise:** o MVP utilizará imagens individuais. Monitoramento contínuo por vídeo ou câmeras será considerado apenas como possível evolução futura.
