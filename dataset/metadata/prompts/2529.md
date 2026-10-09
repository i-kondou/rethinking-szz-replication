This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: fea56932fffe94e2d7dde77d8d27c159acac1795
- Commit message: StatusUpdaterBolt : fixes bug and simplifies code
- Diff:
```
commit fea56932fffe94e2d7dde77d8d27c159acac1795
Author: Julien Nioche <julien@digitalpebble.com>
Date:   Thu Dec 22 11:41:49 2016 +0000

    StatusUpdaterBolt : fixes bug and simplifies code
---
 .../elasticsearch/persistence/StatusUpdaterBolt.java      | 15 +++++++++++----
 1 file changed, 11 insertions(+), 4 deletions(-)

diff --git a/external/elasticsearch/src/main/java/com/digitalpebble/stormcrawler/elasticsearch/persistence/StatusUpdaterBolt.java b/external/elasticsearch/src/main/java/com/digitalpebble/stormcrawler/elasticsearch/persistence/StatusUpdaterBolt.java
index ed3cf70..2938f64 100644
--- a/external/elasticsearch/src/main/java/com/digitalpebble/stormcrawler/elasticsearch/persistence/StatusUpdaterBolt.java
+++ b/external/elasticsearch/src/main/java/com/digitalpebble/stormcrawler/elasticsearch/persistence/StatusUpdaterBolt.java
@@ -66,6 +66,8 @@ public class StatusUpdaterBolt extends AbstractStatusUpdaterBolt {
     private static final String ESStatusRoutingParamName = "es.status.routing";
     private static final String ESStatusRoutingFieldParamName = "es.status.routing.fieldname";
 
+    private boolean routingFieldNameInMetadata = false;
+
     private String indexName;
     private String docType;
 
@@ -105,8 +107,13 @@ public class StatusUpdaterBolt extends AbstractStatusUpdaterBolt {
             partitioner.configure(stormConf);
             fieldNameForRoutingKey = ConfUtils.getString(stormConf,
                     StatusUpdaterBolt.ESStatusRoutingFieldParamName);
-            // periods are not allowed in ES2 - replace with %2E
             if (StringUtils.isNotBlank(fieldNameForRoutingKey)) {
+                if (fieldNameForRoutingKey.startsWith("metadata.")) {
+                    routingFieldNameInMetadata = true;
+                    fieldNameForRoutingKey = fieldNameForRoutingKey
+                            .substring("metadata.".length());
+                }
+                // periods are not allowed in ES2 - replace with %2E
                 fieldNameForRoutingKey = fieldNameForRoutingKey.replaceAll(
                         "\\.", "%2E");
             }
@@ -247,8 +254,8 @@ public class StatusUpdaterBolt extends AbstractStatusUpdaterBolt {
         // store routing key in metadata?
         if (StringUtils.isNotBlank(partitionKey)
                 && StringUtils.isNotBlank(fieldNameForRoutingKey)
-                && fieldNameForRoutingKey.startsWith("metadata.")) {
-            builder.field(fieldNameForRoutingKey.substring(9), partitionKey);
+                && routingFieldNameInMetadata) {
+            builder.field(fieldNameForRoutingKey, partitionKey);
         }
 
         builder.endObject();
@@ -256,7 +263,7 @@ public class StatusUpdaterBolt extends AbstractStatusUpdaterBolt {
         // store routing key outside metadata?
         if (StringUtils.isNotBlank(partitionKey)
                 && StringUtils.isNotBlank(fieldNameForRoutingKey)
-                && !fieldNameForRoutingKey.startsWith("metadata.")) {
+                && !routingFieldNameInMetadata) {
             builder.field(fieldNameForRoutingKey, partitionKey);
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
