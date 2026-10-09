This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: d9853de000d36dd300e4b29bce34779725438770
- Commit message: JS: fix bug in parsing a number in the time formats 'hh:mm:ss' and 'hh:mm:ss.ssssss'

Fixes bug

Signed-off-by: Harry King <d.harry.king@gmail.com>
- Diff:
```
commit d9853de000d36dd300e4b29bce34779725438770
Author: Harry King <d.harry.king@gmail.com>
Date:   Wed Feb 19 10:22:41 2020 -0800

    JS: fix bug in parsing a number in the time formats 'hh:mm:ss' and 'hh:mm:ss.ssssss'
    
    Fixes bug
    
    Signed-off-by: Harry King <d.harry.king@gmail.com>
---
 src/main/java/com/jaamsim/input/Input.java | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)

diff --git a/src/main/java/com/jaamsim/input/Input.java b/src/main/java/com/jaamsim/input/Input.java
index 614fdfe17..988ec072b 100644
--- a/src/main/java/com/jaamsim/input/Input.java
+++ b/src/main/java/com/jaamsim/input/Input.java
@@ -967,7 +967,7 @@ public abstract class Input<T> {
 			ret += hh * usPerHr;
 			ret += mm * usPerMin;
 			ret += ss * usPerSec;
-			return ret;
+			return ret * 1e-6;
 		}
 
 		if (isextendfull.matcher(input).matches()) {
@@ -995,7 +995,7 @@ public abstract class Input<T> {
 			ret += mm * usPerMin;
 			ret += ss * usPerSec;
 			ret += us;
-			return ret;
+			return ret * 1e-6;
 		}
 
 		throw new InputErrorException(INP_ERR_BADDATE, input);
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
