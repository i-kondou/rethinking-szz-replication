This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: c05dbd11f9286459f19ca9262e9e5958ac9ab86b
- Commit message: Keep relative paths in spec and config dropdown

Fixes a bug that only showed the filename without
suffix.
- Diff:
```
commit c05dbd11f9286459f19ca9262e9e5958ac9ab86b
Author: Thomas Lemberger <lembergerth@gmail.com>
Date:   Wed Jun 13 22:37:23 2018 +0200

    Keep relative paths in spec and config dropdown
    
    Fixes a bug that only showed the filename without
    suffix.
---
 org.eclipse.cpacep/src/org/eclipse/cpacep/util/FileHandler.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/org.eclipse.cpacep/src/org/eclipse/cpacep/util/FileHandler.java b/org.eclipse.cpacep/src/org/eclipse/cpacep/util/FileHandler.java
index 4230f52..5277ace 100644
--- a/org.eclipse.cpacep/src/org/eclipse/cpacep/util/FileHandler.java
+++ b/org.eclipse.cpacep/src/org/eclipse/cpacep/util/FileHandler.java
@@ -23,7 +23,7 @@ public class FileHandler {
 			public FileVisitResult visitFile(Path path, BasicFileAttributes attrs) throws IOException {
 				Path fileName = path.getFileName();
 				if (pathMatcher.matches(fileName)) {
-					String tempPath = fileName.toString();
+					String tempPath = location.relativize(path).toString();
 
 					if (glob.contains(CPACEPConnector.SPEC_FILE_TYPE)) {
 						matchedList.add(tempPath.replace(CPACEPConnector.SPEC_FILE_TYPE, ""));
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
