"""Treino com orçamento fixo e sem avaliação quando não há grupos independentes.

Esta adaptação usa os pontos de extensão do Ultralytics 8.3.203, versão fixada
no projeto. Não cria uma validação artificial a partir das imagens de treino.
"""

from pathlib import Path
from types import SimpleNamespace

from ultralytics.data.augment import classify_transforms
from ultralytics.models.yolo.classify.train import ClassificationTrainer
from ultralytics.utils.torch_utils import strip_optimizer


class DemonstrationTrainer(ClassificationTrainer):
    def get_dataset(self):
        root = Path(self.args.data)
        names = sorted(path.name for path in (root / "train").iterdir() if path.is_dir())
        if names != ["dead", "healthy"]:
            raise ValueError("O treino demonstrativo requer somente dead e healthy.")
        return {
            "train": root / "train",
            "val": None,
            "test": None,
            "nc": len(names),
            "names": dict(enumerate(names)),
            "channels": 3,
        }

    def get_dataloader(self, dataset_path, batch_size=16, rank=0, mode="train"):
        if mode == "val":
            self.model.transforms = classify_transforms(size=self.args.imgsz)
            return []
        return super().get_dataloader(dataset_path, batch_size, rank, mode)

    def get_validator(self):
        self.loss_names = ["loss"]
        return SimpleNamespace(metrics=SimpleNamespace(keys=[]))

    def label_loss_items(self, loss_items=None, prefix="train"):
        if prefix == "val":
            return [] if loss_items is None else {}
        return super().label_loss_items(loss_items, prefix)

    def validate(self):
        # O loop pede fitness para gravar checkpoints, mesmo sem validação.
        # A constante não mede desempenho nem seleciona uma época melhor.
        self.best_fitness = 0.0
        return {}, 0.0

    def final_eval(self):
        strip_optimizer(self.last)
