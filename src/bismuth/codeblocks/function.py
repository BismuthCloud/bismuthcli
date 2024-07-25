from .base_code_block import BaseCodeBlock
from typing import ParamSpec, TypeVar, Generic, Callable


P = ParamSpec('P')
R = TypeVar('R')


class Function(BaseCodeBlock, Generic[P, R]):
    """
    Extends BaseCodeBlock. Run a python function with some requirements.
    """

    # Flag for if this block makes any network requests.
    network_enabled: bool
    # Function that will be run by `execute()`.
    func: Callable[P, R]

    def __init__(
        self, func: Callable[P, R], network_enabled: bool = False, *args, **kwargs
    ):
        """
        Initializes the FunctionCodeBlock with the function callable.
        """
        super().__init__(*args, **kwargs)
        self.network_enabled = network_enabled
        self.func = func

    def exec(self, *args: P.args, **kwargs: P.kwargs) -> R:
        """
        Run a subset of arbitrary python functions as defined by Bismuth provided args and kwargs.
        """
        return self.func(*args, **kwargs)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.exec(*args, **kwargs)
