This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: a4ec18f80a2bb1c1bf34f068055df09cc91f34be
- Commit message: 
- Diff:
```
commit a4ec18f80a2bb1c1bf34f068055df09cc91f34be
Author: Duarte Nunes <duarte@scylladb.com>
Date:   Wed May 4 14:28:02 2016 +0200
---
 src/java/com/scylladb/tools/BulkLoader.java | 7 ++++---
 1 file changed, 4 insertions(+), 3 deletions(-)

diff --git a/src/java/com/scylladb/tools/BulkLoader.java b/src/java/com/scylladb/tools/BulkLoader.java
index 20f43652d..46f879a4d 100644
--- a/src/java/com/scylladb/tools/BulkLoader.java
+++ b/src/java/com/scylladb/tools/BulkLoader.java
@@ -222,6 +222,9 @@ public class BulkLoader {
         // fixed-point algorithm until we either load all UDTs or fail to make
         // forward progress.
         private static void loadUserTypes(Collection<UserType> udts, KSMetaData ks) {
+            if (udts.isEmpty()) {
+                return;
+            }
             LinkedList<UserType> notLoaded = new LinkedList<UserType>();
             for (UserType ut : udts) {
                 try {
@@ -241,9 +244,7 @@ public class BulkLoader {
             if (notLoaded.size() == udts.size()) {
                 throw new RuntimeException("Unable to load user types " + notLoaded);
             }
-            if (notLoaded.size() > 0) {
-                loadUserTypes(notLoaded, ks);
-            }
+            loadUserTypes(notLoaded, ks);
         }
 
         private static CQL3Type.Raw getCql3Type(DataType dt) throws Exception {
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
