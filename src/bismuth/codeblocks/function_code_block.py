from .base_code_block import BaseCodeBlock
from typing import Callable, Any


class FunctionCodeBlock(BaseCodeBlock):
    """
    Extends BaseCodeBlock. Run a python function with some requirements.
    """

    # Flag for if this block makes any network requests.
    network_enabled: bool
    # Function that will be run by `execute()`.
    func: Callable[..., Any]

    def __init__(
        self, func: Callable[..., Any], network_enabled: bool = False, *args, **kwargs
    ):
        """
        Initializes the FunctionCodeBlock with the function callable.
        """
        super().__init__(*args, **kwargs)
        self.network_enabled = network_enabled
        self.func = func

    def exec(self, *args, **kwargs: Any) -> Any:
        """
        Run a subset of arbitrary python functions as defined by Bismuth provided args and kwargs.
        """
        return self.func(*args, **kwargs)
