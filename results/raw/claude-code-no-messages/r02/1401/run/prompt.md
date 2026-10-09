This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 8f5cb78051a109986916d97481c994275622de7b
- Commit message: 
- Diff:
```
commit 8f5cb78051a109986916d97481c994275622de7b
Author: Dmitry Batrak <Dmitry.Batrak@jetbrains.com>
Date:   Fri Jun 5 20:50:54 2015 +0300
---
 .../src/com/intellij/codeInsight/daemon/impl/LocalInspectionsPass.java  | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/platform/lang-impl/src/com/intellij/codeInsight/daemon/impl/LocalInspectionsPass.java b/platform/lang-impl/src/com/intellij/codeInsight/daemon/impl/LocalInspectionsPass.java
index 68e6f231a37..2d7520bb42e 100644
--- a/platform/lang-impl/src/com/intellij/codeInsight/daemon/impl/LocalInspectionsPass.java
+++ b/platform/lang-impl/src/com/intellij/codeInsight/daemon/impl/LocalInspectionsPass.java
@@ -570,7 +570,7 @@ public class LocalInspectionsPass extends ProgressableTextEditorHighlightingPass
 
     @NonNls String tooltip = null;
     if (descriptor.showTooltip()) {
-      tooltip = XmlStringUtil.wrapInHtml(message.startsWith("<html>") ? XmlStringUtil.stripHtml(message): XmlStringUtil.escapeString(message)) + link ;
+      tooltip = XmlStringUtil.wrapInHtml((message.startsWith("<html>") ? XmlStringUtil.stripHtml(message): XmlStringUtil.escapeString(message)) + link);
     }
     HighlightInfo highlightInfo = highlightInfoFromDescriptor(descriptor, type, plainMessage, tooltip,element);
     if (highlightInfo != null) {
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
