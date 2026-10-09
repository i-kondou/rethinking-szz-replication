This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: cdaa42c57b0c4dc5db9058cf2cbb112768940e30
- Commit message: 
- Diff:
```
commit cdaa42c57b0c4dc5db9058cf2cbb112768940e30
Author: vigorouscoding <kai.schwaiger@structr.com>
Date:   Tue Feb 28 17:28:25 2017 +0100
---
 structr-ui/src/main/java/org/structr/web/entity/AbstractFile.java | 7 ++++++-
 1 file changed, 6 insertions(+), 1 deletion(-)

diff --git a/structr-ui/src/main/java/org/structr/web/entity/AbstractFile.java b/structr-ui/src/main/java/org/structr/web/entity/AbstractFile.java
index 5bb005d96..ab8131d11 100644
--- a/structr-ui/src/main/java/org/structr/web/entity/AbstractFile.java
+++ b/structr-ui/src/main/java/org/structr/web/entity/AbstractFile.java
@@ -92,7 +92,12 @@ public class AbstractFile extends LinkedTreeNode<FileChildren, FileSiblings, Abs
 	@Override
 	public boolean onModification(final SecurityContext securityContext, final ErrorBuffer errorBuffer, final ModificationQueue modificationQueue) throws FrameworkException {
 
-		final boolean valid = validatePath(securityContext, errorBuffer);
+		boolean valid = true;
+
+		if (validatePathUniqueness) {
+			valid = validatePath(securityContext, errorBuffer);
+		}
+
 		return valid && super.onModification(securityContext, errorBuffer, modificationQueue);
 	}
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
