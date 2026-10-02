"""Deterministic reconstruction, with explicit structural failures."""
import re

def reconstruct(index):
    if index is None or index == {}:
        return None, 'missing_abstract'
    if not isinstance(index, dict):
        return None, 'invalid_abstract_index'
    positions = {}
    for word, offsets in index.items():
        if not isinstance(word, str) or not word.strip() or not isinstance(offsets, list):
            return None, 'invalid_abstract_index'
        for offset in offsets:
            if type(offset) is not int or offset < 0 or offset in positions:
                return None, 'invalid_abstract_positions'
            positions[offset] = word
    if not positions:
        return None, 'missing_abstract'
    if min(positions) != 0 or max(positions) + 1 != len(positions):
        return None, 'invalid_abstract_gaps'
    return ' '.join(positions[i] for i in range(len(positions))), None

def unusable_reason(text, policy):
    if not text or not text.strip():
        return 'empty_abstract'
    normalized = re.sub(r'\s+', ' ', text).strip().casefold()
    if normalized in {x.casefold() for x in policy['reject_exact_metadata_placeholders']}:
        return 'placeholder_abstract'
    if policy['reject_numeric_only_abstract'] and not any(c.isalpha() for c in text):
        return 'numeric_only_abstract'
    return None
