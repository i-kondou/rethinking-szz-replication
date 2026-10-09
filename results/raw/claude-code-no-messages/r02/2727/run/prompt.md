This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: cc2d5bb3f05c35e75fc453c6d4a880014ea4b307
- Commit message: 
- Diff:
```
commit cc2d5bb3f05c35e75fc453c6d4a880014ea4b307
Author: Jonathan McPherson <jonathan@rstudio.com>
Date:   Mon Dec 11 14:58:50 2017 -0800
---
 .../client/workbench/views/vcs/common/ConsoleProgressDialog.java       | 3 +++
 1 file changed, 3 insertions(+)

diff --git a/src/gwt/src/org/rstudio/studio/client/workbench/views/vcs/common/ConsoleProgressDialog.java b/src/gwt/src/org/rstudio/studio/client/workbench/views/vcs/common/ConsoleProgressDialog.java
index dbedddd688..0e5b0af8e6 100644
--- a/src/gwt/src/org/rstudio/studio/client/workbench/views/vcs/common/ConsoleProgressDialog.java
+++ b/src/gwt/src/org/rstudio/studio/client/workbench/views/vcs/common/ConsoleProgressDialog.java
@@ -76,6 +76,9 @@ public class ConsoleProgressDialog extends ProgressDialog
          throw new IllegalArgumentException(
                "Invalid combination of arguments to ConsoleProgressDialog");
       }
+
+      // save console process so that we can compute interaction mode below
+      consoleProcess_ = consoleProcess;
       
       if (getInteractionMode() != ConsoleProcessInfo.INTERACTION_NEVER)
       {
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
