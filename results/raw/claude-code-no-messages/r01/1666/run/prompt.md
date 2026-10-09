This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: d306f2b584e72ff605d45200d38177e6b6120f0c
- Commit message: 
- Diff:
```
commit d306f2b584e72ff605d45200d38177e6b6120f0c
Author: Avuton Olrich <avuton@gmail.com>
Date:   Mon Apr 7 19:24:28 2014 -0700
---
 MPDroid/src/com/namelessdev/mpdroid/helpers/CoverManager.java | 1 +
 1 file changed, 1 insertion(+)

diff --git a/MPDroid/src/com/namelessdev/mpdroid/helpers/CoverManager.java b/MPDroid/src/com/namelessdev/mpdroid/helpers/CoverManager.java
index d802a63f..ff2ebf2a 100644
--- a/MPDroid/src/com/namelessdev/mpdroid/helpers/CoverManager.java
+++ b/MPDroid/src/com/namelessdev/mpdroid/helpers/CoverManager.java
@@ -726,6 +726,7 @@ public class CoverManager {
                         d(CoverManager.class.getSimpleName(),
                                 "Cover downloaded for " + coverInfo.getAlbum() + " from " + url
                                         + ", size=" + coverBytes.length);
+                    break;
                 }
             } catch (Exception e) {
                 w(CoverManager.class.getSimpleName(), "Cover get bytes failure : " + e);
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
