# Análise de uma foto — etapa 4

Com o ambiente instalado e os dois modelos treinados disponíveis:

```powershell
.venv/Scripts/python.exe analyze.py --image "caminho/para/foto.jpg" --output outputs/analise-001
```

Use uma pasta nova a cada execução. Caminhos de entrada e saída são relativos ao terminal; caminhos dos modelos são relativos ao arquivo de configuração. O original é preservado. A orientação EXIF é aplicada antes da detecção e as coordenadas referem-se à imagem orientada.

CPU é o padrão. Para a GPU local, acrescente `--device 0`. Outra configuração pode ser fornecida com `--config CAMINHO`. A seção `inference` de `config.json` define pesos, resolução, confiança, IoU, máximo de detecções e lote do classificador. Os modelos devem ter seus respectivos arquivos `.json` com hashes e mapeamentos de classes correspondentes.

Parâmetros iniciais: detector com entrada 640, confiança 0,25, IoU 0,7 e até 1.500 detecções; classificador com entrada 224 e lotes de 32 recortes. A resolução e o limite de detecções acompanham o treino do PIO; os limiares são valores iniciais, ainda sem otimização para o fluxo integrado. O teste reservado não foi usado para ajustá-los. Se o limite for atingido, o programa avisa sobre possível truncamento da contagem.

## Resultados

- `annotated.jpg`: caixas, identificadores, classes e confiança da classificação. Previsões `dead` aparecem em vermelho com indicação de verificação, independentemente da confiança.
- `report.json`: identificação e horário da análise, imagem e dimensões, tempo de processamento, hashes e metadados dos modelos, parâmetros, resultados individuais, contagens e percentuais. Cada ave tem confiança de detecção e classificação separadas.

Caixas sem área são descartadas; as demais são limitadas à imagem. Não há seleção por confiança do classificador: toda caixa válida recebe uma classe. Sem detecções, a lista fica vazia e os totais e percentuais ficam zerados. Isso não confirma ausência de aves.

Erros de imagem, modelos, classificação ou escrita resultam em código de saída 1. Uma pasta existente não é sobrescrita. Se uma falha de escrita deixar arquivos parciais, não considere a execução concluída: o JSON final só é publicado depois da imagem anotada. Escolha outra pasta para tentar novamente.

## Demonstração local

```powershell
.venv/Scripts/python.exe analyze.py --image "kaggle/extracted/Multimodal Chicken Datasets/dead/mati_rgb_109.jpg" --output outputs/minha-demonstracao
```

Essa foto foi usada para treinar o classificador. A execução comprova o fluxo, não generalização. Na inspeção, o detector marcou chão e partes de aves; seus resultados no PIO não se transferem automaticamente a esse dataset. O classificador também foi treinado apenas em modo demonstrativo, sem avaliação independente. Os percentuais representam as previsões sobre caixas detectadas, não a mortalidade real do plantel. Os resultados da etapa 5 estão no [guia de avaliação e demonstração](avaliacao.md).
