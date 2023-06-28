import copy
from typing import Iterator, Optional

from hbutils.reflection import context
from tqdm.auto import tqdm

from ..action import BaseAction
from ..export import BaseExporter
from ..model import ImageItem


class BaseDataSource:
    def _iter(self) -> Iterator[ImageItem]:
        raise NotImplementedError

    def _iter_from(self) -> Iterator[ImageItem]:
        ctx_name = context().get('waifuc_task_name', None)
        if ctx_name:
            desc = f'{self.__class__.__name__} - {ctx_name}'
        else:
            desc = f'{self.__class__.__name__}'
        for item in tqdm(self._iter(), desc=desc):
            yield item

    def __iter__(self) -> Iterator[ImageItem]:
        yield from self._iter_from()

    def attach(self, *actions: BaseAction) -> 'AttachedDataSource':
        return AttachedDataSource(self, *actions)

    def export(self, exporter: BaseExporter, name: Optional[str] = None):
        exporter = copy.deepcopy(exporter)
        exporter.reset()
        with context().vars(waifuc_task_name=name):
            return exporter.export_from(iter(self))


class AttachedDataSource(BaseDataSource):
    def __init__(self, source: BaseDataSource, *actions: BaseAction):
        self.source = source
        self.actions = actions

    def _iter(self) -> Iterator[ImageItem]:
        t = self.source
        for action in self.actions:
            action = copy.deepcopy(action)
            action.reset()
            t = action.iter_from(t)

        yield from t

    def _iter_from(self) -> Iterator[ImageItem]:
        yield from self._iter()
