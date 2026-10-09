This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 11e5ca1461f94b5dde84a299577bbc878c81b328
- Commit message: 
- Diff:
```
commit 11e5ca1461f94b5dde84a299577bbc878c81b328
Author: neevek <i@neevek.net>
Date:   Mon Mar 23 17:07:57 2015 +0800
---
 PaginizeLib/src/net/neevek/android/lib/paginize/PageManager.java | 5 +++--
 1 file changed, 3 insertions(+), 2 deletions(-)

diff --git a/PaginizeLib/src/net/neevek/android/lib/paginize/PageManager.java b/PaginizeLib/src/net/neevek/android/lib/paginize/PageManager.java
index c046b7a..51ee781 100644
--- a/PaginizeLib/src/net/neevek/android/lib/paginize/PageManager.java
+++ b/PaginizeLib/src/net/neevek/android/lib/paginize/PageManager.java
@@ -326,6 +326,9 @@ public class PageManager {
       }
     }
 
+    mContainerView.removeView(removedPage.getView());
+    mCurPage = prevPage;
+
     int animationDuration = removedPage.getAnimationDuration();
     if (animationDuration == -1 && mPageAnimator != null) {
       animationDuration = mPageAnimator.getAnimationDuration();
@@ -344,10 +347,8 @@ public class PageManager {
   }
 
   private void doFinalWorkForPopPageInternal(Page removedPage, Page prevPage) {
-    mContainerView.removeView(removedPage.getView());
     removedPage.onDetach();
     removedPage.onHidden();
-    mCurPage = prevPage;
 
     if (prevPage != null) {
       prevPage.onUncovered(removedPage.getReturnData());
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
