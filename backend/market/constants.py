"""Shared constants for multi-asset support."""

from django.db import models


class AssetClass(models.TextChoices):
    CRYPTO = "crypto", "Crypto"
    EQUITY = "equity", "Equity"
    FOREX = "forex", "Forex"
