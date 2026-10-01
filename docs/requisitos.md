# Requisitos do Projeto

## 1. Problema e contexto

Em granjas avícolas, a identificação de aves mortas depende principalmente da inspeção visual realizada pelos funcionários responsáveis pelo manejo.

Em ambientes com uma grande quantidade de aves, acompanhar individualmente todos os animais pode ser uma tarefa trabalhosa. Uma ave morta também pode não ser identificada imediatamente, principalmente dependendo de sua posição, da densidade de animais e das condições de visualização dentro do galpão.

O projeto busca avaliar a utilização de visão computacional como ferramenta de apoio a esse processo, detectando e contando aves em uma foto e classificando a condição aparente de cada ave entre saudável (`healthy`) e potencialmente morta (`dead`).

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

**Classificação da condição aparente:** diferenciar aves aparentemente saudáveis e potencialmente mortas.

**Localização e contagem:** localizar cada ave detectada por uma bounding box e apresentar a quantidade de aves detectadas na foto.

**Apresentação de confiança:** informar o nível de confiança associado à classificação realizada pelo modelo.

**Registro das ocorrências:** permitir que as classificações sejam armazenadas para posterior consulta.

**Verificação humana:** permitir que as ocorrências indicadas pelo modelo sejam verificadas por um responsável.

## 4. Escopo e não escopo

O MVP analisará uma foto RGB por execução, podendo conter múltiplas aves. O fluxo será: imagem → detecção individual → contagem → recortes → classificação por ave → métricas → relatório. Esta definição acompanha o [README](../README.md) e o [plano do MVP](plano-mvp.md).

**Dentro do escopo:** execução local por linha de comando, detecção de aves, contagem aproximada, extração de recortes individuais, classificação nas duas classes, confiança por ave, resumo no terminal, imagem anotada e relatório JSON local. O detector e o classificador serão treinados e avaliados separadamente e também avaliados em conjunto.

**Fora do escopo inicial:** classe `sick`, interface web ou mobile, API, banco de dados, consulta de histórico pela aplicação, relatórios PDF, imagens térmicas, vídeo em tempo real, múltiplas câmeras, rastreamento, alertas automáticos, diagnóstico veterinário, previsão futura de mortalidade, sensores ambientais e automação da retirada das aves.

## 5. Requisitos funcionais

**RF01:** receber o caminho de uma foto RGB válida para análise, com uma ou múltiplas aves, ou sem aves visíveis.

**RF02:** executar o detector sobre a foto e o classificador sobre cada recorte válido de ave detectada.

**RF03:** classificar cada recorte válido em exatamente uma classe: `healthy` ou `dead`.

**RF04:** informar a confiança da classificação de cada ave, mantendo-a separada da confiança da detecção.

**RF05:** destacar cada previsão `dead` como possível ave morta para verificação humana, associada a um identificador e à sua caixa na foto.

**RF06:** salvar `report.json` com identificador da análise, data e horário com fuso, imagem de origem, dimensões, tempo de processamento, versões dos dois modelos, parâmetros de inferência, resultados por ave, contagens e percentuais.

**RF07 (evolução futura):** permitir consultar o histórico pela aplicação. No MVP, a consulta será feita abrindo os arquivos salvos.

**RF08:** permitir a utilização de imagens externas ao dataset para testes do modelo.

**RF09:** detectar aves na foto com uma classe de detecção (`chicken`), retornando caixas e confiança. A classe original `Pollo` do PIO será mapeada para `chicken` na preparação dos dados, preservando o identificador 0.

**RF10:** contar as caixas válidas aceitas e extrair um recorte por caixa para classificação, limitado às dimensões da imagem.

**RF11:** apresentar no terminal o total detectado e as quantidades e percentuais por classe; salvar `annotated.jpg` com caixas, identificadores locais, classes e confiança da classificação.

**RF12:** informar claramente erros de entrada, pesos ausentes ou incompatíveis, falha de classificação e impossibilidade de gravar a saída, sem apresentar uma análise incompleta como sucesso.

## 6. Requisitos não funcionais

**RNF01:** medir e registrar o tempo de processamento por foto, juntamente com hardware e resolução na avaliação. O MVP não terá compromisso de tempo real; a meta numérica de latência permanece em aberto.

**RNF02:** o sistema deve registrar os identificadores e versões do detector e do classificador, além dos parâmetros utilizados em cada análise.

**RNF03:** os resultados devem ser apresentados de forma simples e compreensível.

**RNF04:** o processo de treinamento e avaliação deve ser documentado de forma que os experimentos possam ser reproduzidos.

**RNF05:** o sistema deve informar a confiança da previsão sem apresentar a classificação como um diagnóstico definitivo.

**RNF06:** a inferência deve ser executável localmente em CPU e preservar a imagem original. A disponibilidade de GPU para treinamento será verificada na preparação do ambiente.

Sem grupos de captura confiáveis, admite-se treino apenas demonstrativo, sem validação/teste artificiais. Registrar avaliação independente pendente; o MVP funcional não comprova generalização.

## 7. Regras de negócio

**RN01:** em uma análise concluída com sucesso, cada ave detectada com recorte válido deve receber exatamente uma das duas classes. Uma foto sem detecções não recebe classificação de saúde: retorna lista vazia, totais e percentuais zerados e a mensagem “nenhuma ave detectada”. Isso não confirma ausência de aves na foto.


**RN02:** uma classificação como morta deve ser interpretada como indicação de uma ave potencialmente morta e não como confirmação definitiva de óbito.

**RN03:** ocorrências classificadas como possíveis aves mortas devem ser consideradas candidatas à verificação humana.

**RN04:** o foco da avaliação do modelo deve considerar especialmente o desempenho da classe correspondente às aves mortas.

**RN05:** em uma análise concluída com sucesso, `healthy + dead = total_classificado = total_detectado`. Os percentuais usam o total detectado como denominador e não representam a mortalidade de todo o plantel.

**RN06:** identificadores de aves serão válidos apenas dentro da análise; não representam identificação permanente ou rastreamento.

**RN07:** toda previsão `dead` será indicada para verificação, mesmo com baixa confiança. A confiança é uma pontuação do modelo e não uma certeza clínica.

**RN08:** caixas sem área serão descartadas antes da contagem e dos recortes. Se um recorte válido não puder ser classificado, a execução deverá informar falha, sem inventar uma classe.

**RN09:** `healthy` não confirma saúde nem representa toda ave viva. Imagens `sick` não serão convertidas em outra classe nem utilizadas no treinamento binário.

## 8. Critérios de aceitação

Os critérios de aceitação foram definidos para os requisitos considerados essenciais para o MVP.

**CA-RF01:** ao receber uma imagem RGB válida, o sistema deve conseguir carregar e processar o conteúdo.

**CA-RF02:** a análise deve executar os dois modelos treinados, preservando a associação entre caixa, recorte e classificação.

**CA-RF03:** cada ave detectada com recorte válido deve retornar uma das classes `healthy` ou `dead`. Sem detecções, o sistema deve retornar lista vazia e resumo zerado, sem executar classificação nem dividir por zero.

**CA-RF04:** cada resultado individual deve apresentar a confiança da classificação e, separadamente, a confiança da detecção, com valores entre 0 e 1 no JSON.

**CA-RF05:** cada previsão `dead` deve aparecer na imagem anotada e no relatório como possível ocorrência para verificação humana.

**CA-RF06:** o JSON salvo deve conter os campos de RF06 e ser legível independentemente de uma nova execução dos modelos.

**CA-RF08:** uma foto RGB externa deve poder ser analisada pelo mesmo comando, sem depender de estar nas pastas dos datasets.

**CA-RF09:** cada caixa aceita deve estar limitada à imagem e permitir localizar visualmente a detecção; o resultado também pode conter zero detecções.

**CA-RF10:** a quantidade de caixas válidas deve coincidir com a quantidade de recortes classificados em uma execução bem-sucedida.

**CA-RF11:** terminal, imagem anotada e JSON devem representar as mesmas detecções; as contagens e os percentuais devem obedecer à RN05, admitindo arredondamento na exibição.

**CA-RF12:** arquivo inválido, peso ausente e falha de processamento ou gravação devem produzir mensagem compreensível e código de saída diferente de zero.

O desempenho dos modelos deverá ser avaliado utilizando conjuntos de teste separados de treino e validação. Imagens idênticas e imagens da mesma sequência ou animal, quando identificáveis, não devem atravessar as divisões. A auditoria dos arquivos originais está registrada em [experimentos](experimentos.md).

O detector será avaliado por precision, recall, mAP@50 e mAP@50-95. O classificador será avaliado por acurácia, precisão, recall, F1 e matriz de confusão, incluindo suporte por classe e análise específica de `dead`. Na avaliação integrada, aves mortas não encontradas pelo detector também contam como falhas. As metas numéricas de desempenho ainda não foram definidas; o funcionamento do programa não comprova adequação ao uso operacional.

## 9. Priorização do MVP

A priorização dos requisitos foi realizada utilizando o método MoSCoW.

**Must have:** RF01, RF02, RF03, RF04, RF05, RF06, RF08, RF09, RF10, RF11 e RF12. O registro em arquivo é parte do relatório mínimo; a entrada local também atende imagens externas.

**Should have:** nenhuma funcionalidade adicional nesta versão mínima.

**Could have (após o MVP):** RF07.

**Won't have now:** monitoramento contínuo da granja, múltiplas câmeras, aplicativo mobile, sensores ambientais, previsão de mortalidade, diagnóstico veterinário e automação física.

## 10. Riscos, dúvidas e requisitos ainda abertos

**Distribuição do dataset:** a auditoria encontrou 200 imagens RGB por classe, com duas duplicatas exatas excedentes em `healthy`. O equilíbrio de arquivos não garante variedade de animais ou sessões de captura.

**Anotações e divisões:** foram encontradas imagens idênticas entre treino e validação do PIO, cinco caixas com largura zero e imagens de saúde com múltiplas aves sem anotações individuais. Esses pontos precisam ser tratados antes dos treinamentos correspondentes; detalhes e evidências estão em [experimentos](experimentos.md).

**Diferença visual entre as classes:** deve ser avaliado se existem características suficientes para diferenciar uma ave morta de uma ave saudável deitada ou descansando.

**Falsos negativos:** existe o risco de aves mortas não serem identificadas pelo modelo, o que reduz a utilidade da solução como ferramenta de apoio.

**Falsos positivos:** aves saudáveis ou doentes podem apresentar posições semelhantes às de uma ave morta e serem classificadas incorretamente.

**Generalização do modelo:** existe o risco de o desempenho diminuir quando forem utilizadas imagens com iluminação, ângulos, câmeras ou ambientes diferentes daqueles presentes no dataset.

**Imagens reais da granja:** ainda precisa ser avaliado se imagens obtidas em condições reais apresentam características semelhantes às utilizadas durante o treinamento.

**Imagens térmicas:** deverá ser investigado posteriormente se a utilização da modalidade térmica apresenta ganho significativo em relação às imagens RGB.

**Forma de análise:** o MVP utilizará uma foto estática por execução, com classificação individual dos recortes das aves detectadas. Monitoramento contínuo por vídeo ou câmeras será considerado apenas como evolução futura.
