This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 418b068478174bf942a5e101bda962cffad011e1
- Commit message: 
- Diff:
```
commit 418b068478174bf942a5e101bda962cffad011e1
Author: Richard Taupe <richard.taupe@siemens.com>
Date:   Tue Oct 3 11:02:30 2017 +0200
---
 .../src/main/java/at/siemens/ct/jmz/diag/FastDiag.java              | 6 +++---
 1 file changed, 3 insertions(+), 3 deletions(-)

diff --git a/at.siemens.ct.jminizinc.diag/src/main/java/at/siemens/ct/jmz/diag/FastDiag.java b/at.siemens.ct.jminizinc.diag/src/main/java/at/siemens/ct/jmz/diag/FastDiag.java
index fe8706a..27bcc9d 100644
--- a/at.siemens.ct.jminizinc.diag/src/main/java/at/siemens/ct/jmz/diag/FastDiag.java
+++ b/at.siemens.ct.jminizinc.diag/src/main/java/at/siemens/ct/jmz/diag/FastDiag.java
@@ -95,10 +95,10 @@ private List<Constraint> fd(List<Constraint> D, List<Constraint> C, List<Constra
 
 		stepNumber = indent(indent, innerIndex, stepNumber);
 
-		String displayConstraintListC = progressCalback.displayConstraintList(C);
+    String displayConstraintListC = progressCalback == null ? null : progressCalback.displayConstraintList(C);
     if (displayfastDiagSteps && progressCalback != null && displayConstraintListC != null) {
 			String displayConstraintListD = progressCalback.displayConstraintList(D);
-      if (displayConstraintListD != null) {
+      if (displayConstraintListC != null && displayConstraintListD != null) {
         String fdCall = String.format("%sCall FD with D: %s, C: %s", stepNumber, displayConstraintListD.trim(),
             displayConstraintListC.trim());
         progressCalback.displayMessage(fdCall);
@@ -108,7 +108,7 @@ private List<Constraint> fd(List<Constraint> D, List<Constraint> C, List<Constra
     boolean isConsistent = consistencyChecker.isConsistent(AC, fixedModel, mznFile);
 		int q = C.size();
 
-		String displayConstraintListAC = progressCalback.displayConstraintList(AC);
+    String displayConstraintListAC = progressCalback == null ? null : progressCalback.displayConstraintList(AC);
     if (!D.isEmpty()) {
 			if (isConsistent) {
 				if (displayfastDiagSteps && progressCalback != null) {
```

Investigate the repository using local tools. Do not use web search.

When you have identified the bug-introducing commit(s), conclude your
response with the following two sections:

## Bug-Introducing Commits
BIC: <hash1>, <hash2>, ... (or "BIC: NONE")

## Reasoning
Explain:
(1) How you investigated and what led you to this candidate.
(2) What specific change in this commit you believe introduced the bug.
(3) What evidence in the repository supports this conclusion.

Be honest about uncertainty if any.
