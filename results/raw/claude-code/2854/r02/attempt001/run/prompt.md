This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 6d6fbf9de73271f747806fbd0ff21082a40d7dba
- Commit message: fixes error
- Diff:
```
commit 6d6fbf9de73271f747806fbd0ff21082a40d7dba
Author: kb634 <kb634@york.ac.uk>
Date:   Thu Jul 25 16:27:33 2019 +0100

    fixes error
---
 .../src/org/eclipse/scava/crossflow/web/CrossflowHandler.java           | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/crossflow/org.eclipse.scava.crossflow.web/src/org/eclipse/scava/crossflow/web/CrossflowHandler.java b/crossflow/org.eclipse.scava.crossflow.web/src/org/eclipse/scava/crossflow/web/CrossflowHandler.java
index 61f1c837..0647c89a 100755
--- a/crossflow/org.eclipse.scava.crossflow.web/src/org/eclipse/scava/crossflow/web/CrossflowHandler.java
+++ b/crossflow/org.eclipse.scava.crossflow.web/src/org/eclipse/scava/crossflow/web/CrossflowHandler.java
@@ -63,7 +63,7 @@ public class CrossflowHandler implements Crossflow.Iface {
 
 			Workflow workflow = (Workflow) classLoader.loadClass(experiment.getClassName())
 					.getConstructor(Mode.class).newInstance(mode);
-
+			workflow.getSerializer().setClassloader(classLoader);
 			workflow.setInstanceId(experimentId);
 			workflow.createBroker(false);
 			File cacheDir = new File(servlet.getServletContext().getRealPath("experiments/" + experimentId + "/cache"));
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
