This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 5058c4790f047d85b938c168eb8a46f5d15cdb9c
- Commit message: 
- Diff:
```
commit 5058c4790f047d85b938c168eb8a46f5d15cdb9c
Author: Andreas Troelsen <garbagemule@gmail.com>
Date:   Sun Jul 28 11:11:25 2019 +0200
---
 src/main/java/com/garbagemule/MobArena/ArenaListener.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/src/main/java/com/garbagemule/MobArena/ArenaListener.java b/src/main/java/com/garbagemule/MobArena/ArenaListener.java
index 9400d87..59c3b49 100644
--- a/src/main/java/com/garbagemule/MobArena/ArenaListener.java
+++ b/src/main/java/com/garbagemule/MobArena/ArenaListener.java
@@ -898,7 +898,7 @@ public class ArenaListener
         Player p = (Player) event.getEntity();
 
         if (arena.isRunning()) {
-            if (lockFoodLevel) {
+            if (arena.inArena(p) && lockFoodLevel) {
                 event.setCancelled(true);
             }
         } else {
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
