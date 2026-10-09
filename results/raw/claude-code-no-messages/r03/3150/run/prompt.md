This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 7a91a35a001ad1b41d3250c8d06ea3647312d25d
- Commit message: 
- Diff:
```
commit 7a91a35a001ad1b41d3250c8d06ea3647312d25d
Author: Stephen Gold <sgold@sonic.net>
Date:   Sun Jul 9 00:10:58 2017 -0700
---
 src/main/java/maud/Util.java | 25 ++++++++++++++-----------
 1 file changed, 14 insertions(+), 11 deletions(-)

diff --git a/src/main/java/maud/Util.java b/src/main/java/maud/Util.java
index 888ea39..9f14151 100644
--- a/src/main/java/maud/Util.java
+++ b/src/main/java/maud/Util.java
@@ -506,12 +506,9 @@ public class Util {
                 int iSource = sourceSkeleton.getBoneIndex(sourceName);
                 BoneTrack sourceTrack;
                 sourceTrack = MyAnimation.findTrack(sourceAnimation, iSource);
-                if (sourceTrack != null) { // handle null sourceTrack
-                    BoneTrack track;
-                    track = retargetTrack(sourceAnimation, sourceTrack,
-                            sourceSkeleton, targetSkeleton, mapping, iTarget);
-                    result.addTrack(track);
-                }
+                BoneTrack track = retargetTrack(sourceAnimation, sourceTrack,
+                        sourceSkeleton, targetSkeleton, mapping, iTarget);
+                result.addTrack(track);
             }
         }
 
@@ -522,8 +519,7 @@ public class Util {
      * Re-target the specified bone track from the specified source skeleton to
      * the specified target skeleton using the specified mapping.
      *
-     * @param sourceAnimation which animation to re-target (not null,
-     * unaffected)
+     * @param sourceAnimation the animation to re-target, or null for bind pose
      * @param sourceSkeleton (not null, unaffected)
      * @param sourceTrack input bone track (not null, unaffected)
      * @param targetSkeleton (not null, unaffected)
@@ -536,13 +532,20 @@ public class Util {
             Skeleton targetSkeleton, SkeletonMapping mapping,
             int targetBoneIndex) {
         Validate.nonNull(sourceSkeleton, "source skeleton");
-        Validate.nonNull(sourceTrack, "source track");
         Validate.nonNull(targetSkeleton, "target skeleton");
         Validate.nonNull(mapping, "mapping");
         Validate.nonNegative(targetBoneIndex, "target bone index");
 
-        float[] times = sourceTrack.getTimes();
-        int numKeyframes = times.length;
+        float[] times;
+        int numKeyframes;
+        if (sourceTrack == null) {
+            numKeyframes = 1;
+            times = new float[numKeyframes];
+            times[0] = 0f;
+        } else {
+            times = sourceTrack.getTimes();
+            numKeyframes = times.length;
+        }
         Vector3f[] translations = new Vector3f[numKeyframes];
         Quaternion[] rotations = new Quaternion[numKeyframes];
         Vector3f[] scales = new Vector3f[numKeyframes];
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
