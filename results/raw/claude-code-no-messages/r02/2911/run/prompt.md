This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 2c001a55d242822ac7272f56cc5202e84ed889df
- Commit message: 
- Diff:
```
commit 2c001a55d242822ac7272f56cc5202e84ed889df
Author: Samuel Just <sjust@salesforce.com>
Date:   Fri Jan 5 01:13:17 2018 -0800
---
 .../bookkeeper/common/util/OrderedScheduler.java   |   8 +-
 .../bookkeeper/conf/ServerConfiguration.java       |  25 +++
 .../bookkeeper/proto/BookieRequestProcessor.java   |  38 +++-
 .../bookkeeper/test/BookKeeperClusterTestCase.java |  35 ++-
 .../org/apache/bookkeeper/test/OpStatTest.java     | 125 +++++++++++
 .../apache/bookkeeper/test/TestStatsProvider.java  | 245 +++++++++++++++++++++
 6 files changed, 455 insertions(+), 21 deletions(-)

diff --git a/bookkeeper-common/src/main/java/org/apache/bookkeeper/common/util/OrderedScheduler.java b/bookkeeper-common/src/main/java/org/apache/bookkeeper/common/util/OrderedScheduler.java
index a0ab624b..efc9df8b 100644
--- a/bookkeeper-common/src/main/java/org/apache/bookkeeper/common/util/OrderedScheduler.java
+++ b/bookkeeper-common/src/main/java/org/apache/bookkeeper/common/util/OrderedScheduler.java
@@ -154,7 +154,9 @@ public class OrderedScheduler {
 
         @Override
         public void safeRun() {
-            taskPendingStats.registerSuccessfulEvent(initNanos, TimeUnit.NANOSECONDS);
+            taskPendingStats.registerSuccessfulEvent(
+                    MathUtils.elapsedNanos(initNanos),
+                    TimeUnit.NANOSECONDS);
             long startNanos = MathUtils.nowInNano();
             this.runnable.safeRun();
             long elapsedMicroSec = MathUtils.elapsedMicroSec(startNanos);
@@ -325,7 +327,7 @@ public class OrderedScheduler {
      * @param r
      */
     public void submitOrdered(long orderingKey, SafeRunnable r) {
-        chooseThread(orderingKey).execute(r);
+        chooseThread(orderingKey).execute(timedRunnable(r));
     }
 
     /**
@@ -335,7 +337,7 @@ public class OrderedScheduler {
      * @param r
      */
     public void submitOrdered(int orderingKey, SafeRunnable r) {
-        chooseThread(orderingKey).execute(r);
+        chooseThread(orderingKey).execute(timedRunnable(r));
     }
 
     /**
diff --git a/bookkeeper-server/src/main/java/org/apache/bookkeeper/conf/ServerConfiguration.java b/bookkeeper-server/src/main/java/org/apache/bookkeeper/conf/ServerConfiguration.java
index a9757422..d6e4d5f3 100644
--- a/bookkeeper-server/src/main/java/org/apache/bookkeeper/conf/ServerConfiguration.java
+++ b/bookkeeper-server/src/main/java/org/apache/bookkeeper/conf/ServerConfiguration.java
@@ -182,6 +182,9 @@ public class ServerConfiguration extends AbstractConfiguration<ServerConfigurati
     // Registration
     protected static final String REGISTRATION_MANAGER_CLASS = "registrationManagerClass";
 
+    // Stats
+    protected static final String ENABLE_TASK_EXECUTION_STATS = "enableTaskExecutionStats";
+
     /**
      * Construct a default configuration object.
      */
@@ -2412,6 +2415,28 @@ public class ServerConfiguration extends AbstractConfiguration<ServerConfigurati
         return this;
     }
 
+
+    /**
+     * Whether to enable recording task execution stats.
+     *
+     * @return flag to enable/disable recording task execution stats.
+     */
+    public boolean getEnableTaskExecutionStats() {
+        return getBoolean(ENABLE_TASK_EXECUTION_STATS, false);
+    }
+
+    /**
+     * Enable/Disable recording task execution stats.
+     *
+     * @param enabled
+     *          flag to enable/disable recording task execution stats.
+     * @return client configuration.
+     */
+    public ServerConfiguration setEnableTaskExecutionStats(boolean enabled) {
+        setProperty(ENABLE_TASK_EXECUTION_STATS, enabled);
+        return this;
+    }
+
     /**
      * Gets the minimum safe Usable size to be available in index directory for Bookie to create Index File while
      * replaying journal at the time of Bookie Start in Readonly Mode (in bytes).
diff --git a/bookkeeper-server/src/main/java/org/apache/bookkeeper/proto/BookieRequestProcessor.java b/bookkeeper-server/src/main/java/org/apache/bookkeeper/proto/BookieRequestProcessor.java
index 9b5421f3..24a3925c 100644
--- a/bookkeeper-server/src/main/java/org/apache/bookkeeper/proto/BookieRequestProcessor.java
+++ b/bookkeeper-server/src/main/java/org/apache/bookkeeper/proto/BookieRequestProcessor.java
@@ -142,16 +142,21 @@ public class BookieRequestProcessor implements RequestProcessor {
             StatsLogger statsLogger, SecurityHandlerFactory shFactory) throws SecurityException {
         this.serverCfg = serverCfg;
         this.bookie = bookie;
-        this.readThreadPool = createExecutor(this.serverCfg.getNumReadWorkerThreads(),
-                "BookieReadThread-" + serverCfg.getBookiePort(),
-                serverCfg.getMaxPendingReadRequestPerThread());
-        this.writeThreadPool = createExecutor(this.serverCfg.getNumAddWorkerThreads(),
-                "BookieWriteThread-" + serverCfg.getBookiePort(),
-                serverCfg.getMaxPendingAddRequestPerThread());
-        this.longPollThreadPool =
-            createExecutor(
+        this.readThreadPool = createExecutor(
+                this.serverCfg.getNumReadWorkerThreads(),
+                "BookieReadThreadPool",
+                serverCfg.getMaxPendingReadRequestPerThread(),
+                statsLogger);
+        this.writeThreadPool = createExecutor(
+                this.serverCfg.getNumAddWorkerThreads(),
+                "BookieWriteThreadPool",
+                serverCfg.getMaxPendingAddRequestPerThread(),
+                statsLogger);
+        this.longPollThreadPool = createExecutor(
                 this.serverCfg.getNumLongPollWorkerThreads(),
-                "BookieLongPollThread-" + serverCfg.getBookiePort(), OrderedScheduler.NO_TASK_LIMIT);
+                "BookieLongPollThread",
+                OrderedScheduler.NO_TASK_LIMIT,
+                statsLogger);
         this.requestTimer = new HashedWheelTimer(
             new ThreadFactoryBuilder().setNameFormat("BookieRequestTimer-%d").build(),
             this.serverCfg.getRequestTimerTickDurationMs(),
@@ -192,12 +197,21 @@ public class BookieRequestProcessor implements RequestProcessor {
         shutdownExecutor(longPollThreadPool);
     }
 
-    private OrderedSafeExecutor createExecutor(int numThreads, String nameFormat, int maxTasksInQueue) {
+    private OrderedSafeExecutor createExecutor(
+            int numThreads,
+            String nameFormat,
+            int maxTasksInQueue,
+            StatsLogger statsLogger) {
         if (numThreads <= 0) {
             return null;
         } else {
-            return OrderedSafeExecutor.newBuilder().numThreads(numThreads).name(nameFormat)
-                .maxTasksInQueue(maxTasksInQueue).build();
+            return OrderedSafeExecutor.newBuilder()
+                    .numThreads(numThreads)
+                    .name(nameFormat)
+                    .traceTaskExecution(serverCfg.getEnableTaskExecutionStats())
+                    .statsLogger(statsLogger)
+                    .maxTasksInQueue(maxTasksInQueue)
+                    .build();
         }
     }
 
diff --git a/bookkeeper-server/src/test/java/org/apache/bookkeeper/test/BookKeeperClusterTestCase.java b/bookkeeper-server/src/test/java/org/apache/bookkeeper/test/BookKeeperClusterTestCase.java
index 6f2f58e6..300b6f00 100644
--- a/bookkeeper-server/src/test/java/org/apache/bookkeeper/test/BookKeeperClusterTestCase.java
+++ b/bookkeeper-server/src/test/java/org/apache/bookkeeper/test/BookKeeperClusterTestCase.java
@@ -81,6 +81,7 @@ public abstract class BookKeeperClusterTestCase {
     protected final List<File> tmpDirs = new LinkedList<File>();
     protected final List<BookieServer> bs = new LinkedList<BookieServer>();
     protected final List<ServerConfiguration> bsConfs = new LinkedList<ServerConfiguration>();
+    private final Map<BookieSocketAddress, TestStatsProvider> bsLoggers = new HashMap<>();
     protected int numBookies;
     protected BookKeeperTestClient bkc;
 
@@ -198,6 +199,7 @@ public abstract class BookKeeperClusterTestCase {
             }
         }
         bs.clear();
+        bsLoggers.clear();
     }
 
     protected void cleanupTempDirs() throws Exception {
@@ -235,6 +237,7 @@ public abstract class BookKeeperClusterTestCase {
             ledgerDirNames[i] = ledgerDirs[i].getPath();
         }
         conf.setLedgerDirNames(ledgerDirNames);
+        conf.setEnableTaskExecutionStats(true);
         return conf;
     }
 
@@ -307,6 +310,7 @@ public abstract class BookKeeperClusterTestCase {
         if (toRemove != null) {
             stopAutoRecoveryService(toRemove);
             bs.remove(toRemove);
+            bsLoggers.remove(addr);
             return bsConfs.remove(toRemoveIndex);
         }
         return null;
@@ -346,6 +350,7 @@ public abstract class BookKeeperClusterTestCase {
         server.shutdown();
         stopAutoRecoveryService(server);
         bs.remove(server);
+        bsLoggers.remove(server.getLocalAddress());
         return bsConfs.remove(index);
     }
 
@@ -480,16 +485,14 @@ public abstract class BookKeeperClusterTestCase {
         int toRemoveIndex = 0;
         for (BookieServer server : bs) {
             if (server.getLocalAddress().equals(addr)) {
-                server.shutdown();
                 toRemove = server;
                 break;
             }
             ++toRemoveIndex;
         }
         if (toRemove != null) {
-            stopAutoRecoveryService(toRemove);
-            bs.remove(toRemove);
-            ServerConfiguration newConfig = bsConfs.remove(toRemoveIndex);
+            ServerConfiguration newConfig = bsConfs.get(toRemoveIndex);
+            killBookie(toRemoveIndex);
             Thread.sleep(1000);
             bs.add(startBookie(newConfig));
             bsConfs.add(newConfig);
@@ -517,6 +520,7 @@ public abstract class BookKeeperClusterTestCase {
             stopAutoRecoveryService(server);
         }
         bs.clear();
+        bsLoggers.clear();
         Thread.sleep(1000);
         // restart them to ensure we can't
         for (ServerConfiguration conf : bsConfs) {
@@ -557,8 +561,11 @@ public abstract class BookKeeperClusterTestCase {
      */
     protected BookieServer startBookie(ServerConfiguration conf)
             throws Exception {
-        BookieServer server = new BookieServer(conf);
+        TestStatsProvider provider = new TestStatsProvider();
+        BookieServer server = new BookieServer(conf, provider.getStatsLogger(""));
         BookieSocketAddress address = Bookie.getBookieAddress(conf);
+        bsLoggers.put(address, provider);
+
         if (bkc == null) {
             bkc = new BookKeeperTestClient(baseClientConf);
         }
@@ -588,7 +595,8 @@ public abstract class BookKeeperClusterTestCase {
      */
     protected BookieServer startBookie(ServerConfiguration conf, final Bookie b)
             throws Exception {
-        BookieServer server = new BookieServer(conf) {
+        TestStatsProvider provider = new TestStatsProvider();
+        BookieServer server = new BookieServer(conf, provider.getStatsLogger("")) {
             @Override
             protected Bookie newBookie(ServerConfiguration conf) {
                 return b;
@@ -604,6 +612,7 @@ public abstract class BookKeeperClusterTestCase {
             : bkc.waitForWritableBookie(address);
 
         server.start();
+        bsLoggers.put(server.getLocalAddress(), provider);
 
         waitForBookie.get(30, TimeUnit.SECONDS);
         LOG.info("New bookie '{}' has been created.", address);
@@ -723,4 +732,18 @@ public abstract class BookKeeperClusterTestCase {
     public static boolean isCreatedFromIp(BookieSocketAddress addr) {
         return addr.getSocketAddress().toString().startsWith("/");
     }
+
+    public void resetBookieOpLoggers() {
+        for (TestStatsProvider provider : bsLoggers.values()) {
+            provider.clear();
+        }
+    }
+
+    public TestStatsProvider getStatsProvider(BookieSocketAddress addr) {
+        return bsLoggers.get(addr);
+    }
+
+    public TestStatsProvider getStatsProvider(int index) throws Exception {
+        return getStatsProvider(bs.get(index).getLocalAddress());
+    }
 }
diff --git a/bookkeeper-server/src/test/java/org/apache/bookkeeper/test/OpStatTest.java b/bookkeeper-server/src/test/java/org/apache/bookkeeper/test/OpStatTest.java
new file mode 100644
index 00000000..798f151b
--- /dev/null
+++ b/bookkeeper-server/src/test/java/org/apache/bookkeeper/test/OpStatTest.java
@@ -0,0 +1,125 @@
+/*
+ *
+ * Licensed to the Apache Software Foundation (ASF) under one
+ * or more contributor license agreements.  See the NOTICE file
+ * distributed with this work for additional information
+ * regarding copyright ownership.  The ASF licenses this file
+ * to you under the Apache License, Version 2.0 (the
+ * "License"); you may not use this file except in compliance
+ * with the License.  You may obtain a copy of the License at
+ *
+ *   http://www.apache.org/licenses/LICENSE-2.0
+ *
+ * Unless required by applicable law or agreed to in writing,
+ * software distributed under the License is distributed on an
+ * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
+ * KIND, either express or implied.  See the License for the
+ * specific language governing permissions and limitations
+ * under the License.
+ *
+ */
+
+package org.apache.bookkeeper.test;
+
+import static org.apache.bookkeeper.bookie.BookKeeperServerStats.SERVER_SCOPE;
+import static org.junit.Assert.assertTrue;
+
+import java.util.function.BiConsumer;
+import org.apache.bookkeeper.client.BookKeeper;
+import org.apache.bookkeeper.client.LedgerHandle;
+import org.apache.bookkeeper.util.MathUtils;
+import org.junit.After;
+import org.junit.Before;
+import org.junit.Test;
+
+/**
+ * Basic tests to verify that stats are being updated as expected.
+ */
+public class OpStatTest extends BookKeeperClusterTestCase {
+    private LedgerHandle lh;
+
+    public OpStatTest() {
+        super(1);
+    }
+
+    @Before
+    @Override
+    public void setUp() throws Exception {
+        super.setUp();
+        lh = bkc.createLedger(1, 1, BookKeeper.DigestType.CRC32, "".getBytes());
+        resetBookieOpLoggers();
+    }
+
+    @After
+    @Override
+    public void tearDown() throws Exception {
+        lh.close();
+        lh = null;
+        super.tearDown();
+    }
+
+    private void validateOpStat(TestStatsProvider stats, String path, BiConsumer<Long, Double> f) {
+        assertTrue(stats != null);
+        TestStatsProvider.TestOpStatsLogger logger = stats.getOpStatsLogger(path);
+        assertTrue(logger != null);
+        f.accept(logger.getSuccessCount(), logger.getSuccessAverage());
+    }
+
+    private void validateOpStat(TestStatsProvider stats, String paths[], BiConsumer<Long, Double> f) {
+        for (String path : paths) {
+            validateOpStat(stats, path, f);
+        }
+    }
+
+    @Test
+    public void testTopLevelBookieWriteCounters() throws Exception {
+        long startNanos = MathUtils.nowInNano();
+        lh.addEntry("test".getBytes());
+        long elapsed = MathUtils.elapsedNanos(startNanos);
+        TestStatsProvider stats = getStatsProvider(0);
+        validateOpStat(stats, new String[]{
+                SERVER_SCOPE + ".ADD_ENTRY",
+                SERVER_SCOPE + ".ADD_ENTRY_REQUEST",
+                SERVER_SCOPE + ".BookieWriteThreadPool.task_queued",
+                SERVER_SCOPE + ".BookieWriteThreadPool.task_execution",
+                SERVER_SCOPE + ".CHANNEL_WRITE"
+        }, (count, average) -> {
+            assertTrue(count == 1);
+            assertTrue(average > 0);
+            assertTrue(average <= elapsed);
+        });
+        validateOpStat(stats, new String[]{
+                SERVER_SCOPE + ".CHANNEL_WRITE"
+        }, (count, average) -> {
+            assertTrue(count > 0);
+            assertTrue(average > 0);
+            assertTrue(average <= elapsed);
+        });
+    }
+
+    @Test
+    public void testTopLevelBookieReadCounters() throws Exception {
+        long startNanos = MathUtils.nowInNano();
+        lh.addEntry("test".getBytes());
+        lh.readEntries(0, 0);
+        long elapsed = MathUtils.elapsedNanos(startNanos);
+        TestStatsProvider stats = getStatsProvider(0);
+        validateOpStat(stats, new String[]{
+                SERVER_SCOPE + ".READ_ENTRY",
+                SERVER_SCOPE + ".READ_ENTRY_REQUEST",
+                SERVER_SCOPE + ".BookieReadThreadPool.task_queued",
+                SERVER_SCOPE + ".BookieReadThreadPool.task_execution",
+        }, (count, average) -> {
+            assertTrue(count == 1);
+            assertTrue(average > 0);
+            assertTrue(average <= elapsed);
+        });
+        validateOpStat(stats, new String[]{
+                SERVER_SCOPE + ".CHANNEL_WRITE"
+        }, (count, average) -> {
+            assertTrue(count > 0);
+            assertTrue(average > 0);
+            assertTrue(average <= elapsed);
+        });
+    }
+}
diff --git a/bookkeeper-server/src/test/java/org/apache/bookkeeper/test/TestStatsProvider.java b/bookkeeper-server/src/test/java/org/apache/bookkeeper/test/TestStatsProvider.java
new file mode 100644
index 00000000..b55ebad2
--- /dev/null
+++ b/bookkeeper-server/src/test/java/org/apache/bookkeeper/test/TestStatsProvider.java
@@ -0,0 +1,245 @@
+/*
+ *
+ * Licensed to the Apache Software Foundation (ASF) under one
+ * or more contributor license agreements.  See the NOTICE file
+ * distributed with this work for additional information
+ * regarding copyright ownership.  The ASF licenses this file
+ * to you under the Apache License, Version 2.0 (the
+ * "License"); you may not use this file except in compliance
+ * with the License.  You may obtain a copy of the License at
+ *
+ *   http://www.apache.org/licenses/LICENSE-2.0
+ *
+ * Unless required by applicable law or agreed to in writing,
+ * software distributed under the License is distributed on an
+ * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
+ * KIND, either express or implied.  See the License for the
+ * specific language governing permissions and limitations
+ * under the License.
+ *
+ */
+
+package org.apache.bookkeeper.test;
+
+import java.util.Map;
+import java.util.concurrent.ConcurrentHashMap;
+import java.util.concurrent.TimeUnit;
+import java.util.concurrent.atomic.AtomicLong;
+import java.util.function.BiConsumer;
+import org.apache.bookkeeper.stats.Counter;
+import org.apache.bookkeeper.stats.Gauge;
+import org.apache.bookkeeper.stats.OpStatsData;
+import org.apache.bookkeeper.stats.OpStatsLogger;
+import org.apache.bookkeeper.stats.StatsLogger;
+import org.apache.bookkeeper.stats.StatsProvider;
+import org.apache.commons.configuration.Configuration;
+
+/**
+ * Simple in-memory stat provider for use in unit tests.
+ */
+public class TestStatsProvider implements StatsProvider {
+    /**
+     * In-memory counter.
+     */
+    public class TestCounter implements Counter {
+        private AtomicLong val = new AtomicLong(0);
+
+        @Override
+        public void clear() {
+            val.set(0);
+        }
+
+        @Override
+        public void inc() {
+            val.incrementAndGet();
+        }
+
+        @Override
+        public void dec() {
+            val.decrementAndGet();
+        }
+
+        @Override
+        public void add(long delta) {
+            val.addAndGet(delta);
+        }
+
+        @Override
+        public Long get() {
+            return val.get();
+        }
+    }
+
+    /**
+     * In-memory StatsLogger.
+     */
+    public class TestOpStatsLogger implements OpStatsLogger {
+        private long successCount;
+        private long successValue;
+
+        private long failureCount;
+        private long failureValue;
+
+        TestOpStatsLogger() {
+            clear();
+        }
+
+        @Override
+        public void registerFailedEvent(long eventLatency, TimeUnit unit) {
+            registerFailedValue(unit.convert(eventLatency, TimeUnit.NANOSECONDS));
+        }
+
+        @Override
+        public void registerSuccessfulEvent(long eventLatency, TimeUnit unit) {
+            registerSuccessfulValue(unit.convert(eventLatency, TimeUnit.NANOSECONDS));
+        }
+
+        @Override
+        public synchronized void registerSuccessfulValue(long value) {
+            successCount++;
+            successValue += value;
+        }
+
+        @Override
+        public synchronized void registerFailedValue(long value) {
+            failureCount++;
+            failureValue += value;
+        }
+
+        @Override
+        public OpStatsData toOpStatsData() {
+            // Not supported at this time
+            return null;
+        }
+
+        @Override
+        public synchronized void clear() {
+            successCount = 0;
+            successValue = 0;
+            failureCount = 0;
+            failureValue = 0;
+        }
+
+        public synchronized double getSuccessAverage() {
+            if (successCount == 0) {
+                return 0;
+            }
+            return successValue / (double) successCount;
+        }
+
+        public synchronized long getSuccessCount() {
+            return successCount;
+        }
+    }
+
+    /**
+     * In-memory Logger.
+     */
+    public class TestStatsLogger implements StatsLogger {
+        private String path;
+
+        TestStatsLogger(String path) {
+            this.path = path;
+        }
+
+        private String getSubPath(String name) {
+            if (path.isEmpty()) {
+                return name;
+            } else {
+                return path + "." + name;
+            }
+        }
+
+        @Override
+        public OpStatsLogger getOpStatsLogger(String name) {
+            return TestStatsProvider.this.getOrCreateOpStatsLogger(getSubPath(name));
+        }
+
+        @Override
+        public Counter getCounter(String name) {
+            return TestStatsProvider.this.getOrCreateCounter(getSubPath(name));
+        }
+
+        @Override
+        public <T extends Number> void registerGauge(String name, Gauge<T> gauge) {
+            TestStatsProvider.this.registerGauge(getSubPath(name), gauge);
+        }
+
+        @Override
+        public <T extends Number> void unregisterGauge(String name, Gauge<T> gauge) {
+            TestStatsProvider.this.unregisterGauge(getSubPath(name), gauge);
+        }
+
+        @Override
+        public StatsLogger scope(String name) {
+            return new TestStatsLogger(getSubPath(name));
+        }
+
+        @Override
+        public void removeScope(String name, StatsLogger statsLogger) {}
+    }
+
+    @Override
+    public void start(Configuration conf) {
+    }
+
+    @Override
+    public void stop() {
+    }
+
+    private Map<String, TestOpStatsLogger> opStatLoggerMap = new ConcurrentHashMap<>();
+    private Map<String, TestCounter> counterMap = new ConcurrentHashMap<>();
+    private Map<String, Gauge<? extends Number>> gaugeMap = new ConcurrentHashMap<>();
+
+    @Override
+    public StatsLogger getStatsLogger(String scope) {
+        return new TestStatsLogger(scope);
+    }
+
+    public TestOpStatsLogger getOpStatsLogger(String path) {
+        return opStatLoggerMap.get(path);
+    }
+
+    public TestCounter getCounter(String path) {
+        return counterMap.get(path);
+    }
+
+    public Gauge<? extends Number> getGauge(String path) {
+        return gaugeMap.get(path);
+    }
+
+    public void forEachOpStatLogger(BiConsumer<String, TestOpStatsLogger> f) {
+        for (Map.Entry<String, TestOpStatsLogger> entry : opStatLoggerMap.entrySet()) {
+            f.accept(entry.getKey(), entry.getValue());
+        }
+    }
+
+    public void clear() {
+        for (TestOpStatsLogger logger : opStatLoggerMap.values()) {
+            logger.clear();
+        }
+        for (TestCounter counter : counterMap.values()) {
+            counter.clear();
+        }
+    }
+
+    private TestOpStatsLogger getOrCreateOpStatsLogger(String path) {
+        return opStatLoggerMap.computeIfAbsent(
+                path,
+                (String s) -> new TestOpStatsLogger());
+    }
+
+    private TestCounter getOrCreateCounter(String path) {
+        return counterMap.computeIfAbsent(
+                path,
+                (String s) -> new TestCounter());
+    }
+
+    private <T extends Number> void registerGauge(String name, Gauge<T> gauge) {
+        gaugeMap.put(name, gauge);
+    }
+
+    private <T extends Number> void unregisterGauge(String name, Gauge<T> gauge) {
+        gaugeMap.remove(name, gauge);
+    }
+}
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
