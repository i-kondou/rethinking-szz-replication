# Search-design observations

- Data: DIO-V and saved RQ1 answers; identified means at least one of three answers contains the oracle BIC.
- Evidence: [review.json](review.json). The analysis verifies candidate counts and selections; causal explanations remain qualitative.

## Observations

- **LLM4SZZ:** oracle absent from all three candidate sets in 11 of 15 Claude-only cases, based on original-version logs.
- **Simple-SZZ-Agent:** oracle outside modified-file histories in cases 624, 1656 and 3459 (3 of 6 Claude-only cases).
- **AgentSZZ:** selected earlier code introductions in cases 1656, 1991 and 2529, missing the related package rename, comparison-boundary change or input preprocessing.
- **SZZ-Agent:** accepted stage-1 candidates in cases 1991, 2529 and 3459 without reaching stage 2; the oracle was absent from those candidate sets.

## Exceptions

- Finding a candidate does not guarantee selecting it: AgentSZZ also hit turn limits, and SZZ-Agent had preparation/selection failures.
- In [case 1728](../rq3/README.md#case-1728), Simple-SZZ-Agent's history included the corrected BIC, but it selected earlier commits.
