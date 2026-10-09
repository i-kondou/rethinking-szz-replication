# Git message scrubber

- Used by `preprocess/remove_messages.py`; creates a separate repository without changing the source.
- For study inputs, use the [root instructions](../../README.md). For standalone use, run from this directory:

```sh
PYTHONPATH=src python3 -m git_message_scrubber plan --source /path/to/repository
PYTHONPATH=src python3 -m git_message_scrubber create \
  --source /path/to/repository --output /path/to/new-bundle
PYTHONPATH=src python3 -m git_message_scrubber verify \
  /path/to/new-bundle --source /path/to/repository
```

- Default: empty all commit messages. `--keep-message REV`: preserve one message. `--revision REV`: include only that commit and its ancestors.
- `--collision-policy identity-header`: keep otherwise identical commits distinct; used in the study.
- Give agents only `repo/`, not `metadata/` (hash maps and verification records).
- Authors, timestamps, source files and branch names are not anonymized.
