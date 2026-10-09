This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 09fa087bedbfa1102c0d91279264df4d451c922f
- Commit message: 
- Diff:
```
commit 09fa087bedbfa1102c0d91279264df4d451c922f
Author: Aleksey Pivovarov <aleksey.pivovarov@jetbrains.com>
Date:   Sat Feb 20 12:35:04 2016 +0300
---
 .../src/com/intellij/openapi/vcs/history/FileHistoryPanelImpl.java    | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)

diff --git a/platform/vcs-impl/src/com/intellij/openapi/vcs/history/FileHistoryPanelImpl.java b/platform/vcs-impl/src/com/intellij/openapi/vcs/history/FileHistoryPanelImpl.java
index ecb621f08d0..9955dc7cf30 100644
--- a/platform/vcs-impl/src/com/intellij/openapi/vcs/history/FileHistoryPanelImpl.java
+++ b/platform/vcs-impl/src/com/intellij/openapi/vcs/history/FileHistoryPanelImpl.java
@@ -398,13 +398,13 @@ public class FileHistoryPanelImpl extends PanelWithActionsAndCloseButton {
     listener.installOn(myDualView.getTreeView());
     setEmptyText(CommonBundle.getLoadingTreeNodeText());
 
+    myPopupActions = createPopupActions();
+
     createDualView();
     if (isStaticEmbedded) {
       setIsStaticAndEmbedded(isStaticEmbedded);
     }
 
-    myPopupActions = createPopupActions();
-
     myHistoryPanelRefresh = new AsynchConsumer<VcsHistorySession>() {
       public void finished() {
         if (treeHistoryProvider != null) {
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
