# Plano de evolução: monitoramento por fotos sequenciais

## Objetivo

Evoluir o Poultry Master de uma análise isolada por foto para uma demonstração local que acompanha aves em uma sequência de imagens e sinaliza quando uma ave detectada permanece aparentemente imóvel por tempo prolongado.

O resultado será uma **suspeita para verificação humana**. Imobilidade pode corresponder a descanso, sono, oclusão ou falha de rastreamento; o MVP não confirma morte nem substitui a inspeção da granja.

## Decisão de escopo do MVP

Para reduzir dependências e permitir uma demonstração reproduzível, a primeira versão usará:

- Uma câmera fixa, com enquadramento e resolução constantes.
- Fotos RGB gravadas em uma pasta, em intervalos nominais de um minuto.
- Uma pasta de capturas cujos nomes contenham timestamps Unix em milissegundos (`screenshot_<timestamp_ms>_<contador>.png`) ou, para outros padrões, um manifesto CSV com o caminho e o horário de cada foto. O horário real será usado, mesmo que o intervalo varie.
- O detector de aves e os pesos já existentes para gerar caixas por foto. Não faz parte deste plano treinar ou substituir o detector.
- Associação simples de caixas entre fotos para manter um identificador temporário por trajetória.
- Uma regra temporal ajustável para sinalizar imobilidade persistente. O valor inicial proposto é cinco minutos.
- Saídas locais: imagens anotadas, `tracks.csv` e `report.json`.

A análise de foto existente será mantida. O classificador `healthy/dead` não determinará o alerta temporal nesta etapa: sua avaliação independente está pendente e ele não foi treinado para distinguir sono de imobilidade.

## Fora do escopo inicial

- Captura automática por RTSP, integração com câmera ou execução como serviço contínuo.
- Vídeo em tempo real, múltiplas câmeras ou identificação permanente da ave.
- Diagnóstico de óbito ou alerta automático para funcionários.
- KNN na primeira implementação. Sem exemplos sequenciais rotulados, não há base para treinar e avaliar esse classificador.
- Garantia de detectar todas as aves em um galpão. O teste demonstrativo será feito em uma cena controlada e documentada.

## Fluxo funcional proposto

```text
Manifesto de fotos e horários
        -> validação e ordenação temporal
        -> detecção de aves em cada foto
        -> associação de caixas e IDs temporários
        -> cálculo de deslocamento e duração observada
        -> estado da trajetória
        -> imagens anotadas + tracks.csv + report.json
        -> revisão humana dos candidatos
```

Estados mínimos por trajetória:

1. `tracking`: ave associada entre capturas, ainda sem imobilidade suficiente.
2. `stationary_candidate`: baixa movimentação aparente pelo período configurado; requer verificação humana.
3. `lost`: a trajetória deixou de ser observada pelo número configurado de capturas. Não deve ser tratada como imobilidade.

## Contrato de entrada e saída

### Entrada

Para nomes de captura reconhecidos, o programa extrai o horário e monta a sequência sem CSV. Para outros nomes, use um manifesto `sequence.csv` com pelo menos:

| Campo | Descrição |
| --- | --- |
| `image` | Caminho relativo ou absoluto da foto RGB |
| `timestamp` | Data e hora ISO 8601, preferencialmente com fuso horário |

Exemplo:

```csv
image,timestamp
frames/frame-001.jpg,2026-10-19T10:00:00-03:00
frames/frame-002.jpg,2026-10-19T10:01:00-03:00
```

O programa deve rejeitar manifesto vazio, imagem ilegível, horários inválidos e imagens com dimensões incompatíveis, com mensagem clara e código de saída diferente de zero. Horários repetidos ou fora de ordem devem ser ordenados ou rejeitados de forma explícita; a decisão deve ficar registrada no relatório.

### Saída

- `frames/`: cópias anotadas por captura, com caixa, ID temporário e estado.
- `tracks.csv`: uma linha por observação, com horário, ID, caixa, centro, deslocamento, confiança e estado.
- `report.json`: parâmetros, versão/hash do detector, resumo por trajetória, alertas candidatos e contagens por estado.
- Resumo no terminal: fotos processadas, trajetórias criadas, candidatos e erros.

O relatório deve dizer que o sinal é de **imobilidade aparente nas capturas observadas**, não uma constatação de óbito. O arquivo original não será alterado.

## Componentes a implementar

1. **Leitor de sequência** — valida manifesto, caminhos, horários e dimensões; ordena as capturas.
2. **Integração do detector existente** — reaproveita a inferência e os pesos atuais, expondo as caixas e confianças ao fluxo sequencial sem exigir que o classificador `healthy/dead` seja executado. Pode exigir um pequeno refatoramento da função atual, mas não a criação de um detector novo.
3. **Associador de trajetórias** — associa detecções consecutivas com IoU e distância entre centros normalizada pelo tamanho da caixa. Começar com correspondência gulosa, um-para-um, e limites configuráveis; registrar ambiguidades e IDs encerrados.
4. **Estimador temporal** — calcula duração observada e deslocamento dos centros entre horários reais. Permite uma captura ausente sem zerar imediatamente a trajetória; encerra após tolerância configurável.
5. **Regra de alerta** — marca candidata após cinco minutos de baixa movimentação aparente e observações suficientes. O limite e a tolerância ficam em configuração, não embutidos no código.
6. **Relatórios e anotação** — salva a evidência visual e tabular de cada trajetória e mantém a associação entre resumo e observações.

### Regra inicial de imobilidade

Começar com uma regra transparente, não com um modelo aprendido:

- Comparar os centros das caixas em capturas consecutivas.
- Normalizar o deslocamento pelo tamanho da caixa para reduzir dependência da resolução.
- Acumular tempo somente quando as observações forem compatíveis com baixa movimentação.
- Sinalizar candidato quando a duração observada atingir cinco minutos, com pelo menos quatro observações válidas nesse intervalo.
- Reiniciar a duração de imobilidade quando houver movimento acima do limiar.
- Se a ave sumir por mais que a tolerância, marcar `lost`; não acumular imobilidade durante a ausência.

Os limiares de deslocamento e associação serão parâmetros de configuração. Os primeiros valores serão calibrados com exemplos controlados e registrados no relatório; não serão descritos como parâmetros validados para granja.

## Etapas de trabalho e critérios de aceite

### Etapa 1 — Preparar uma sequência reproduzível

**Tarefas:** definir o enquadramento fixo; coletar ou selecionar uma sequência com horários; criar manifesto; verificar se as imagens abrem e têm dimensões consistentes.

**Aceite:** uma sequência de pelo menos dez minutos pode ser carregada e ordenada, e erros de arquivo ou horário são informados claramente.

**Evidência:** manifesto versionável sem imagens sensíveis, inventário das capturas e duas ou três imagens representativas autorizadas para apresentação.

### Etapa 2 — Integrar o detector existente

**Tarefas:** reutilizar `models/detector.pt` e o detector já usado pelo pipeline de foto. Se necessário, extrair a chamada de detecção para uma função que retorne caixas e confiança sem executar o classificador `healthy/dead`. Não treinar nem substituir o detector. Manter o comando de foto atual funcionando.

**Aceite:** a integração sequencial produz as mesmas caixas do detector atual para as mesmas imagens e parâmetros, inclusive para uma foto sem detecções; o fluxo existente de análise por foto continua disponível.

**Evidência:** comparação entre saída anterior e nova em um conjunto pequeno de imagens fixas.

### Etapa 3 — Associar as caixas ao longo da sequência

**Tarefas:** implementar correspondência um-para-um por IoU e distância de centros; criar e encerrar IDs; tratar detecção ausente por uma captura; registrar observações em `tracks.csv`.

**Aceite:** numa sequência controlada, as caixas compatíveis preservam IDs entre capturas; detecções novas recebem ID novo; caixas que desaparecem não permanecem indefinidamente ativas; cada observação aponta para a imagem e horário de origem.

**Evidência:** sequência curta anotada com IDs e CSV correspondente revisados visualmente.

### Etapa 4 — Detectar imobilidade persistente

**Tarefas:** calcular deslocamento normalizado; implementar estados `tracking`, `stationary_candidate` e `lost`; permitir configurar o limite de duração, movimento e capturas ausentes.

**Aceite:** teste controlado confirma que movimento reseta a duração, cinco minutos de baixa movimentação geram candidato, menos de quatro observações não geram candidato e desaparecimento prolongado resulta em `lost`.

**Evidência:** pelo menos um caso ativo, um caso parado e um caso com detecção ausente, com horários e transições documentados.

### Etapa 5 — Entregar o fluxo de demonstração

**Tarefas:** criar comando `analyze_sequence.py`; gravar quadros anotados, CSV e JSON; apresentar resumo; documentar execução local e limitações.

**Aceite:** uma execução a partir de manifesto novo termina sem intervenção manual, as contagens do terminal correspondem ao JSON/CSV e os candidatos podem ser localizados nas imagens.

**Evidência:** comando reproduzível, pasta de saída, imagens anotadas e relatório.

## Validação mínima

O conjunto de demonstração deve incluir pelo menos três sequências curtas, com câmera parada e condições documentadas: movimento frequente, descanso/sono e um alvo que permaneça parado durante a janela. Para cada sequência, revisar manualmente uma amostra das trajetórias e anotar os horários em que a regra deveria ou não sinalizar.

Medir e reportar:

- Percentual de observações em que uma trajetória mantém a associação correta, por revisão manual.
- Quantidade de trocas de ID e trajetórias fragmentadas.
- Candidatos gerados por sequência e quantos correspondem a imobilidade observável na revisão.
- Atraso entre o início observado da imobilidade e o alerta.
- Efeito de fotos ausentes, iluminação e oclusão.

Esses números descrevem apenas o piloto controlado. Não serão apresentados como desempenho de mortalidade nem generalizados para outras câmeras ou granjas. Separar sequências por sessão na avaliação; não misturar capturas vizinhas da mesma sequência entre calibração e avaliação.

## KNN: etapa posterior, condicionada a dados

KNN não é necessário para o primeiro MVP. Primeiro, registrar atributos por janela temporal: deslocamento, variação da caixa, proporção de capturas observadas e duração de baixa movimentação. Depois, com autorização e rotulagem humana, montar exemplos de `active`, `resting` e `stationary_suspect`.

Só adicionar KNN se houver exemplos suficientes e independentes por sessão para avaliar se ele melhora a regra simples. A avaliação deve separar sessões e incluir métricas por classe e matriz de confusão. O KNN classificará padrões observados; não confirmará óbito.

## Reaproveitamento do conjunto do classificador

O conjunto já existente deve ser aproveitado como material de preparação e teste técnico, com limites claros:

- As imagens RGB originais de `healthy` e `dead` podem ser usadas para exercitar a leitura de imagens, executar o detector atual e gerar anotações por imagem. Como são imagens classificadas por condição e não uma sequência temporal identificada, não devem ser ordenadas artificialmente para alegar rastreamento ou comportamento.
- Os 80 recortes aprovados (40 por classe) podem ser usados para conferir o formato dos dados e a inferência estática do classificador. Eles não contêm rótulos de movimento, sono ou duração de imobilidade e não formam um conjunto independente de avaliação.
- Para testar a lógica de estados sem novas fotos, podem ser criadas sequências sintéticas a partir de detecções controladas: caixas paradas, caixas em movimento, uma detecção ausente e reaparecimento. Isso valida associação e temporização do código, mas não valida o detector em movimento nem a utilidade dos alertas na granja.
- A demonstração de comportamento temporal em condições reais ainda exige fotos sucessivas da mesma câmera com horários confiáveis. Se a fonte original tiver sequências e timestamps comprováveis, essa parte pode ser revista antes de coletar dados novos.

## Riscos e respostas

| Risco | Efeito | Resposta no MVP |
| --- | --- | --- |
| Aves dormindo ou descansando | Candidatos falsos | Usar linguagem de suspeita, janela ajustável e revisão humana; medir no piloto |
| Erros/supercontagem do detector | IDs espúrios e contagens infladas | Começar em cena controlada; salvar evidência e revisar trajetórias |
| Aves próximas ou sobrepostas | Trocas e fragmentação de IDs | Expor ambiguidade; limitar a demonstração a enquadramento adequado; medir trocas |
| Caixa estável com movimento dentro dela | Imobilidade aparente incorreta | Registrar como limitação; testar fluxo óptico dentro dos recortes numa iteração posterior |
| Câmera deslocada ou zoom alterado | Muitos IDs e movimentos artificiais | Exigir câmera fixa e dimensões consistentes; detectar mudança global de cena e suspender alertas |
| Intervalos irregulares | Duração calculada errada | Usar timestamps reais, nunca apenas número de quadros |
| Poucos dados rotulados | KNN sem avaliação confiável | Não incluir KNN no escopo inicial |

## Definition of Done

- A sequência é processada localmente por um comando documentado.
- Cada detecção tem ID temporário ou motivo explícito para não ser associada.
- O sistema distingue acompanhamento, candidato estacionário e trajetória perdida.
- O limite de cinco minutos e os demais parâmetros são ajustáveis.
- Uma captura ausente não é interpretada como imobilidade.
- A saída contém evidência visual, CSV e JSON coerentes.
- A análise isolada por foto continua disponível.
- O relatório descreve a limitação do piloto e não afirma detectar/confirmar morte.
- O piloto inclui casos de movimento, descanso e imobilidade, com revisão humana registrada.

## Estimativa revisada de esforço

Como o detector e a geração de bounding boxes já existem, o trabalho não inclui treinamento de visão computacional. Para uma pessoa com experiência básica em Python e uma sequência controlada disponível, a estimativa inicial é de **dois a quatro dias de trabalho focado**:

| Parte | Estimativa |
| --- | --- |
| Leitura/validação do manifesto e integração com o detector atual | 0,5–1 dia |
| Associação de caixas e IDs temporários | 0,5–1,5 dia |
| Regra temporal, estados e configuração | 0,5 dia |
| CLI, CSV, JSON e imagens anotadas | 0,5–1 dia |
| Ajustes com sequência controlada | 0,5–1 dia |

As partes podem se sobrepor durante a implementação; o intervalo é uma estimativa de planejamento, não um prazo garantido. A principal incerteza é manter trajetórias corretas quando as caixas do detector oscilam, se sobrepõem ou desaparecem. Uma câmera real com alta densidade de aves pode exigir mais tempo de calibração, sem que isso implique treinar um detector novo.

## Primeiro pacote necessário para iniciar a implementação

1. Uma sequência de fotos da mesma câmera, idealmente com pelo menos dez minutos e horários confiáveis; ou confirmação de que devemos criar suporte usando um conjunto de exemplo controlado.
2. Confirmação de que a câmera ficará fixa e de que imagens podem ser usadas na demonstração.
3. Uma pessoa da equipe para revisar as trajetórias e rotular os casos do piloto.

Sem câmera/dados reais, é possível implementar leitor, associação e regra temporal com imagens sintéticas ou sequências de teste. Isso valida o software, mas não o comportamento em uma granja real.
