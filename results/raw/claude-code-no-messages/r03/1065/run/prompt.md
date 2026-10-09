This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: e00995294047f1c04f9d5713bc45868f889d94c8
- Commit message: 
- Diff:
```
commit e00995294047f1c04f9d5713bc45868f889d94c8
Author: Melissa Linkert <melissa@glencoesoftware.com>
Date:   Thu Jan 7 13:17:56 2016 -0600
---
 components/formats-gpl/src/loci/formats/in/FlexReader.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/components/formats-gpl/src/loci/formats/in/FlexReader.java b/components/formats-gpl/src/loci/formats/in/FlexReader.java
index acb675542..76b731a3d 100644
--- a/components/formats-gpl/src/loci/formats/in/FlexReader.java
+++ b/components/formats-gpl/src/loci/formats/in/FlexReader.java
@@ -1369,7 +1369,7 @@ public class FlexReader extends FormatReader {
           FlexFile file = new FlexFile();
           file.row = row;
           file.column = col;
-          file.field = field % runCount;
+          file.field = field % (nFiles / (wellCount * runCount));
           file.file = files.get(field);
           file.acquisition = runDirs.size() == 0 ? 0:
             runDirs.indexOf(new Location(file.file).getParentFile());
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
