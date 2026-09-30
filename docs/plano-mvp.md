# Plano de implementação do MVP

## 1. Objetivo e decisão de escopo

Entregar um programa local que receba uma foto RGB com múltiplas aves, detecte e conte os indivíduos, classifique cada recorte em `healthy`, `sick` ou `dead` e salve uma imagem anotada e um relatório simples para verificação humana.

Base do plano: [README](../README.md), [requisitos](requisitos.md) e [referências](referencias.md). Na criação do plano, o repositório continha apenas documentação. A auditoria da etapa 1 está registrada em [experimentos](experimentos.md).

O README define detecção e classificação de múltiplas aves. Os requisitos, que antes descreviam classificação de uma imagem individual, foram alinhados a esse fluxo na etapa 1. A classificação isolada será uma entrega intermediária, mas não será suficiente para concluir o MVP.

**A simplificação principal será na aplicação:** uma imagem por execução, interface por linha de comando e arquivos locais. Sem interface web, API, banco de dados, autenticação, serviços em nuvem, vídeo, câmeras ou histórico consultável pela aplicação. Também ficam fora imagens térmicas, diagnóstico veterinário, notificações automáticas e rastreamento.

## 2. Experiência mínima de uso

Comando proposto, a ser implementado:

```powershell
python analyze.py --image exemplos/granja.jpg --output outputs/analise-001
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
    → classificador: healthy / sick / dead
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

Fixar a versão da biblioteca e os checkpoints escolhidos durante a preparação do ambiente, após verificar compatibilidade com o hardware disponível. Usar pesos específicos para cada tarefa, não o mesmo modelo para as duas etapas. O detector genérico pré-treinado será apenas o ponto de partida; não substituirá o treinamento no PIO.

A inferência deverá poder ser executada em CPU. A disponibilidade de GPU para treinamento e o tempo de execução ainda precisam ser verificados. Não contratar infraestrutura como parte deste plano.

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

Evitar camadas de serviços, sistemas de plugins, gerenciadores de experimentos e empacotamento para distribuição neste primeiro momento.

## 4. Etapas de implementação

### Etapa 1 — Alinhar requisitos e verificar os dados

- Atualizar `docs/requisitos.md` para explicitar múltiplas aves por imagem, detecção, contagem, recortes e relatório. Ajustar RN01 e CA-RF03 para que as três classes se apliquem a cada ave com recorte válido; imagens sem detecções não recebem uma classe de saúde.
- Confirmar acesso, condições de uso, estrutura e anotações dos dois datasets citados no README. Os arquivos foram disponibilizados localmente e inspecionados na etapa 1; o inventário e as pendências estão em [experimentos](experimentos.md).
- No PIO, conferir imagens, caixas e classe de detecção em uma amostra visual, incluindo cenas densas e aves parcialmente visíveis.
- No dataset de saúde, separar RGB de térmicas, contar amostras por classe e verificar se os rótulos realmente correspondem a `healthy`, `sick` e `dead`.
- Verificar se os exemplos de saúde mostram uma única ave. Se houver múltiplas aves, usar anotações individuais para produzir recortes; não atribuir automaticamente o rótulo da imagem a todos os animais.
- Registrar limitações: o PIO pode não conter exemplos suficientes de aves mortas e o dataset de saúde pode diferir bastante dos recortes produzidos pelo detector.

**Entrega:** requisitos alinhados e inventário simples dos dados em `docs/experimentos.md`.

**Situação em 30/09/2026:** auditoria e alinhamento realizados. Foram confirmadas as licenças e identificados vazamento entre divisões do PIO, caixas sem área e ausência de rótulos individuais nas imagens de saúde com múltiplas aves. A inspeção está registrada; a condição de dados prontos para treinamento ainda não foi atendida. A etapa 2 deve incorporar essas correções, e o classificador depende da revisão dos recortes.

**Condição para avançar:** dados acessíveis e rótulos utilizáveis para as duas tarefas. Se faltarem classes ou anotações essenciais, resolver essa lacuna antes de prometer o treinamento completo. Não inventar rótulos nem converter outras condições patológicas em `dead` sem justificativa.

### Etapa 2 — Preparar ambiente e divisões dos datasets

- Criar ambiente virtual, dependências fixadas, configuração e `.gitignore` para dados, pesos, resultados e ambiente local.
- Preservar divisões oficiais quando adequadas. Caso seja necessário criar divisões, adotar inicialmente 70% para treino, 15% para validação e 15% para teste, registrando a semente e a lista de arquivos.
- Manter imagens do mesmo animal, sequência ou sessão no mesmo conjunto, conforme os metadados disponíveis. Procurar duplicatas para reduzir vazamento entre treino e teste.
- Separar imagens de origem antes de extrair recortes. Fazer aumentos de dados somente no treinamento.
- Preparar o PIO no formato de detecção e os dados RGB nas três classes de classificação. Verificar representação das classes em cada conjunto.

**Entrega:** preparação reproduzível, configuração do detector e diretórios de classificação prontos para treinamento.

**Condição para avançar:** uma amostra de cada divisão carrega corretamente e as verificações de rótulos e caixas passam. O conjunto de teste fica reservado até a avaliação final.

### Etapa 3 — Obter os dois primeiros modelos

- Executar um treino curto em um subconjunto de treino para verificar o funcionamento de cada tarefa. Isso valida o processo, não o desempenho final.
- Ajustar o detector pequeno no PIO para a classe `chicken`.
- Ajustar o classificador pequeno nos dados RGB para `healthy`, `sick` e `dead`.
- Usar a validação para selecionar checkpoints e parâmetros; não usar o teste para essas decisões.
- Examinar especialmente confusões entre aves descansando e `dead`, além de classes com poucas amostras.
- Salvar os dois pesos, o mapeamento das classes e os metadados: identificador do modelo, checkpoint inicial, versão das bibliotecas, parâmetros, semente e divisão dos dados.

**Entrega:** `models/detector.pt`, `models/classifier.pt` e metadados associados.

**Condição para avançar:** os modelos executam inferência real, o detector retorna caixas e o classificador retorna classe e confiança para recortes válidos. Nesta etapa, resultados fracos devem ser documentados; não iniciar busca extensa de arquiteturas ou hiperparâmetros.

### Etapa 4 — Integrar a análise de uma imagem

- Implementar o carregamento dos pesos uma vez por execução.
- Aplicar os parâmetros de detecção definidos na validação e limitar caixas às dimensões da imagem, descartando caixas sem área.
- Conferir o limite máximo de detecções para que ele não corte artificialmente a contagem em cenas densas. Registrar esse parâmetro junto ao limiar de confiança e ao tamanho de entrada.
- Recortar cada caixa válida, aplicar o mesmo pré-processamento do classificador usado na avaliação e associar o resultado ao identificador local da detecção.
- Manter separadas a confiança da detecção e a confiança da classificação. Não assumir a ordem das classes: usar o mapeamento salvo com o modelo.
- Produzir resumo, imagem anotada e relatório. Todo resultado `dead`, inclusive com confiança baixa, deve aparecer como candidato à verificação humana.
- Tratar imagem inválida, peso ausente ou incompatível e diretório de saída indisponível com mensagem clara e saída de erro.

**Entrega:** o comando de análise funciona do início ao fim com os dois modelos treinados.

**Condição para avançar:** a contagem, as caixas, os registros individuais e o resumo são coerentes entre si; a imagem original permanece preservada.

### Etapa 5 — Avaliar, demonstrar e documentar

- Avaliar o detector no teste reservado: precision, recall, mAP@50 e mAP@50-95. Inspecionar também erros de contagem e sobreposição de aves.
- Avaliar o classificador no teste reservado: acurácia, precisão, recall e F1 por classe, suporte por classe e matriz de confusão, destacando falsos negativos e falsos positivos de `dead`.
- Separar esses resultados da avaliação integrada. Bom desempenho nos datasets isolados não demonstra que o classificador funciona nos recortes de fotos de granja.
- Avaliar o fluxo completo em um pequeno conjunto independente com caixas e condições revisadas, incluindo possíveis aves mortas, aves descansando, oclusões e diferentes iluminações. Não reutilizar essas imagens para ajuste e continuar chamando-as de teste.
- Na avaliação integrada de `dead`, contar também aves mortas que o detector não encontrou. Se não houver exemplos rotulados suficientes, registrar a avaliação como qualitativa e a identificação de mortalidade como ainda não validada.
- Medir o tempo total por imagem e registrar hardware, resolução e quantidade de detecções. O RNF01 não define um limite de latência; não assumir compromisso de tempo real.
- Documentar instalação, obtenção dos pesos, preparação dos dados, comandos de treino, avaliação, análise e uma demonstração reproduzível.

**Entrega:** MVP local demonstrável, exemplos de saída e relatório de avaliação em `docs/experimentos.md`.

**Condição de conclusão:** todos os critérios funcionais abaixo atendidos e as limitações medidas e registradas. Os documentos não estabelecem metas numéricas de desempenho; uma demonstração funcional não equivale à validação para uso operacional na granja.

## 5. Contrato mínimo de saída

O `report.json` deverá conter:

- Identificador da análise, data e horário com fuso, nome/caminho da imagem, dimensões e tempo de processamento.
- Identificadores e versões dos dois modelos, mapeamento de classes e parâmetros de inferência.
- Total detectado, total classificado, quantidade e percentual de cada classe e quantidade de candidatos à verificação por previsão `dead`.
- Para cada ave: identificador válido apenas nessa análise, caixa em pixels `[x1, y1, x2, y2]`, confiança da detecção, classe e confiança da classificação.
- Caminho da imagem anotada e aviso de que o resultado representa uma condição aparente que requer verificação humana.

Regras de consistência:

- Em uma análise concluída com sucesso, `healthy + sick + dead = total_classificado = total_detectado`.
- Os percentuais usam o total detectado como denominador e representam somente as aves detectadas naquela imagem, não a mortalidade de todo o plantel.
- Sem detecções: totais e percentuais iguais a zero, lista vazia e mensagem “nenhuma ave detectada”. Isso não confirma ausência de aves na foto.
- Se um recorte válido não puder ser classificado, a execução deve informar falha, sem apresentar um relatório completo de sucesso ou inventar uma classe.
- Confiança é a pontuação do modelo; não deve ser apresentada como certeza clínica nem como probabilidade calibrada sem avaliação específica.

## 6. Critérios de aceitação e verificações

| Cenário | Resultado esperado |
| --- | --- |
| Foto RGB válida com várias aves | Inferência real, caixas, recortes, classes e dois arquivos de saída |
| Ave prevista como `dead` | Identificador localizável na imagem e indicação de verificação humana |
| Nenhuma detecção | Resumo zerado, lista vazia e nenhuma divisão por zero |
| Arquivo inválido ou modelo ausente | Mensagem compreensível e execução encerrada com erro |
| Caixa na borda da imagem | Recorte limitado à imagem e sem região vazia |
| Resultado agregado | Soma das classes consistente com total detectado |
| Registro da análise | Versões dos dois modelos e parâmetros presentes no JSON |
| Nova instalação | Execução possível seguindo os passos documentados |

Automatizar apenas as verificações essenciais de agregação, ausência de detecções, recortes nas bordas e associação entre caixa e classificação. Resultados controlados podem ser usados nesses testes, mas a aceitação do pipeline exige também uma execução com pesos reais. Inspecionar visualmente a imagem anotada e executar uma demonstração completa seguindo o README.

## 7. Prioridade e sequência

Executar as etapas na ordem **dados → ambiente → modelos → integração → avaliação e documentação**. A verificação dos datasets é a primeira prioridade, pois pode revelar impedimentos que nenhuma interface resolverá.

O primeiro marco é classificar um recorte com um modelo treinado; o segundo é detectar e contar aves com o detector treinado; o terceiro é executar ambos sobre uma foto e produzir as saídas; o último é demonstrar o resultado acompanhado de avaliação e limitações.

Encerrar o escopo inicial após esses marcos. Interface visual, consulta de histórico, relatórios PDF, implantação remota e otimizações adicionais ficam para uma próxima versão. Não estimar prazo fechado antes de conhecer a disponibilidade dos dados e os tempos de treinamento no hardware disponível.
