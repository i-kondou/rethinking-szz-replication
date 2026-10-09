This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: ab32c49df964e63f93713a2b2a44b68147e86782
- Commit message: 
- Diff:
```
commit ab32c49df964e63f93713a2b2a44b68147e86782
Author: Johannes Schindelin <johannes.schindelin@gmx.de>
Date:   Mon Jul 23 14:54:09 2012 -0500
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
