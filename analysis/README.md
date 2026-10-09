# Reproduce the analyses

- Use the Docker command in the [root README](../README.md).
- The runner verifies [checksums](../results/manifest.json) and regenerated values against saved results; saved answers and measurements are preserved.

## Outputs

- `rq1/`: accuracy, Holm-adjusted Wilcoxon tests, token-based cost and elapsed time.
- `rq2/`: command counts, ABC classifications, operation sequences, tables and figures.
- `rq3/`: 22 case classifications and source/test evidence checks.
- `further_analysis/`: message ablation, efficiency tests, DIO-V rescoring and overlap figures.

## Analysis rules

- Average TP/FP/FN and accuracy across repetitions; incomplete runs count as empty answers. Resource averages use completed runs.
- Score the study's 79 cases, including when historical rule-based logs contain 80. Resolve commit hashes using saved records.
- RQ2 uses recorded commands and Git-query results, without executing logged commands or downloading repositories.
- Apply the [20 manual labels](../results/inputs/rq2-manual-labels.csv); `B+C` is an unordered set. Preserve unknown and overlapping operations.
- Check the [case-3109 illustration](assets/case-3109.pdf) against its three logged sequences.
- [RQ3](rq3/README.md) and [performance differences](anti-patterns/README.md) reuse the saved reviews; they are not new independent assessments.
