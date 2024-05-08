from .base_code_block import BaseCodeBlock
from typing import Callable, Any


class FunctionCodeBlock(BaseCodeBlock):
    def __init__(
        self, func: Callable[[Any], Any], network_enabled: bool = False, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.network_enabled = network_enabled
        self.func = func

    def exec(self, **kwargs):
        return self.func(**kwargs)
