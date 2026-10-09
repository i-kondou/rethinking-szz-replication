"""Parse final BIC answers, not intermediate hash mentions."""
import json,re
from pathlib import Path
BIC_ITEM_HASH=re.compile(r"^\s*([0-9a-fA-F]{7,40})(?![0-9a-fA-F])")

def load_result_entry(jsonl_path: Path) -> dict | None:
    """Find and return the last entry with type == 'result' from a jsonl file."""
    result = None
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") == "result":
                result = obj
    return result

def extract_bic_hashes(result_text: str) -> list[str]:
    """
    Extract BIC hashes from the result text.

    Looks for lines matching `BIC: <hash1>, <hash2>, ...` or `BIC: NONE`.
    Returns the LAST match in the text (the final answer).

    A candidate item may append parenthetical prose such as a commit title or
    confidence label.  The parser accepts only the leading 7--40 hexadecimal
    token in each comma-separated item.  Hex-like text later in an annotation
    is not treated as an additional prediction.
    """
    matches = re.findall(r"BIC\s*:\s*(.+?)(?:\n|$)", result_text, flags=re.IGNORECASE)
    if not matches:
        return []
    last_match = matches[-1].strip()
    if re.match(r"^NONE\b", last_match, flags=re.IGNORECASE):
        return []
    hashes = []
    for item in last_match.split(","):
        match = BIC_ITEM_HASH.match(item)
        if match is not None:
            hashes.append(match.group(1))
    # Deduplicate, preserving order
    seen = set()
    uniq = []
    for h in hashes:
        if h.lower() not in seen:
            seen.add(h.lower())
            uniq.append(h.lower())
    return uniq
