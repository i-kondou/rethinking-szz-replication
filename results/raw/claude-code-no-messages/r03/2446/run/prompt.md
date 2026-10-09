This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: e373c9aa511546b590ccb5fcff6a8ad3f0faec9e
- Commit message: 
- Diff:
```
commit e373c9aa511546b590ccb5fcff6a8ad3f0faec9e
Author: Michael Beer <michael@crate.io>
Date:   Tue Oct 24 22:24:27 2017 +0200
---
 sql/src/main/java/io/crate/executor/transport/RerouteActions.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/sql/src/main/java/io/crate/executor/transport/RerouteActions.java b/sql/src/main/java/io/crate/executor/transport/RerouteActions.java
index da5e4d923..192954e77 100644
--- a/sql/src/main/java/io/crate/executor/transport/RerouteActions.java
+++ b/sql/src/main/java/io/crate/executor/transport/RerouteActions.java
@@ -51,7 +51,7 @@ public final class RerouteActions {
 
     }
 
-    static final CompletableFuture<Long> execute(
+    public static CompletableFuture<Long> execute(
         BiConsumer<ClusterRerouteRequest, ActionListener<ClusterRerouteResponse>> rerouteAction,
         RerouteAnalyzedStatement stmt,
         Row parameters) {
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
