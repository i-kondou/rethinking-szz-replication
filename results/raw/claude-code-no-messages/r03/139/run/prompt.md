This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 8e0deafda38bd86af8ce90ad8916ea3bd99fd47b
- Commit message: 
- Diff:
```
commit 8e0deafda38bd86af8ce90ad8916ea3bd99fd47b
Author: Eran Mizrahi <eranmizra@gmail.com>
Date:   Mon Apr 4 21:10:37 2011 +0300
---
 core/java/android/text/TextUtils.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/core/java/android/text/TextUtils.java b/core/java/android/text/TextUtils.java
index 88f725945..54bb57f0a 100644
--- a/core/java/android/text/TextUtils.java
+++ b/core/java/android/text/TextUtils.java
@@ -1692,7 +1692,7 @@ public class TextUtils {
                (c >= 0xFB1D && c <= 0xFB4F) ||
                (c >= 0x0600 && c <= 0x07BF) ||
                (c >= 0xFB50 && c <= 0xFDFF) ||
-               (c >= 0xFE70 && c <= 0xFEFF)    ;
+               (c >= 0xFE70 && c <= 0xFEFE)    ;
     }
 
     /**
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
