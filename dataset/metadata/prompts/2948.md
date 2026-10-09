This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 0b59466d102d0a56a80e8059846bc4fdd8ffdb9c
- Commit message: ND2: fix string indexing bug
- Diff:
```
commit 0b59466d102d0a56a80e8059846bc4fdd8ffdb9c
Author: Melissa Linkert <melissa@glencoesoftware.com>
Date:   Thu Nov 16 14:36:27 2017 -0600

    ND2: fix string indexing bug
---
 components/formats-gpl/src/loci/formats/in/NativeND2Reader.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/components/formats-gpl/src/loci/formats/in/NativeND2Reader.java b/components/formats-gpl/src/loci/formats/in/NativeND2Reader.java
index 417137f02..a733301fa 100644
--- a/components/formats-gpl/src/loci/formats/in/NativeND2Reader.java
+++ b/components/formats-gpl/src/loci/formats/in/NativeND2Reader.java
@@ -2413,7 +2413,7 @@ public class NativeND2Reader extends FormatReader {
       lines = textString.split(" ");
       for (int i=0; i<lines.length; i++) {
         StringBuffer sb = new StringBuffer(lines[i++]);
-        while (sb.charAt(sb.length() - 1) != ':' && sb.indexOf("_") < 0 && i < lines.length) {
+        while ((sb.length() == 0 || sb.charAt(sb.length() - 1) != ':') && sb.indexOf("_") < 0 && i < lines.length) {
           sb.append(" ");
           sb.append(lines[i++]);
           if (i >= lines.length) {
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
