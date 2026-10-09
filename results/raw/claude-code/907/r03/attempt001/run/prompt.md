This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 120201466dc5554166a2b5a894f50eb508a2d904
- Commit message: Hopefully a (perhaps temporary) fix for the synthetic stack bug.

Temporary in the sense that I think a better long term solution is needed.

RELNOTES=n/a

-------------
Created by MOE: https://github.com/google/moe
MOE_MIGRATED_REVID=321223718
- Diff:
```
commit 120201466dc5554166a2b5a894f50eb508a2d904
Author: dbeaumont <dbeaumont@google.com>
Date:   Tue Jul 14 13:28:40 2020 -0700

    Hopefully a (perhaps temporary) fix for the synthetic stack bug.
    
    Temporary in the sense that I think a better long term solution is needed.
    
    RELNOTES=n/a
    
    -------------
    Created by MOE: https://github.com/google/moe
    MOE_MIGRATED_REVID=321223718
---
 .../main/java/com/google/common/flogger/LogContext.java    | 14 +++++++++++++-
 .../java/com/google/common/flogger/util/CallerFinder.java  | 13 ++++++-------
 2 files changed, 19 insertions(+), 8 deletions(-)

diff --git a/api/src/main/java/com/google/common/flogger/LogContext.java b/api/src/main/java/com/google/common/flogger/LogContext.java
index 0381dbd..dc4ac54 100644
--- a/api/src/main/java/com/google/common/flogger/LogContext.java
+++ b/api/src/main/java/com/google/common/flogger/LogContext.java
@@ -495,11 +495,23 @@ public abstract class LogContext<
     if (stackSize != null) {
       // we add this information to the stack trace exception so it doesn't need to go here.
       removeMetadata(Key.CONTEXT_STACK_SIZE);
+      // IMPORTANT: Skipping at least 1 stack frame below is essential for correctness, since
+      // postProcess() can be overridden, so the stack could look like:
+      //
+      // ^  UserCode::someMethod       << we want to start here and skip everything below
+      // |  LogContext::log
+      // |  LogContext::shouldLog
+      // |  OtherChildContext::postProcess
+      // |  ChildContext::postProcess  << this is not the caller of LogContext we're after
+      // \- LogContext::postProcess    << we are here
+      //
+      // By skipping the initial code inside this method, we don't trigger any stack capture until
+      // after the "log" method.
       LogSiteStackTrace context =
           new LogSiteStackTrace(
               getMetadata().findValue(LogContext.Key.LOG_CAUSE),
               stackSize,
-              getStackForCallerOf(LogContext.class, new Throwable(), stackSize.getMaxDepth()));
+              getStackForCallerOf(LogContext.class, new Throwable(), stackSize.getMaxDepth(), 1));
       // The "cause" is a unique metadata key, we must replace any existing value.
       addMetadata(LogContext.Key.LOG_CAUSE, context);
     }
diff --git a/api/src/main/java/com/google/common/flogger/util/CallerFinder.java b/api/src/main/java/com/google/common/flogger/util/CallerFinder.java
index 2dd92f0..ae2c7b9 100644
--- a/api/src/main/java/com/google/common/flogger/util/CallerFinder.java
+++ b/api/src/main/java/com/google/common/flogger/util/CallerFinder.java
@@ -81,17 +81,21 @@ public final class CallerFinder {
    * @param target the class who caller the returned stack trace will start at.
    * @param throwable a new Throwable made at a known point in the call hierarchy.
    * @param maxDepth the maximum size of the returned stack (pass -1 for the complete stack).
+   * @param skip the minimum number of stack frames to skip before looking for callers.
    * @return a synthetic stack trace starting at the immediate caller of the specified target, or
    *     the empty array if no caller was found (due to incorrect target, wrong skip count or use
    *     of JNI).
    */
   public static StackTraceElement[] getStackForCallerOf(
-      Class<?> target, Throwable throwable, int maxDepth) {
+      Class<?> target, Throwable throwable, int maxDepth, int skip) {
     checkNotNull(target, "target");
     checkNotNull(throwable, "throwable");
     if (maxDepth <= 0 && maxDepth != -1) {
       throw new IllegalArgumentException("invalid maximum depth: " + maxDepth);
     }
+    if (skip < 0) {
+      throw new IllegalArgumentException("skip count cannot be negative: " + skip);
+    }
     // Getting the full stack trace is expensive, so avoid it where possible.
     StackTraceElement[] stack;
     int depth;
@@ -103,12 +107,7 @@ public final class CallerFinder {
       depth = stack.length;
     }
     boolean foundCaller = false;
-    // Note that previous versions of this code skipped some variable number of stack frames to
-    // account for "known" stack frames at the point this method was called. This was a minor
-    // performance optimization but turned out to be problematic in the face of things like
-    // Proguard, which can fold method/classes and change the number of intermediate stack frames.
-    // Now we just start at the immediate "parent" frame.
-    for (int index = 0; index < depth; index++) {
+    for (int index = skip; index < depth; index++) {
       StackTraceElement element =
           (stackGetter != null) ? stackGetter.getStackTraceElement(throwable, index) : stack[index];
       if (target.getName().equals(element.getClassName())) {
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
