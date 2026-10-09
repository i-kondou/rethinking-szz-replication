This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 16abeae70ca970bc022e0c9b9b07d98fc1a47a71
- Commit message: 
- Diff:
```
commit 16abeae70ca970bc022e0c9b9b07d98fc1a47a71
Author: Alex Kuiper <alex@nightwhistler.net>
Date:   Mon Sep 30 09:39:55 2013 +0200
---
 src/net/nightwhistler/pageturner/view/bookview/BookView.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/src/net/nightwhistler/pageturner/view/bookview/BookView.java b/src/net/nightwhistler/pageturner/view/bookview/BookView.java
index 44f6f8e..250d088 100644
--- a/src/net/nightwhistler/pageturner/view/bookview/BookView.java
+++ b/src/net/nightwhistler/pageturner/view/bookview/BookView.java
@@ -1080,7 +1080,7 @@ public class BookView extends ScrollView implements LinkTagHandler.LinkCallBack
 
         LOG.debug( "Looking for pageNumber for index=" + index + ", position=" + position );
 		
-		int pageNum = 0;
+		int pageNum = -1;
 		
 		List<List<Integer>> pageOffsets = spine.getPageOffsets();
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
