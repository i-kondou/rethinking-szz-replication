This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: cc0094c538cb3499bf19116965b70d6249ceaa94
- Commit message: 
- Diff:
```
commit cc0094c538cb3499bf19116965b70d6249ceaa94
Author: Yizhou Zhang <yizhou@cs.cornell.edu>
Date:   Tue Sep 6 18:36:15 2016 -0400
---
 src/polyglot/main/Options.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/src/polyglot/main/Options.java b/src/polyglot/main/Options.java
index 0feb8c58..47fe2561 100644
--- a/src/polyglot/main/Options.java
+++ b/src/polyglot/main/Options.java
@@ -763,7 +763,7 @@ public class Options {
     }
 
     protected void addBootCP(List<File> value) {
-        bootclasspathDirectories().addAll(value);
+        bootclasspathDirectories().addAll(0, value);
     }
 
     protected void setSourcepath(List<File> value) {
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
