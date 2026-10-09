This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: fd8182365d1bf0e7afecbaa6413763878e43387e
- Commit message: 
- Diff:
```
commit fd8182365d1bf0e7afecbaa6413763878e43387e
Author: Mihail Muhin <Mihail.Muhin@jetbrains.com>
Date:   Wed May 27 18:13:16 2015 +0200
---
 .../source/jetbrains/mps/lang/typesystem/runtime/RuleSet.java           | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/core/typesystemEngine/source/jetbrains/mps/lang/typesystem/runtime/RuleSet.java b/core/typesystemEngine/source/jetbrains/mps/lang/typesystem/runtime/RuleSet.java
index 3923bba53778..bb4495098cc6 100644
--- a/core/typesystemEngine/source/jetbrains/mps/lang/typesystem/runtime/RuleSet.java
+++ b/core/typesystemEngine/source/jetbrains/mps/lang/typesystem/runtime/RuleSet.java
@@ -46,7 +46,7 @@ public class RuleSet<T extends IApplicableToConcept> {
 
     @Override
     protected List<SAbstractConcept> getParents(SAbstractConcept nextConcept) {
-      return SConceptOperations.getAllSuperConcepts(nextConcept, false);
+      return SConceptOperations.getDirectSuperConcepts(nextConcept, false);
     }
 
     @Override
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
