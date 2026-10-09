This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 5c128a48829bd2caff4a061c5f4637d39c85ab6d
- Commit message: Updater: Brown paper bag fix

This fixes a bug. Basically, the bug would prevent any
shadowing (update sites overriding other update sites' files).

Signed-off-by: Johannes Schindelin <johannes.schindelin@gmx.de>
- Diff:
```
commit 5c128a48829bd2caff4a061c5f4637d39c85ab6d
Author: Johannes Schindelin <johannes.schindelin@gmx.de>
Date:   Mon Jul 23 14:54:09 2012 -0500

    Updater: Brown paper bag fix
    
    This fixes a bug. Basically, the bug would prevent any
    shadowing (update sites overriding other update sites' files).
    
    Signed-off-by: Johannes Schindelin <johannes.schindelin@gmx.de>
---
 core/updater/core/src/main/java/imagej/updater/core/XMLFileReader.java | 1 +
 1 file changed, 1 insertion(+)

diff --git a/core/updater/core/src/main/java/imagej/updater/core/XMLFileReader.java b/core/updater/core/src/main/java/imagej/updater/core/XMLFileReader.java
index 316913918..bba523ecb 100644
--- a/core/updater/core/src/main/java/imagej/updater/core/XMLFileReader.java
+++ b/core/updater/core/src/main/java/imagej/updater/core/XMLFileReader.java
@@ -117,6 +117,7 @@ public void read(final String updateSite, final InputStream in,
 		SAXException
 	{
 		this.updateSite = updateSite;
+		filesFromThisSite.clear();
 		newTimestamp = timestamp;
 
 		final InputSource inputSource = new InputSource(in);
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
