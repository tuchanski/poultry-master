# Plano de implementação do MVP

## 1. Objetivo e decisão de escopo

Entregar um programa local que receba uma foto RGB com múltiplas aves, detecte e conte os indivíduos, classifique cada recorte em **`healthy` ou `dead`** e salve uma imagem anotada e um relatório JSON para verificação humana.

Considerando o prazo curto informado pelo usuário, o essencial é demonstrar **dois modelos treinados funcionando juntos**: um detector que localiza as aves (`chicken`) e um classificador binário que analisa cada recorte. A classe `sick` fica para depois; suas imagens não serão convertidas em `healthy` nem utilizadas no treinamento binário. `Healthy` indica semelhança com os exemplos saudáveis do treinamento, não confirmação de saúde nem uma categoria que represente todo animal vivo.

Base do plano: [README](../README.md), [requisitos](requisitos.md) e [referências](referencias.md). Na criação do plano, o repositório continha apenas documentação. A auditoria da etapa 1 está registrada em [experimentos](experimentos.md).

O fluxo de detecção e classificação de múltiplas aves permanece. Este plano reduz a proposta de três classes ainda descrita no README e nos requisitos; a atualização desses documentos e dos contratos do código para duas classes faz parte da etapa 3. A classificação isolada não será suficiente para concluir o MVP.

**Ponto de partida:** as etapas 1 e 2 já têm sua implementação disponível. Reaproveitar ambiente, PIO preparado, scripts e ferramenta de revisão. A preparação dos recortes reais de saúde continua pendente, mas deixa de exigir a revisão das 598 imagens: será feita sobre um subconjunto binário, com auxílio do detector na etapa 3.

**A simplificação principal será na aplicação:** uma imagem por execução, interface por linha de comando e arquivos locais. Sem interface web da aplicação, API, banco de dados, autenticação, serviços em nuvem, vídeo, câmeras ou histórico consultável pela aplicação. Também ficam fora a classe `sick`, a revisão integral do dataset de saúde, imagens térmicas, diagnóstico veterinário, notificações automáticas e rastreamento. A ferramenta local de revisão já implementada continua sendo utilizada na preparação dos dados.

## 2. Experiência mínima de uso

Comando proposto, a ser implementado:

```powershell
.venv/Scripts/python.exe analyze.py --image exemplos/granja.jpg --output outputs/analise-001
```

Os caminhos dos pesos e os parâmetros de inferência ficarão em um arquivo de configuração local. O programa deverá:

1. Carregar e validar a imagem.
2. Detectar aves e contar as caixas válidas aceitas pelo detector.
3. Recortar cada caixa e classificar a condição aparente da ave.
4. Mostrar no terminal o total e as quantidades e percentuais por classe.
5. Salvar `annotated.jpg`, com identificadores, caixas, classes e confiança da classificação.
6. Salvar `report.json`, com o resumo e os resultados individuais.
7. Destacar as aves previstas como `dead` como “potencialmente mortas — verificar presencialmente”.

O relatório em JSON constitui o registro básico de RF06. Sua abertura manual permite consultar o resultado, mas uma funcionalidade específica de consulta de histórico, prevista em RF07, ficará para depois. A entrada por caminho de arquivo já permite testes com imagens externas, como previsto em RF08.

## 3. Arquitetura e ferramentas propostas

```text
Imagem RGB
    → detector de uma classe: chicken
    → caixas válidas e contagem
    → recortes individuais
    → classificador: healthy / dead
    → agregação dos resultados
    → terminal + annotated.jpg + report.json
```

| Componente | Escolha inicial | Motivo |
| --- | --- | --- |
| Execução | Python, ambiente virtual e dependências fixadas | Um único ambiente para treinamento e aplicação |
| Detector | Modelo YOLO pequeno, pré-treinado e ajustado no PIO | Seguir a arquitetura definida no README |
| Classificador | Modelo pequeno de classificação da mesma biblioteca, ajustado nos dados RGB | Reduzir integrações e evitar desenvolver uma rede própria |
| Biblioteca dos modelos | Ultralytics | Disponibiliza tarefas de [detecção](https://docs.ultralytics.com/tasks/detect/) e [classificação](https://docs.ultralytics.com/tasks/classify/) |
| Imagens | Pillow | Carregar, recortar e desenhar as anotações |
| Relatório e CLI | `json` e `argparse` da biblioteca padrão | Evitar dependências adicionais na aplicação |
| Avaliação | Métricas do detector e scikit-learn para o classificador | Produzir métricas e matriz de confusão |

Reutilizar Python 3.12.11 e as dependências já fixadas na etapa 2. Os checkpoints iniciais definidos em `config.json` são `yolo11n.pt` para detecção e `yolo11n-cls.pt` para classificação. Salvar pesos treinados separados. O detector genérico pré-treinado será apenas o ponto de partida; não substituirá o treinamento no PIO.

A inferência deverá poder ser executada em CPU. A etapa 2 já verificou CPU e GPU, com CUDA disponível na RTX 4070 Ti SUPER de 16 GB. Medir o tempo de treinamento nas primeiras épocas para definir seu orçamento. Não contratar infraestrutura como parte deste plano.

Estrutura inicial proposta:

```text
analyze.py
config.json
requirements.txt
.gitignore
src/
    pipeline.py
    reporting.py
scripts/
    prepare_data.py
    train_detector.py
    suggest_health_boxes.py
    train_classifier.py
    evaluate.py
tests/
    test_pipeline.py
    test_reporting.py
data/                   # datasets locais, fora do Git
models/                 # pesos locais, fora do Git
outputs/                # resultados locais, fora do Git
docs/
    plano-mvp.md
    experimentos.md
```

Priorizar legibilidade: funções pequenas, nomes claros e responsabilidades separadas. Reaproveitar `src/preparation` e a página de revisão existentes. Evitar camadas de serviços, sistemas de plugins, gerenciadores de experimentos e empacotamento para distribuição neste primeiro momento.

## 4. Etapas de implementação

### Etapa 1 — Alinhar requisitos e verificar os dados — realizada

Os itens abaixo registram o trabalho realizado no escopo original de três classes. Preservar a auditoria histórica; a adaptação binária será aplicada a partir da etapa 3.

- Atualizar `docs/requisitos.md` para explicitar múltiplas aves por imagem, detecção, contagem, recortes e relatório. Ajustar RN01 e CA-RF03 para que as três classes se apliquem a cada ave com recorte válido; imagens sem detecções não recebem uma classe de saúde.
- Confirmar acesso, condições de uso, estrutura e anotações dos dois datasets citados no README. Os arquivos foram disponibilizados localmente e inspecionados na etapa 1; o inventário e as pendências estão em [experimentos](experimentos.md).
- No PIO, conferir imagens, caixas e classe de detecção em uma amostra visual, incluindo cenas densas e aves parcialmente visíveis.
- No dataset de saúde, separar RGB de térmicas, contar amostras por classe e verificar se os rótulos realmente correspondem a `healthy`, `sick` e `dead`.
- Verificar se os exemplos de saúde mostram uma única ave. Se houver múltiplas aves, usar anotações individuais para produzir recortes; não atribuir automaticamente o rótulo da imagem a todos os animais.
- Registrar limitações: o PIO pode não conter exemplos suficientes de aves mortas e o dataset de saúde pode diferir bastante dos recortes produzidos pelo detector.

**Entrega:** requisitos alinhados e inventário simples dos dados em `docs/experimentos.md`.

**Situação em 30/09/2026:** auditoria e alinhamento realizados. Foram confirmadas as licenças e identificados vazamento entre divisões do PIO, caixas sem área e ausência de rótulos individuais nas imagens de saúde com múltiplas aves. A inspeção está registrada; a condição de dados prontos para treinamento ainda não foi atendida. A etapa 2 deve incorporar essas correções, e o classificador depende da revisão dos recortes.

**Encaminhamento no plano revisado:** a auditoria foi realizada e o PIO já foi preparado na etapa 2. As lacunas do dataset de saúde serão tratadas na etapa 3. Não inventar rótulos nem converter outras condições patológicas em `dead` ou `healthy`.

### Etapa 2 — Preparar ambiente e divisões dos datasets — implementação disponível

Reaproveitar a implementação existente. Os itens abaixo descrevem a preparação originalmente prevista; a finalização dos recortes de saúde foi transferida para a etapa 3, usando um subconjunto binário.

- Criar ambiente virtual, dependências fixadas, configuração e `.gitignore` para dados, pesos, resultados e ambiente local.
- Preservar divisões oficiais quando adequadas. Caso seja necessário criar divisões, adotar inicialmente 70% para treino, 15% para validação e 15% para teste, registrando a semente e a lista de arquivos.
- Manter imagens do mesmo animal, sequência ou sessão no mesmo conjunto, conforme os metadados disponíveis. Procurar duplicatas para reduzir vazamento entre treino e teste.
- Separar imagens de origem antes de extrair recortes. Fazer aumentos de dados somente no treinamento.
- Preparar o PIO no formato de detecção e os dados RGB nas três classes de classificação. Verificar representação das classes em cada conjunto.

**Entregue:** ambiente, configuração do detector, preparação reproduzível do PIO, scripts e ferramenta de revisão do classificador. Os diretórios reais de classificação ainda dependem dos recortes aprovados.

**Situação em 01/10/2026:** ambiente local criado e verificado em CPU/GPU; PIO preparado com 1.229 imagens: 870 de treino, 171 de validação e 188 de teste, sem hashes ou grupos conhecidos compartilhados. Scripts e ferramenta local de revisão implementados e testados. A fila original contém 598 imagens RGB pendentes; o plano revisado permite selecionar somente parte de `healthy` e `dead`. As instruções em [preparação dos dados](preparacao-dados.md) descrevem a implementação atual, que ainda exige três classes e revisão completa. Não considerar a seleção binária já implementada.

**Condição para avançar:** a leitura das três divisões do PIO já foi verificada; iniciar o treinamento do detector sem aguardar a revisão de saúde. Preservar o teste reservado e os arquivos originais. Não refazer o ambiente ou as divisões do PIO para adotar o escopo reduzido.

### Etapa 3 — Treinar os modelos e preparar o subconjunto binário

#### 3.1. Treinar primeiro o detector

- Implementar `scripts/train_detector.py`, usando o PIO já preparado e o checkpoint de detecção configurado.
- Executar um treino curto para verificar o fluxo e medir o tempo por época. Definir o orçamento do treinamento a partir dessa medição, reservando tempo para integração e demonstração.
- Ajustar o detector para a classe `chicken`, selecionar o checkpoint pela validação e salvar `models/detector.pt`.
- Conferir algumas detecções visualmente e registrar parâmetros, semente, versões, checkpoint de origem e divisão dos dados. Não usar o teste para selecionar parâmetros.

**Entrega:** detector treinado que retorna caixas em fotos reais. Seu treinamento não depende da revisão do dataset de saúde.

#### 3.2. Sugerir caixas e revisar um subconjunto

- Implementar `scripts/suggest_health_boxes.py` para aplicar o detector treinado às imagens RGB de `healthy` e `dead`.
- Começar com uma pequena amostra das duas classes para conferir se as sugestões economizam trabalho. Se forem ruins, passar à marcação manual apenas do subconjunto escolhido.
- Salvar sugestões, confiança da detecção e versão do detector em arquivo separado. Adaptar a ferramenta existente para aceitar, ajustar ou excluir sugestões, preservando CSV original e decisões já revisadas.
- Manter sugestões automáticas como pendentes até revisão. Em imagens com várias detecções, exigir seleção explícita da ave; não escolher automaticamente a maior caixa nem atribuir a classe da foto a todos os animais. Sem detecção, permitir desenhar a caixa manualmente.
- Selecionar inicialmente **30–50 recortes utilizáveis por classe**, buscando variedade de enquadramentos e condições. Essa é uma meta de trabalho para o protótipo, não garantia de desempenho ou quantidade suficiente para uma avaliação confiável.
- Excluir exemplos ambíguos. Não inferir a condição de saúde a partir da confiança do detector.

**Entrega:** manifesto do subconjunto binário com origem, hash, caixa, classe, decisão de revisão e grupo de captura quando conhecido. Não é necessário revisar `sick` nem todas as imagens restantes para essa entrega.

#### 3.3. Preparar o subconjunto e treinar o classificador

- Atualizar configuração, README, requisitos, guia de preparação e testes para `healthy`/`dead`, preservando o histórico da auditoria de três classes.
- Adaptar o exportador para receber uma seleção explícita e exigir revisão completa **dessa seleção**. As imagens não selecionadas permanecem fora do treino, sem aprovação automática nem falsa indicação de erro.
- Gerar o dataset binário somente com recortes aprovados, sem imagens térmicas e sem reclassificar `sick` como `healthy`.
- Preservar hashes, grupos conhecidos e vínculos com a foto de origem. Atribuir a divisão à imagem antes de gerar recortes e aplicar aumentos somente no treinamento.
- Quando houver grupos suficientes, buscar 70/15/15, mantendo grupos inteiros e as duas classes em cada divisão. Reservar o teste para a avaliação final.
- Implementar `scripts/train_classifier.py`, ajustar o checkpoint pequeno de classificação e salvar `models/classifier.pt`, o mapeamento binário e seus metadados.
- Examinar erros de `dead`, especialmente aves descansando previstas como mortas e aves mortas previstas como `healthy`. Limitar os ajustes ao necessário para a primeira demonstração.

**Se faltarem grupos independentes:** não inventar sessões nem dividir frames relacionados para apresentar um teste como independente. O exportador atual rejeita grupos insuficientes; qualquer modo de treinamento apenas demonstrativo deve ser implementado explicitamente e identificado nos metadados. Nesse modo, registrar orçamento fixo de treinamento e ausência de seleção por validação independente. Imagens de treino reutilizadas na demonstração devem ser identificadas como tal, sem métricas de generalização.

**Entrega:** os dois pesos treinados, suas versões, o mapeamento de classes, manifesto dos recortes utilizados e registro das limitações dos dados.

**Condição para avançar:** inferência real com os dois modelos, caixas produzidas pelo detector e classe/confiança retornadas pelo classificador. Não iniciar busca extensa de arquiteturas ou hiperparâmetros. Um treinamento demonstrativo não substitui a avaliação futura com dados independentes.

### Etapa 4 — Integrar a análise de uma imagem

- Implementar o carregamento dos pesos uma vez por execução.
- Aplicar os parâmetros de detecção definidos na validação e limitar caixas às dimensões da imagem, descartando caixas sem área.
- Conferir o limite máximo de detecções para que ele não corte artificialmente a contagem em cenas densas. Registrar esse parâmetro junto ao limiar de confiança e ao tamanho de entrada.
- Recortar cada caixa válida, aplicar o pré-processamento do classificador binário e associar `healthy` ou `dead` ao identificador local da detecção.
- Manter separadas a confiança da detecção e a confiança da classificação. Não assumir a ordem das classes: usar o mapeamento salvo com o modelo.
- Produzir resumo, imagem anotada e relatório. Todo resultado `dead`, inclusive com confiança baixa, deve aparecer como candidato à verificação humana.
- Tratar imagem inválida, peso ausente ou incompatível e diretório de saída indisponível com mensagem clara e saída de erro.

**Entrega:** o comando de análise funciona do início ao fim com os dois modelos treinados.

**Condição para avançar:** a contagem, as caixas, os registros individuais e o resumo são coerentes entre si; a imagem original permanece preservada.

### Etapa 5 — Avaliar, demonstrar e documentar

- Avaliar o detector no teste reservado: precision, recall, mAP@50 e mAP@50-95. Inspecionar também erros de contagem e sobreposição de aves.
- Avaliar o classificador no teste reservado, quando disponível: acurácia, precisão, recall e F1 nas duas classes, suporte e matriz de confusão, destacando erros de `dead`. Identificar o conjunto avaliado e suas limitações. Sem teste independente, registrar “avaliação independente pendente”, sem apresentar resultados de treino ou demonstração como prova de generalização.
- Separar esses resultados da avaliação integrada. Bom desempenho nos datasets isolados não demonstra que o classificador funciona nos recortes de fotos de granja.
- Demonstrar o fluxo completo em fotos reais, informando se foram usadas no treinamento e se possuem rótulos revisados. Quando houver exemplos independentes disponíveis, avaliar também esses casos. Não reutilizar imagens para ajuste e continuar chamando-as de teste.
- Na avaliação integrada de `dead`, contar também aves mortas que o detector não encontrou. Se não houver exemplos rotulados suficientes, registrar a avaliação como qualitativa e a identificação de mortalidade como ainda não validada.
- Medir o tempo total por imagem e registrar hardware, resolução e quantidade de detecções. O RNF01 não define um limite de latência; não assumir compromisso de tempo real.
- Documentar instalação, obtenção dos pesos, preparação dos dados, comandos de treino, avaliação, análise e uma demonstração reproduzível.

**Entrega:** MVP local demonstrável, exemplos de saída e relatório de avaliação em `docs/experimentos.md`.

**Condição de conclusão:** fluxo completo com dois modelos treinados, critérios funcionais abaixo atendidos, resultados verificáveis e limitações registradas. Não há meta numérica de acurácia para essa entrega. A avaliação independente pode permanecer pendente quando faltarem dados adequados, mas isso deve constar explicitamente no relatório; a demonstração funcional não equivale à validação para uso operacional na granja.

## 5. Contrato mínimo de saída

O `report.json` deverá conter:

- Identificador da análise, data e horário com fuso, nome/caminho da imagem, dimensões e tempo de processamento.
- Identificadores e versões dos dois modelos, mapeamento de classes e parâmetros de inferência.
- Total detectado, total classificado, quantidade e percentual de `healthy` e `dead` e quantidade de candidatos à verificação por previsão `dead`.
- Para cada ave: identificador válido apenas nessa análise, caixa em pixels `[x1, y1, x2, y2]`, confiança da detecção, classe e confiança da classificação.
- Caminho da imagem anotada e aviso de que o resultado representa uma condição aparente que requer verificação humana. Informar que o modelo binário não avalia a classe `sick`.

Regras de consistência:

- Em uma análise concluída com sucesso, `healthy + dead = total_classificado = total_detectado`.
- Os percentuais usam o total detectado como denominador e representam somente as aves detectadas naquela imagem, não a mortalidade de todo o plantel.
- Sem detecções: totais e percentuais iguais a zero, lista vazia e mensagem “nenhuma ave detectada”. Isso não confirma ausência de aves na foto.
- Se um recorte válido não puder ser classificado, a execução deve informar falha, sem apresentar um relatório completo de sucesso ou inventar uma classe.
- Confiança é a pontuação do modelo; não deve ser apresentada como certeza clínica nem como probabilidade calibrada sem avaliação específica.

## 6. Critérios de aceitação e verificações

| Cenário | Resultado esperado |
| --- | --- |
| Foto RGB válida com várias aves | Inferência real, caixas, recortes, classes e dois arquivos de saída |
| Ave prevista como `dead` | Identificador localizável na imagem e indicação de verificação humana |
| Classificação binária | Somente `healthy` e `dead`; nenhuma imagem `sick` renomeada como saudável |
| Nenhuma detecção | Resumo zerado, lista vazia e nenhuma divisão por zero |
| Arquivo inválido ou modelo ausente | Mensagem compreensível e execução encerrada com erro |
| Caixa na borda da imagem | Recorte limitado à imagem e sem região vazia |
| Resultado agregado | Soma das classes consistente com total detectado |
| Registro da análise | Versões dos dois modelos e parâmetros presentes no JSON |
| Nova instalação | Execução possível seguindo os passos documentados |

Preservar os testes existentes que continuam aplicáveis e adaptar as regras de classes e seleção do classificador. Automatizar as verificações essenciais de agregação, ausência de detecções, recortes nas bordas e associação entre caixa e classificação. Resultados controlados podem ser usados nesses testes, mas a aceitação exige uma execução completa com pesos reais. Inspecionar a imagem anotada e executar a demonstração seguindo o README.

## 7. Prioridade e sequência

**Próxima ação: etapa 3.1, treinar o detector com o PIO já preparado.**

```text
Etapas 1 e 2 existentes
    → treinar detector
    → sugerir caixas e revisar subconjunto healthy/dead
    → preparar recortes e treinar classificador binário
    → integrar os dois modelos
    → verificar, documentar e demonstrar
```

Priorizar uma primeira execução completa antes de ampliar dados ou ajustar hiperparâmetros. Medir o tempo dos primeiros treinos e limitar tentativas para preservar tempo de integração. A quantidade de épocas depende dessa medição; não prometer desempenho mínimo sem evidência.

Se as sugestões de caixas forem ruins, marcar manualmente apenas o subconjunto selecionado. Se faltarem dados independentes, restringir a alegação da entrega a demonstração funcional, registrando a pendência. Se um dos modelos não puder ser treinado, o MVP ainda não estará concluído; resultados simulados não substituem nenhum dos modelos.

Após a entrega, retomar a classe `sick`, ampliar a revisão e a diversidade dos dados, obter grupos de captura confiáveis e avaliar a solução em imagens independentes de granjas. Interface visual da aplicação, histórico, PDF e implantação remota continuam fora dessa entrega.
