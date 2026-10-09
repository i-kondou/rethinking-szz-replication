"""Paths and small I/O helpers for independent experiment entry points."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import urllib.request

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'experiments/scripts'
sys.path[:0] = [str(SCRIPTS), str(ROOT / 'preprocess')]
import common
from common import require, load


def impl():
    return ROOT / 'experiments'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, obj):
    common.write_new(Path(path), common.json_bytes(obj))


def score(predictions, oracle):
    predictions, oracle = set(predictions), set(oracle)
    return dict(tp=len(predictions & oracle), fp=len(predictions - oracle), fn=len(oracle - predictions))


def download(url, digest, target):
    target = Path(target)
    if target.exists():
        require(sha(target) == digest, 'Existing download checksum differs')
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.download-', dir=target.parent) as tmp:
        staged = Path(tmp) / 'download'
        with urllib.request.urlopen(url, timeout=90) as response, staged.open('wb') as stream:
            shutil.copyfileobj(response, stream)
        require(sha(staged) == digest, 'Download checksum differs')
        require(not target.exists(), 'Concurrent download appeared')
        staged.rename(target)
