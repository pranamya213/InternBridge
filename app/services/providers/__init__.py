from .base_provider import BaseProvider
from .arbeitnow_provider import ArbeitnowProvider

def get_all_providers():
    return [
        ArbeitnowProvider()
    ]
