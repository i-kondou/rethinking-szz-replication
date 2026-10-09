This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 7546a2336ef8e493f7074f1e6ff887a8174eb1ed
- Commit message: Fix Hadoop config namespace refs

This commit fixes a bug that broke some scanjob helper classes.
- Diff:
```
commit 7546a2336ef8e493f7074f1e6ff887a8174eb1ed
Author: Dan LaRocque <dalaro@hopcount.org>
Date:   Tue May 5 01:33:21 2015 -0400

    Fix Hadoop config namespace refs
    
    This commit fixes a bug that broke some scanjob helper classes.
---
 .../java/com/thinkaurelius/titan/hadoop/MapReduceIndexJobs.java   | 3 ++-
 .../com/thinkaurelius/titan/hadoop/MapReduceIndexManagement.java  | 8 ++++----
 .../titan/hadoop/scan/CassandraHadoopScanRunner.java              | 5 +++--
 .../thinkaurelius/titan/hadoop/scan/HBaseHadoopScanRunner.java    | 6 +++---
 .../java/com/thinkaurelius/titan/hadoop/CassandraScanJobIT.java   | 8 ++++----
 5 files changed, 16 insertions(+), 14 deletions(-)

diff --git a/titan-hadoop-parent/titan-hadoop-core/src/main/java/com/thinkaurelius/titan/hadoop/MapReduceIndexJobs.java b/titan-hadoop-parent/titan-hadoop-core/src/main/java/com/thinkaurelius/titan/hadoop/MapReduceIndexJobs.java
index faf99dc33..eb0903717 100644
--- a/titan-hadoop-parent/titan-hadoop-core/src/main/java/com/thinkaurelius/titan/hadoop/MapReduceIndexJobs.java
+++ b/titan-hadoop-parent/titan-hadoop-core/src/main/java/com/thinkaurelius/titan/hadoop/MapReduceIndexJobs.java
@@ -144,10 +144,11 @@ public class MapReduceIndexJobs {
     }
 
     private static void copyPropertiesToInputAndOutputConf(org.apache.hadoop.conf.Configuration sink, Properties source) {
+        final String prefix = ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS, true) + ".";
         for (Map.Entry<Object, Object> e : source.entrySet()) {
             String k;
             String v = e.getValue().toString();
-            k = ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS) + "." + e.getKey().toString();
+            k = prefix + e.getKey().toString();
             sink.set(k, v);
             log.info("Set {}={}", k, v);
         }
diff --git a/titan-hadoop-parent/titan-hadoop-core/src/main/java/com/thinkaurelius/titan/hadoop/MapReduceIndexManagement.java b/titan-hadoop-parent/titan-hadoop-core/src/main/java/com/thinkaurelius/titan/hadoop/MapReduceIndexManagement.java
index c8b7ac0ad..fd47a1b49 100644
--- a/titan-hadoop-parent/titan-hadoop-core/src/main/java/com/thinkaurelius/titan/hadoop/MapReduceIndexManagement.java
+++ b/titan-hadoop-parent/titan-hadoop-core/src/main/java/com/thinkaurelius/titan/hadoop/MapReduceIndexManagement.java
@@ -191,7 +191,7 @@ public class MapReduceIndexManagement {
             if (!pid.element.isOption())
                 continue;
 
-            String k = ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS) + "." + key;
+            String k = ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS, true) + "." + key;
             String v = source.getProperty(key).toString();
 
             hadoopConf.set(k, v);
@@ -200,13 +200,13 @@ public class MapReduceIndexManagement {
     }
 
     private static void copyIndexJobKeys(org.apache.hadoop.conf.Configuration hadoopConf, String indexName, String relationType) {
-        hadoopConf.set(ConfigElement.getPath(TitanHadoopConfiguration.SCAN_JOB_CONFIG_KEYS) + "." +
+        hadoopConf.set(ConfigElement.getPath(TitanHadoopConfiguration.SCAN_JOB_CONFIG_KEYS, true) + "." +
                         ConfigElement.getPath(IndexUpdateJob.INDEX_NAME), indexName);
 
-        hadoopConf.set(ConfigElement.getPath(TitanHadoopConfiguration.SCAN_JOB_CONFIG_KEYS) + "." +
+        hadoopConf.set(ConfigElement.getPath(TitanHadoopConfiguration.SCAN_JOB_CONFIG_KEYS, true) + "." +
                 ConfigElement.getPath(IndexUpdateJob.INDEX_RELATION_TYPE), relationType);
 
-        hadoopConf.set(ConfigElement.getPath(TitanHadoopConfiguration.SCAN_JOB_CONFIG_KEYS) + "." +
+        hadoopConf.set(ConfigElement.getPath(TitanHadoopConfiguration.SCAN_JOB_CONFIG_KEYS, true) + "." +
                 ConfigElement.getPath(GraphDatabaseConfiguration.JOB_START_TIME),
                 String.valueOf(System.currentTimeMillis()));
     }
diff --git a/titan-hadoop-parent/titan-hadoop-core/src/main/java/com/thinkaurelius/titan/hadoop/scan/CassandraHadoopScanRunner.java b/titan-hadoop-parent/titan-hadoop-core/src/main/java/com/thinkaurelius/titan/hadoop/scan/CassandraHadoopScanRunner.java
index cd20f870d..412663811 100644
--- a/titan-hadoop-parent/titan-hadoop-core/src/main/java/com/thinkaurelius/titan/hadoop/scan/CassandraHadoopScanRunner.java
+++ b/titan-hadoop-parent/titan-hadoop-core/src/main/java/com/thinkaurelius/titan/hadoop/scan/CassandraHadoopScanRunner.java
@@ -45,8 +45,9 @@ public class CassandraHadoopScanRunner extends AbstractHadoopScanRunner<Cassandr
 
         if (null != titanConf) {
             for (String k : titanConf.getKeys("")) {
-                hadoopConf.set(ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS) + "." + k, titanConf.<Object>get(k, Object.class).toString());
-                log.debug("Set: {}={}", ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS) + "." + k,
+                String prefix = ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS, true) + ".";
+                hadoopConf.set(prefix + k, titanConf.get(k, Object.class).toString());
+                log.debug("Set: {}={}", prefix + k,
                         titanConf.<Object>get(k, Object.class).toString());
             }
         }
diff --git a/titan-hadoop-parent/titan-hadoop-core/src/main/java/com/thinkaurelius/titan/hadoop/scan/HBaseHadoopScanRunner.java b/titan-hadoop-parent/titan-hadoop-core/src/main/java/com/thinkaurelius/titan/hadoop/scan/HBaseHadoopScanRunner.java
index 48503d19e..a9a6ebf26 100644
--- a/titan-hadoop-parent/titan-hadoop-core/src/main/java/com/thinkaurelius/titan/hadoop/scan/HBaseHadoopScanRunner.java
+++ b/titan-hadoop-parent/titan-hadoop-core/src/main/java/com/thinkaurelius/titan/hadoop/scan/HBaseHadoopScanRunner.java
@@ -36,10 +36,10 @@ public class HBaseHadoopScanRunner extends AbstractHadoopScanRunner<HBaseHadoopS
                 baseHadoopConf : new org.apache.hadoop.conf.Configuration();
 
         if (null != titanConf) {
+            String prefix = ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS, true) + ".";
             for (String k : titanConf.getKeys("")) {
-                hadoopConf.set(ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS) + "." + k, titanConf.<Object>get(k, Object.class).toString());
-                log.debug("Set: {}={}", ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS) + "." + k,
-                        titanConf.<Object>get(k, Object.class).toString());
+                hadoopConf.set(prefix + k, titanConf.get(k, Object.class).toString());
+                log.debug("Set: {}={}", prefix + k, titanConf.get(k, Object.class).toString());
             }
         }
         Preconditions.checkNotNull(hadoopConf);
diff --git a/titan-hadoop-parent/titan-hadoop-core/src/test/java/com/thinkaurelius/titan/hadoop/CassandraScanJobIT.java b/titan-hadoop-parent/titan-hadoop-core/src/test/java/com/thinkaurelius/titan/hadoop/CassandraScanJobIT.java
index 5f239a22b..09324378f 100644
--- a/titan-hadoop-parent/titan-hadoop-core/src/test/java/com/thinkaurelius/titan/hadoop/CassandraScanJobIT.java
+++ b/titan-hadoop-parent/titan-hadoop-core/src/test/java/com/thinkaurelius/titan/hadoop/CassandraScanJobIT.java
@@ -85,8 +85,8 @@ public class CassandraScanJobIT extends TitanGraphBaseTest {
         graph.tx().commit();
 
         org.apache.hadoop.conf.Configuration c = new org.apache.hadoop.conf.Configuration();
-        c.set(ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS) + "." + "storage.cassandra.keyspace", getClass().getSimpleName());
-        c.set(ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS) + "." + "storage.backend", "cassandrathrift");
+        c.set(ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS, true) + "." + "storage.cassandra.keyspace", getClass().getSimpleName());
+        c.set(ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS, true) + "." + "storage.backend", "cassandrathrift");
         c.set("cassandra.input.partitioner.class", "org.apache.cassandra.dht.ByteOrderedPartitioner");
 
         Job job = getVertexJobWithDefaultMapper(c);
@@ -113,8 +113,8 @@ public class CassandraScanJobIT extends TitanGraphBaseTest {
         graph.tx().commit();
 
         org.apache.hadoop.conf.Configuration c = new org.apache.hadoop.conf.Configuration();
-        c.set(ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS) + "." + "storage.cassandra.keyspace", getClass().getSimpleName());
-        c.set(ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS) + "." + "storage.backend", "cassandrathrift");
+        c.set(ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS, true) + "." + "storage.cassandra.keyspace", getClass().getSimpleName());
+        c.set(ConfigElement.getPath(TitanHadoopConfiguration.GRAPH_CONFIG_KEYS, true) + "." + "storage.backend", "cassandrathrift");
         c.set(ConfigElement.getPath(TitanHadoopConfiguration.FILTER_PARTITIONED_VERTICES), "true");
         c.set("cassandra.input.partitioner.class", "org.apache.cassandra.dht.ByteOrderedPartitioner");
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
