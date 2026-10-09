This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 58902b70070a0cdef5b7d098c0c56f7685b5e0d4
- Commit message: 
- Diff:
```
commit 58902b70070a0cdef5b7d098c0c56f7685b5e0d4
Author: Greg Sheremeta <gshereme@redhat.com>
Date:   Fri Mar 27 16:54:05 2015 -0400
---
 .../bll/src/main/java/org/ovirt/engine/core/bll/RemoveVmCommand.java    | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/backend/manager/modules/bll/src/main/java/org/ovirt/engine/core/bll/RemoveVmCommand.java b/backend/manager/modules/bll/src/main/java/org/ovirt/engine/core/bll/RemoveVmCommand.java
index 0de4946a62..a028e4ab46 100644
--- a/backend/manager/modules/bll/src/main/java/org/ovirt/engine/core/bll/RemoveVmCommand.java
+++ b/backend/manager/modules/bll/src/main/java/org/ovirt/engine/core/bll/RemoveVmCommand.java
@@ -349,7 +349,7 @@ public class RemoveVmCommand<T extends RemoveVmParameters> extends VmCommand<T>
             try {
                 failedRemoveCinderDisks = future.get().getActionReturnValue();
             } catch (InterruptedException | ExecutionException e) {
-                failedRemoveCinderDisks.addAll(cinderDisks);
+                failedRemoveCinderDisks = cinderDisks;
                 log.error("Exception", e);
             }
         }
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
