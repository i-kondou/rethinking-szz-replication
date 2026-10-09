This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: b1fbad54f2acadd010d3960fb1bb475c59ca2a38
- Commit message: fix weird reclaim bug
- Diff:
```
commit b1fbad54f2acadd010d3960fb1bb475c59ca2a38
Author: Vyacheslav Lukianov <lvo@intellij.net>
Date:   Tue Sep 27 21:00:05 2016 +0300

    fix weird reclaim bug
---
 .../main/java/jetbrains/exodus/tree/patricia/PatriciaTreeMutable.java | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)

diff --git a/environment/src/main/java/jetbrains/exodus/tree/patricia/PatriciaTreeMutable.java b/environment/src/main/java/jetbrains/exodus/tree/patricia/PatriciaTreeMutable.java
index 9b0f045..1223383 100644
--- a/environment/src/main/java/jetbrains/exodus/tree/patricia/PatriciaTreeMutable.java
+++ b/environment/src/main/java/jetbrains/exodus/tree/patricia/PatriciaTreeMutable.java
@@ -467,7 +467,7 @@ final class PatriciaTreeMutable extends PatriciaTreeBase implements ITreeMutable
                         actItr = actual.currentNode.keySequence.iterator();
                     }
                 } else if (actItr.hasNext()) {
-                    final NodeChildrenIterator children = sourceNode.getChildren(actItr.next());
+                    final NodeChildrenIterator children = source.currentNode.getChildren(actItr.next());
                     final ChildReference child = children.getNode();
                     if (child == null || !source.isAddressReclaimable(child.suffixAddress)) {
                         break; // child can be expired if source parent was already not-current
@@ -476,7 +476,7 @@ final class PatriciaTreeMutable extends PatriciaTreeBase implements ITreeMutable
                     source.currentIterator = children;
                     source.moveDown();
                     ++srcPushes;
-                    srcItr = sourceNode.keySequence.iterator();
+                    srcItr = source.currentNode.keySequence.iterator();
                 } else { // both iterators matched, here comes the branching
                     reclaimChildren(source, actual);
                     break;
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
