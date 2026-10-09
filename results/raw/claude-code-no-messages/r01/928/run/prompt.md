This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: f6600d247898d32f8e907da56cd2fb4a72f055a5
- Commit message: 
- Diff:
```
commit f6600d247898d32f8e907da56cd2fb4a72f055a5
Author: yushijinhun <yushijinhun@gmail.com>
Date:   Sat Jul 7 17:26:20 2018 +0800
---
 .../java/org/jackhuang/hmcl/ui/animation/TransitionHandler.java     | 6 ++----
 1 file changed, 2 insertions(+), 4 deletions(-)

diff --git a/HMCL/src/main/java/org/jackhuang/hmcl/ui/animation/TransitionHandler.java b/HMCL/src/main/java/org/jackhuang/hmcl/ui/animation/TransitionHandler.java
index cec4a9d4..b350bb9a 100644
--- a/HMCL/src/main/java/org/jackhuang/hmcl/ui/animation/TransitionHandler.java
+++ b/HMCL/src/main/java/org/jackhuang/hmcl/ui/animation/TransitionHandler.java
@@ -86,7 +86,7 @@ public final class TransitionHandler implements AnimationHandler {
             Timeline nowAnimation = new Timeline();
             nowAnimation.getKeyFrames().addAll(transition.animate(this));
             nowAnimation.getKeyFrames().add(new KeyFrame(duration, e -> {
-                previousNode.setMouseTransparent((Boolean) previousNode.getProperties().get(MOUSE_TRANSPARENT));
+                view.setMouseTransparent(false);
                 view.getChildren().remove(previousNode);
             }));
             nowAnimation.play();
@@ -105,14 +105,12 @@ public final class TransitionHandler implements AnimationHandler {
         if (previousNode == newView)
             previousNode = NULL;
 
-        previousNode.getProperties().put(MOUSE_TRANSPARENT, previousNode.isMouseTransparent());
-        previousNode.setMouseTransparent(true);
+        view.setMouseTransparent(true);
 
         currentNode = newView;
 
         view.getChildren().setAll(previousNode, currentNode);
     }
 
-    private static final String MOUSE_TRANSPARENT = "TransitionHandler.MOUSE_TRANSPARENT";
     private static final StackPane NULL = new StackPane();
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
