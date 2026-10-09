This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: dd79357d0560a2d9ce81a2fa536ad530b76d7dd4
- Commit message: 
- Diff:
```
commit dd79357d0560a2d9ce81a2fa536ad530b76d7dd4
Author: Pascal Proulx <pplx@ilscipio.com>
Date:   Mon Jun 4 15:34:32 2018 -0400
---
 .../cms/src/com/ilscipio/scipio/cms/template/CmsRenderTemplate.java     | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/applications/cms/src/com/ilscipio/scipio/cms/template/CmsRenderTemplate.java b/applications/cms/src/com/ilscipio/scipio/cms/template/CmsRenderTemplate.java
index 545d03daf..26d09742f 100644
--- a/applications/cms/src/com/ilscipio/scipio/cms/template/CmsRenderTemplate.java
+++ b/applications/cms/src/com/ilscipio/scipio/cms/template/CmsRenderTemplate.java
@@ -187,7 +187,7 @@ public interface CmsRenderTemplate extends Serializable {
             ClassLoader loader = Thread.currentThread().getContextClassLoader();
             Enumeration<URL> resources;
             try {
-                resources = loader.getResources("cmsFreemarkerTransforms");
+                resources = loader.getResources("cmsFreemarkerTransforms.properties");
             } catch (IOException e) {
                 Debug.logError(e, "Could not load list of cmsFreemarkerTransforms", module);
                 throw UtilMisc.initCause(new InternalError(e.getMessage()), e);
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
