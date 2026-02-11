"""Dicionário NER e Entity Resolution para normalização de textos brasileiros."""
from .normalizar import normalizar_texto, normalizar_palavra, load_dict, reload_dict, stats
from .entity_resolution import (
    is_variant, is_abbreviation_of, normalize_name, longer_name,
    confidence, full_name_tokens, full_name_compatible, split_name_canonical,
)
