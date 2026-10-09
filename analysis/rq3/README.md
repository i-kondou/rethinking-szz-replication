# Disagreement analysis

- [Classification](classification.json): one primary category per case, not necessarily shared by all three runs; saved reviews, not a new independent assessment.
- Check the oracle first: invalid oracle → oracle error; defensible alternatives due to definition/attribution → ambiguous; valid oracle and wrong answer → Claude Code error.
- Raw answers: `results/raw/`.

## Claude Code was incorrect (6 cases)

- <a id="case-921"></a>921: selected calendar-export code instead of the removal of timezone settings.
- <a id="case-1065"></a>1065: selected multi-measurement code instead of the division-to-remainder change.
- <a id="case-1666"></a>1666: one run explained the removed early return but selected a later resource-closing commit; two selected the oracle.
- <a id="case-1991"></a>1991: one run selected a total-page-count change instead of the current-page boundary; two selected the oracle.
- <a id="case-2602"></a>2602: selected a later TickCounter refactoring instead of the initialization change exposing a null city.
- <a id="case-2854"></a>2854: two runs selected an incomplete fix instead of the removal of the class-loader setting; one selected the oracle.

## Ambiguous or incomplete BIC (9 cases)

- <a id="case-313"></a>313: unsafe set modification existed earlier; the oracle triggered it for expired alarms. One run selected a later file split.
- <a id="case-399"></a>399: double escaping existed earlier; the oracle reactivated it for explicitly supplied port 6789.
- <a id="case-717"></a>717: earlier code appended rather than prepended; the oracle changed default handling and triggered the ordering failure.
- <a id="case-2513"></a>2513: earlier name-comparison logic was reused for static imports; bypassing the self-import guard triggered the unchanged BFC-added test.
- <a id="case-2357"></a>2357: discussed the introducing commit but returned `NONE`, treating an unused-variable warning as nonfunctional.
- <a id="case-3521"></a>3521: attribution depended on whether comparison overhead counted as a bug.
- <a id="case-975"></a>975: equivalent affected-file changes on different branches.
- <a id="case-1470"></a>1470: two runs selected an equivalent change on the BFC branch; one returned `NONE` for a dead-store warning. The oracle was outside the supplied ancestry.
- <a id="case-718"></a>718: the BFC fixed argument-order and row-hashing bugs; the oracle and agent identified different causes.

## Incorrect oracle labels

### Case 907

- **Oracle error:** `5c283580b0` added a blank line; `02a5f3fff3` removed a stack-frame skip in `GoogleLogContext`.
- **Evidence:** logging tests reported `postProcess()` after the change, but the user caller before it and after the BFC. Both sides of the oracle failed. Three repeats covered one-/two-level overrides and a no-override control. [Diffs](patches/907.json); [tests](tests/history/runs/claude-candidates-usage-20260912/usage-history-01/907).
- **DIO-V:** use `02a5f3fff3` for the public-history bug. Unavailable internal Google code remains an unverified explanation for the developer reference.

### Case 1121

- **Oracle error:** `3661e14674` added tests; the faulty quantifier-AST implementation already existed in root import `2b20287b17`. [Diffs](patches/1121.json).
- **DIO-V:** exclude. Earlier SVN/CPAchecker history is unresolved and Z3 was not reproduced; the public import is not established as the original introducer.

### Case 1381

- **Oracle error:** `6862f13bd9` changed iOS code; `878f010685` introduced the syntax error in Android's `CustomPieChart.java`. [Diffs](patches/1381.json).
- **DIO-V:** use `878f010685`, based on diffs; the original build was not rerun. Identical subjects alone do not establish why the label was wrong.

### Case 1728

- **Oracle error:** `cf27461bfa` preceded `19ca9570e9`, which stopped using the application context and changed the receiver's lifetime. The BFC added cleanup in `onDestroy`. [Diffs](patches/1728.json).
- **DIO-V:** use `19ca9570e9`, selected by two runs; the earlier initialization change selected by the third remains incorrect. Static evidence only, not a full Android lifecycle reproduction.

### Case 2557

- **Oracle error:** `e083434176` changed embedder controls; its parent `abfb232` already read the unsafe `runningBatchKey` state.
- **Evidence:** examples-parameter input passed before the read, failed during JUnit description construction afterward, and passed after the BFC. The 84 observations and four controls place failure before `beforeStory`. [Diffs](patches/2557.json); [tests](tests/2557/results.json).
- **DIO-V:** exclude. Multiple causal roles and the original input remain unresolved; the harness used historical classes and a rebuilt dependency fork, not the full Spring/Allure application.

### Case 2911

- **Oracle error:** `e33ec10aa4` followed two bugs: `6cfecea6c3` recorded a timestamp as a duration; `25c113f62a` bypassed a timing wrapper in primitive-key overloads.
- **Evidence:** 84 observations (7 history points × 3 overloads × 2 tracing settings × 2 repeats) found both bugs before/after the oracle and neither after the BFC. [Diffs](patches/2911.json); [tests](tests/2911/attempt002/observations.json).
- **DIO-V:** exclude this multi-cause case. The developer message points to the oracle, contrary to the tests; the harness ran one task with a recording metrics sink, not a Bookie cluster.

### Case 3530

- **Oracle error:** `84e97c4979` changed other media paths; `e98ea09934` introduced unconditional buffer rounding in the affected JPCSP path.
- **Evidence:** the original buffer-accounting method passed before `e98ea09934`, failed afterward and on both sides of the oracle, and passed after the BFC. [Diffs](patches/3530.json); [tests](tests/history/runs/java-causal-expansion-20260912/expansion-history-01/3530).
- **DIO-V:** use `e98ea09934`. Tests used a fixed codec result, not a full game/emulator.

## Check the evidence

- From the package root: `python3 -B analysis/reproduce.py --sections rq3 --numeric-only` checks saved results and source hashes without model calls.
- `tests/` retains source snapshots, harnesses and compile/test records, including original paths and comments.
- With a JDK: `python3 -B analysis/rq3/replay_313.py --output outputs/rq3-313` rebuilds case 313. Other tests retain historical dependency/JDK paths and are checked from saved results, not rerun.
