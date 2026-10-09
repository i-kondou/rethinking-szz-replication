This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 6cb1c62cb4b58db126b8fc76c1725f2503f38f58
- Commit message: Fix NPE when stories are run using JUnit runner

jbehave-junit-runner builds JUnit execution tree before the actual
execution. Also it knows nothing about Vividus batches. As result
when BDD stories are run NPE is thrown, because no batch is running.
- Diff:
```
commit 6cb1c62cb4b58db126b8fc76c1725f2503f38f58
Author: Valery Yatsynovich <valery_yatsynovich@epam.com>
Date:   Wed Feb 5 12:10:54 2020 +0300

    Fix NPE when stories are run using JUnit runner
    
    jbehave-junit-runner builds JUnit execution tree before the actual
    execution. Also it knows nothing about Vividus batches. As result
    when BDD stories are run NPE is thrown, because no batch is running.
---
 .../src/main/java/org/vividus/bdd/context/BddRunContext.java        | 3 ++-
 .../src/test/java/org/vividus/bdd/context/BddRunContextTests.java   | 6 ++++++
 2 files changed, 8 insertions(+), 1 deletion(-)

diff --git a/vividus-bdd-engine/src/main/java/org/vividus/bdd/context/BddRunContext.java b/vividus-bdd-engine/src/main/java/org/vividus/bdd/context/BddRunContext.java
index 86c5d4e..232d0fa 100644
--- a/vividus-bdd-engine/src/main/java/org/vividus/bdd/context/BddRunContext.java
+++ b/vividus-bdd-engine/src/main/java/org/vividus/bdd/context/BddRunContext.java
@@ -29,7 +29,8 @@ public class BddRunContext implements IBddRunContext
 {
     private TestContext testContext;
 
-    private Optional<String> runningBatchKey;
+    // must be initialized for jbehave-junit-runner
+    private Optional<String> runningBatchKey = Optional.of("batch-1");
     private boolean dryRun;
 
     public void putRunningStory(RunningStory story, boolean givenStory)
diff --git a/vividus-bdd-engine/src/test/java/org/vividus/bdd/context/BddRunContextTests.java b/vividus-bdd-engine/src/test/java/org/vividus/bdd/context/BddRunContextTests.java
index adf0f6a..6cb570d 100644
--- a/vividus-bdd-engine/src/test/java/org/vividus/bdd/context/BddRunContextTests.java
+++ b/vividus-bdd-engine/src/test/java/org/vividus/bdd/context/BddRunContextTests.java
@@ -83,6 +83,12 @@ class BddRunContextTests
         assertNull(bddRunContext.getRunningStory());
     }
 
+    @Test
+    void testGetDefaultRunningBatchKey()
+    {
+        assertEquals("batch-1", bddRunContext.getRunningBatchKey());
+    }
+
     @Test
     void testGetRunningBatchKey()
     {
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
