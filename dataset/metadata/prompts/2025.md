This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: a8726173a9351b718b477ee1579a20c1b9a7a446
- Commit message: [bugfix] exist.home is not in src/org/exist/system.properties. Fixes a bug
- Diff:
```
commit a8726173a9351b718b477ee1579a20c1b9a7a446
Author: Adam Retter <adam.retter@googlemail.com>
Date:   Wed Jun 15 15:59:22 2016 +0100

    [bugfix] exist.home is not in src/org/exist/system.properties. Fixes a bug
---
 src/org/exist/jetty/JettyStart.java | 5 ++---
 1 file changed, 2 insertions(+), 3 deletions(-)

diff --git a/src/org/exist/jetty/JettyStart.java b/src/org/exist/jetty/JettyStart.java
index cf0e63034..894877632 100644
--- a/src/org/exist/jetty/JettyStart.java
+++ b/src/org/exist/jetty/JettyStart.java
@@ -129,13 +129,12 @@ public class JettyStart extends Observable implements LifeCycle.Listener {
 
         logger.info("Running as user '" 
                 + System.getProperty("user.name", "(unknown user.name)") + "'");
-
+        logger.info("[eXist Home : "
+                + System.getProperty("exist.home", "unknown") + "]");
         logger.info("[eXist Version : " 
                 + SystemProperties.getInstance().getSystemProperty("product-version", "unknown") + "]");
         logger.info("[eXist Build : " 
                 + SystemProperties.getInstance().getSystemProperty("product-build", "unknown") + "]");
-        logger.info("[eXist Home : " 
-                + SystemProperties.getInstance().getSystemProperty("exist.home", "unknown") + "]");
         logger.info("[Git commmit : " 
                 + SystemProperties.getInstance().getSystemProperty("git-commit", "unknown") + "]");
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
