## Trabalhos científicos

### [YOLO-Based Model for Automatic Detection of Broiler Pathological Phenomena through Visual and Thermal Images in Intensive Poultry Houses](https://www.mdpi.com/2077-0472/13/8/1527)

Elmessery et al., 2023. Publicado na revista **Agriculture**.

O trabalho utiliza modelos baseados em **YOLOv5, YOLOv7 e YOLOv8** para detectar e classificar condições patológicas em frangos de corte utilizando imagens RGB e térmicas.

O dataset utilizado possui aproximadamente **10 mil imagens e 50 mil anotações**, incluindo categorias como aves saudáveis, letárgicas, estressadas, com problemas nos olhos, tendões deslocados e alterações no papo.

O YOLOv8 utilizando imagens térmicas apresentou os melhores resultados, chegando a **mAP50 de 0,988 e F1-score de 0,972**.

Esse trabalho é especialmente relevante para o **poultry-master**, pois demonstra a viabilidade de utilizar YOLO e imagens visuais ou térmicas para identificar condições anormais em aves dentro de ambientes de criação.

Também serve como referência para uma possível evolução futura utilizando imagens térmicas.

[Artigo na MDPI](https://www.mdpi.com/2077-0472/13/8/1527)

---

### [A review on computer vision systems in monitoring of poultry: A welfare perspective](https://www.sciencedirect.com/science/article/pii/S2589721720300258)

Publicado em 2020 na revista **Artificial Intelligence in Agriculture**.

O artigo apresenta uma revisão das principais aplicações de visão computacional no monitoramento de aves, incluindo abordagens tradicionais de machine learning e técnicas modernas de deep learning.

Entre as aplicações discutidas estão monitoramento de comportamento, saúde e bem-estar das aves. O trabalho também destaca problemas comuns encontrados nesse tipo de sistema, como **variações de iluminação, oclusão entre aves e falta de datasets devidamente anotados**.

Esses problemas são diretamente relacionados ao **poultry-master**, principalmente caso o modelo seja testado posteriormente com imagens reais de uma granja, onde várias aves podem aparecer juntas e as condições de iluminação são menos controladas.

[ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2589721720300258)

---

### [Computer vision models for precision poultry farming: A narrative review of behavioral and welfare monitoring studies](https://pmc.ncbi.nlm.nih.gov/articles/PMC13091050/)

Paneru et al., 2026. Publicado na revista **Poultry Science**.

O trabalho revisa aplicações recentes de visão computacional em **Precision Poultry Farming**, com atenção especial para modelos da família YOLO.

Foram analisados **82 trabalhos científicos**, incluindo aplicações para detecção e identificação de aves, reconhecimento de comportamento, contagem, rastreamento, avaliação de saúde e doenças e análise da distribuição dos animais dentro dos galpões.

A revisão mostra que modelos YOLO passaram a ser amplamente utilizados no setor avícola principalmente a partir de 2021.

É uma referência importante para justificar a escolha dessa família de modelos no **poultry-master** e também para identificar possíveis extensões futuras do projeto.

[PubMed Central](https://pmc.ncbi.nlm.nih.gov/articles/PMC13091050/)

---

### [A Systematic Review of Precision Livestock Farming in the Poultry Sector: Is Technology Focussed on Improving Bird Welfare?](https://pmc.ncbi.nlm.nih.gov/articles/PMC6770384/)

Publicado em 2019 na revista **Animals**.

O estudo realiza uma revisão sistemática de **264 publicações** relacionadas à utilização de tecnologias de Precision Livestock Farming no setor avícola.

Entre as tecnologias analisadas estão câmeras, sensores ambientais e dispositivos utilizados para monitorar automaticamente saúde, comportamento e bem-estar das aves.

O estudo aponta que grande parte das soluções encontradas na literatura ainda estava em estágio de protótipo e que câmeras constituíam uma das principais tecnologias utilizadas para monitoramento não invasivo.

O trabalho serve como referência mais ampla para posicionar o **poultry-master** dentro do conceito de **avicultura de precisão**.

[PubMed Central](https://pmc.ncbi.nlm.nih.gov/articles/PMC6770384/)

---

### [Review: Automated techniques for monitoring the behaviour and welfare of broilers and laying hens: towards the goal of precision livestock farming](https://www.sciencedirect.com/science/article/pii/S1751731119002155)

Li et al., 2020. Publicado na revista **Animal**.

O trabalho discute técnicas utilizadas para monitoramento automático de frangos de corte e galinhas poedeiras, incluindo análise de som, sensores, RFID e **processamento de imagens**.

Os autores destacam que sistemas baseados em imagens podem ser utilizados para acompanhar comportamento e identificar situações anormais de forma automática e não invasiva.

O artigo também discute uma dificuldade relevante para o **poultry-master**: aplicar técnicas desenvolvidas em condições experimentais a ambientes comerciais com milhares de aves.

[ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1751731119002155)

## Projetos técnicos relacionados

### AI/ML Computer Vision for the Next Generation Poultry Farms

Projeto europeu voltado ao desenvolvimento de sistemas de monitoramento de granjas utilizando **câmeras, inteligência artificial, edge computing e sensores**.

Os modelos desenvolvidos foram direcionados a tarefas como detecção e segmentação de aves, contagem, estimativa de peso e identificação de animais mortos.

É uma das referências técnicas mais próximas da possível evolução futura do **poultry-master**, pois apresenta o uso de câmeras instaladas na própria granja para realizar monitoramento automatizado.

[Projeto FF4EuroHPC](https://www.ff4eurohpc.eu/en/success-stories/2022111918411196/aiml_computer_vision_for_the_next_generation_poultry_farms)

## Datasets e referências para dados

### [A survey of open-access datasets for computer vision in precision poultry farming](https://www.sciencedirect.com/science/article/pii/S0032579125000215)

Publicado na revista **Poultry Science**, o estudo reúne e analisa datasets públicos utilizados em aplicações de visão computacional para avicultura.

A revisão inclui conjuntos voltados para detecção de aves, comportamento, saúde e classificação de condições anormais.

Entre os datasets discutidos está o conjunto de imagens RGB e térmicas utilizado por Elmessery et al. para classificação de condições de saúde.

Esse trabalho pode ser utilizado como referência para avaliar se o dataset inicialmente escolhido pelo **poultry-master** é suficiente ou se existem outros conjuntos que possam ser utilizados futuramente para treinamento e validação.

[ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0032579125000215)