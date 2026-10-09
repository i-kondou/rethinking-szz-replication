This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 0705528149860c5e4aca92591f05b1e6dabc067f
- Commit message: Call AbstractElement getID() insteado of getId()

Relying on capitalization significance to differentiate methods on
this object seems like asking for trouble.  For now, just fix the
capitalization bug, but we might want to
refactor getID() and getId() to more distinct names.
- Diff:
```
commit 0705528149860c5e4aca92591f05b1e6dabc067f
Author: Dan LaRocque <dalaro@hopcount.org>
Date:   Wed May 29 18:50:45 2013 -0400

    Call AbstractElement getID() insteado of getId()
    
    Relying on capitalization significance to differentiate methods on
    this object seems like asking for trouble.  For now, just fix the
    capitalization bug, but we might want to
    refactor getID() and getId() to more distinct names.
---
 .../com/thinkaurelius/titan/graphdb/internal/AbstractElement.java     | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)

diff --git a/titan-core/src/main/java/com/thinkaurelius/titan/graphdb/internal/AbstractElement.java b/titan-core/src/main/java/com/thinkaurelius/titan/graphdb/internal/AbstractElement.java
index 339f4a0..ca0bb90 100644
--- a/titan-core/src/main/java/com/thinkaurelius/titan/graphdb/internal/AbstractElement.java
+++ b/titan-core/src/main/java/com/thinkaurelius/titan/graphdb/internal/AbstractElement.java
@@ -38,9 +38,9 @@ public abstract class AbstractElement implements InternalElement {
         } else if (other==null) {
             return false;
         } else if (this instanceof TitanVertex && other instanceof TitanVertex) {
-            return getId().equals(((TitanVertex)other).getId());
+            return getID() == ((TitanVertex)other).getID();
         } else if (this instanceof TitanEdge && other instanceof TitanEdge) {
-            return getId().equals(((TitanEdge)other).getId());
+            return getID() == ((TitanEdge)other).getID();
         } else {
             return false;
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
