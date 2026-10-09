This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 8b593bb579b6953d5eeb2d2505170a9aaa10ee26
- Commit message: 
- Diff:
```
commit 8b593bb579b6953d5eeb2d2505170a9aaa10ee26
Author: Clebert Suconic <clebertsuconic@apache.org>
Date:   Thu Apr 13 16:53:53 2017 -0400
---
 .../activemq/artemis/utils/SimpleFuture.java       |  74 +++---
 .../activemq/artemis/utils/SimpleFutureImpl.java   |  81 +++++++
 .../activemq/artemis/utils/SimpleFutureTest.java   |   4 +-
 .../artemis/core/journal/impl/JournalBase.java     |   9 +-
 .../core/journal/impl/JournalCompactor.java        |  85 +++++++
 .../artemis/core/journal/impl/JournalImpl.java     | 265 +++++++++++++--------
 .../core/journal/impl/JournalTransaction.java      |  10 +
 .../integration/journal/NIOJournalCompactTest.java | 103 +++++++-
 .../core/journal/impl/AlignedJournalImplTest.java  |   4 +-
 .../unit/core/journal/impl/JournalAsyncTest.java   |   1 +
 .../core/journal/impl/JournalImplTestBase.java     |  42 ++--
 11 files changed, 513 insertions(+), 165 deletions(-)

diff --git a/artemis-commons/src/main/java/org/apache/activemq/artemis/utils/SimpleFuture.java b/artemis-commons/src/main/java/org/apache/activemq/artemis/utils/SimpleFuture.java
index eedfef492..b871f24fb 100644
--- a/artemis-commons/src/main/java/org/apache/activemq/artemis/utils/SimpleFuture.java
+++ b/artemis-commons/src/main/java/org/apache/activemq/artemis/utils/SimpleFuture.java
@@ -17,63 +17,55 @@
 
 package org.apache.activemq.artemis.utils;
 
-import java.util.concurrent.CountDownLatch;
 import java.util.concurrent.ExecutionException;
 import java.util.concurrent.Future;
 import java.util.concurrent.TimeUnit;
 import java.util.concurrent.TimeoutException;
 
-public class SimpleFuture<V> implements Future<V> {
+public interface SimpleFuture<V> extends Future<V> {
 
-   public SimpleFuture() {
-   }
+   SimpleFuture dumb = new SimpleFuture() {
+      @Override
+      public void fail(Throwable e) {
 
-   V value;
-   Exception exception;
+      }
 
-   private final CountDownLatch latch = new CountDownLatch(1);
+      @Override
+      public void set(Object o) {
 
-   boolean canceled = false;
+      }
 
-   @Override
-   public boolean cancel(boolean mayInterruptIfRunning) {
-      canceled = true;
-      latch.countDown();
-      return true;
-   }
+      @Override
+      public boolean cancel(boolean mayInterruptIfRunning) {
+         return false;
+      }
 
-   @Override
-   public boolean isCancelled() {
-      return canceled;
-   }
+      @Override
+      public boolean isCancelled() {
+         return false;
+      }
 
-   @Override
-   public boolean isDone() {
-      return latch.getCount() <= 0;
-   }
+      @Override
+      public boolean isDone() {
+         return false;
+      }
 
-   public void fail(Exception e) {
-      this.exception = e;
-      latch.countDown();
-   }
+      @Override
+      public Object get() throws InterruptedException, ExecutionException {
+         return null;
+      }
 
-   @Override
-   public V get() throws InterruptedException, ExecutionException {
-      latch.await();
-      if (this.exception != null) {
-         throw new ExecutionException(this.exception);
+      @Override
+      public Object get(long timeout, TimeUnit unit) throws InterruptedException, ExecutionException, TimeoutException {
+         return null;
       }
-      return value;
-   }
+   };
 
-   public void set(V v) {
-      this.value = v;
-      latch.countDown();
+   static SimpleFuture dumb() {
+      return dumb;
    }
 
-   @Override
-   public V get(long timeout, TimeUnit unit) throws InterruptedException, ExecutionException, TimeoutException {
-      latch.await(timeout, unit);
-      return value;
-   }
+   void fail(Throwable e);
+
+   void set(V v);
 }
diff --git a/artemis-commons/src/main/java/org/apache/activemq/artemis/utils/SimpleFutureImpl.java b/artemis-commons/src/main/java/org/apache/activemq/artemis/utils/SimpleFutureImpl.java
new file mode 100644
index 000000000..fae91c221
--- /dev/null
+++ b/artemis-commons/src/main/java/org/apache/activemq/artemis/utils/SimpleFutureImpl.java
@@ -0,0 +1,81 @@
+/**
+ * Licensed to the Apache Software Foundation (ASF) under one or more
+ * contributor license agreements. See the NOTICE file distributed with
+ * this work for additional information regarding copyright ownership.
+ * The ASF licenses this file to You under the Apache License, Version 2.0
+ * (the "License"); you may not use this file except in compliance with
+ * the License. You may obtain a copy of the License at
+ *
+ * http://www.apache.org/licenses/LICENSE-2.0
+ *
+ * Unless required by applicable law or agreed to in writing, software
+ * distributed under the License is distributed on an "AS IS" BASIS,
+ * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
+ * See the License for the specific language governing permissions and
+ * limitations under the License.
+ */
+
+package org.apache.activemq.artemis.utils;
+
+import java.util.concurrent.CountDownLatch;
+import java.util.concurrent.ExecutionException;
+import java.util.concurrent.TimeUnit;
+import java.util.concurrent.TimeoutException;
+
+public class SimpleFutureImpl<V> implements SimpleFuture<V> {
+
+   public SimpleFutureImpl() {
+   }
+
+   V value;
+   Throwable exception;
+
+   private final CountDownLatch latch = new CountDownLatch(1);
+
+   boolean canceled = false;
+
+   @Override
+   public boolean cancel(boolean mayInterruptIfRunning) {
+      canceled = true;
+      latch.countDown();
+      return true;
+   }
+
+   @Override
+   public boolean isCancelled() {
+      return canceled;
+   }
+
+   @Override
+   public boolean isDone() {
+      return latch.getCount() <= 0;
+   }
+
+   @Override
+   public void fail(Throwable e) {
+      this.exception = e;
+      latch.countDown();
+   }
+
+   @Override
+   public V get() throws InterruptedException, ExecutionException {
+      latch.await();
+      if (this.exception != null) {
+         throw new ExecutionException(this.exception);
+      }
+      return value;
+   }
+
+   @Override
+   public void set(V v) {
+      this.value = v;
+      latch.countDown();
+   }
+
+   @Override
+   public V get(long timeout, TimeUnit unit) throws InterruptedException, ExecutionException, TimeoutException {
+      latch.await(timeout, unit);
+      return value;
+   }
+
+}
diff --git a/artemis-commons/src/test/java/org/apache/activemq/artemis/utils/SimpleFutureTest.java b/artemis-commons/src/test/java/org/apache/activemq/artemis/utils/SimpleFutureTest.java
index 00fd5d7dc..c3fa482c7 100644
--- a/artemis-commons/src/test/java/org/apache/activemq/artemis/utils/SimpleFutureTest.java
+++ b/artemis-commons/src/test/java/org/apache/activemq/artemis/utils/SimpleFutureTest.java
@@ -29,7 +29,7 @@ public class SimpleFutureTest {
    @Test
    public void testFuture() throws Exception {
       final long randomStart = System.currentTimeMillis();
-      final SimpleFuture<Long> simpleFuture = new SimpleFuture<>();
+      final SimpleFuture<Long> simpleFuture = new SimpleFutureImpl<>();
       Thread t = new Thread() {
          @Override
          public void run() {
@@ -44,7 +44,7 @@ public class SimpleFutureTest {
 
    @Test
    public void testException() throws Exception {
-      final SimpleFuture<Long> simpleFuture = new SimpleFuture<>();
+      final SimpleFuture<Long> simpleFuture = new SimpleFutureImpl<>();
       Thread t = new Thread() {
          @Override
          public void run() {
diff --git a/artemis-journal/src/main/java/org/apache/activemq/artemis/core/journal/impl/JournalBase.java b/artemis-journal/src/main/java/org/apache/activemq/artemis/core/journal/impl/JournalBase.java
index e6bd99ee4..2c03f928b 100644
--- a/artemis-journal/src/main/java/org/apache/activemq/artemis/core/journal/impl/JournalBase.java
+++ b/artemis-journal/src/main/java/org/apache/activemq/artemis/core/journal/impl/JournalBase.java
@@ -162,13 +162,10 @@ abstract class JournalBase implements Journal {
    abstract void scheduleReclaim();
 
    protected SyncIOCompletion getSyncCallback(final boolean sync) {
-      if (supportsCallback) {
-         if (sync) {
-            return new SimpleWaitIOCallback();
-         }
-         return DummyCallback.getInstance();
+      if (sync) {
+         return new SimpleWaitIOCallback();
       }
-      return null;
+      return DummyCallback.getInstance();
    }
 
    private static final class NullEncoding implements EncodingSupport {
diff --git a/artemis-journal/src/main/java/org/apache/activemq/artemis/core/journal/impl/JournalCompactor.java b/artemis-journal/src/main/java/org/apache/activemq/artemis/core/journal/impl/JournalCompactor.java
index 1ac567613..8b89c3ed9 100644
--- a/artemis-journal/src/main/java/org/apache/activemq/artemis/core/journal/impl/JournalCompactor.java
+++ b/artemis-journal/src/main/java/org/apache/activemq/artemis/core/journal/impl/JournalCompactor.java
@@ -17,6 +17,7 @@
 package org.apache.activemq.artemis.core.journal.impl;
 
 import java.util.ArrayList;
+import java.util.Arrays;
 import java.util.HashMap;
 import java.util.LinkedList;
 import java.util.List;
@@ -139,10 +140,16 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
     * This methods informs the Compactor about the existence of a pending (non committed) transaction
     */
    public void addPendingTransaction(final long transactionID, final long[] ids) {
+      if (logger.isTraceEnabled()) {
+         logger.trace("addPendingTransaction::tx=" + transactionID + ", ids=" + Arrays.toString(ids));
+      }
       pendingTransactions.put(transactionID, new PendingTransaction(ids));
    }
 
    public void addCommandCommit(final JournalTransaction liveTransaction, final JournalFile currentFile) {
+      if (logger.isTraceEnabled()) {
+         logger.trace("addCommandCommit " + liveTransaction.getId());
+      }
       pendingCommands.add(new CommitCompactCommand(liveTransaction, currentFile));
 
       long[] ids = liveTransaction.getPositiveArray();
@@ -170,6 +177,9 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
    }
 
    public void addCommandRollback(final JournalTransaction liveTransaction, final JournalFile currentFile) {
+      if (logger.isTraceEnabled()) {
+         logger.trace("addCommandRollback " + liveTransaction + " currentFile " + currentFile);
+      }
       pendingCommands.add(new RollbackCompactCommand(liveTransaction, currentFile));
    }
 
@@ -178,6 +188,9 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
     * @param usedFile
     */
    public void addCommandDelete(final long id, final JournalFile usedFile) {
+      if (logger.isTraceEnabled()) {
+         logger.trace("addCommandDelete id " + id + " usedFile " + usedFile);
+      }
       pendingCommands.add(new DeleteCompactCommand(id, usedFile));
    }
 
@@ -186,6 +199,9 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
     * @param usedFile
     */
    public void addCommandUpdate(final long id, final JournalFile usedFile, final int size) {
+      if (logger.isTraceEnabled()) {
+         logger.trace("addCommandUpdate id " + id + " usedFile " + usedFile + " size " + size);
+      }
       pendingCommands.add(new UpdateCompactCommand(id, usedFile, size));
    }
 
@@ -241,6 +257,9 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
     */
    public void replayPendingCommands() {
       for (CompactCommand command : pendingCommands) {
+         if (logger.isTraceEnabled()) {
+            logger.trace("Replay " + command);
+         }
          try {
             command.execute();
          } catch (Exception e) {
@@ -256,6 +275,9 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
 
    @Override
    public void onReadAddRecord(final RecordInfo info) throws Exception {
+      if (logger.isTraceEnabled()) {
+         logger.trace("Read Record " + info);
+      }
       if (lookupRecord(info.id)) {
          JournalInternalRecord addRecord = new JournalAddRecord(true, info.id, info.getUserRecordType(), EncoderPersister.getInstance(), new ByteArrayEncoding(info.data));
          addRecord.setCompactCount((short) (info.compactCount + 1));
@@ -270,6 +292,9 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
 
    @Override
    public void onReadAddRecordTX(final long transactionID, final RecordInfo info) throws Exception {
+      if (logger.isTraceEnabled()) {
+         logger.trace("Read Add Recprd TX " + transactionID + " info " + info);
+      }
       if (pendingTransactions.get(transactionID) != null || lookupRecord(info.id)) {
          JournalTransaction newTransaction = getNewJournalTransaction(transactionID);
 
@@ -288,6 +313,10 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
    @Override
    public void onReadCommitRecord(final long transactionID, final int numberOfRecords) throws Exception {
 
+      if (logger.isTraceEnabled()) {
+         logger.trace("onReadCommitRecord " + transactionID);
+      }
+
       if (pendingTransactions.get(transactionID) != null) {
          // Sanity check, this should never happen
          ActiveMQJournalLogger.LOGGER.inconsistencyDuringCompacting(transactionID);
@@ -307,6 +336,10 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
 
    @Override
    public void onReadDeleteRecord(final long recordID) throws Exception {
+      if (logger.isTraceEnabled()) {
+         logger.trace("onReadDeleteRecord " + recordID);
+      }
+
       if (newRecords.get(recordID) != null) {
          // Sanity check, it should never happen
          ActiveMQJournalLogger.LOGGER.inconsistencyDuringCompactingDelete(recordID);
@@ -316,6 +349,10 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
 
    @Override
    public void onReadDeleteRecordTX(final long transactionID, final RecordInfo info) throws Exception {
+      if (logger.isTraceEnabled()) {
+         logger.trace("onReadDeleteRecordTX " + transactionID + " info " + info);
+      }
+
       if (pendingTransactions.get(transactionID) != null) {
          JournalTransaction newTransaction = getNewJournalTransaction(transactionID);
 
@@ -339,6 +376,10 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
    public void onReadPrepareRecord(final long transactionID,
                                    final byte[] extraData,
                                    final int numberOfRecords) throws Exception {
+      if (logger.isTraceEnabled()) {
+         logger.trace("onReadPrepareRecord " + transactionID);
+      }
+
       if (pendingTransactions.get(transactionID) != null) {
 
          JournalTransaction newTransaction = getNewJournalTransaction(transactionID);
@@ -356,6 +397,10 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
 
    @Override
    public void onReadRollbackRecord(final long transactionID) throws Exception {
+      if (logger.isTraceEnabled()) {
+         logger.trace("onReadRollbackRecord " + transactionID);
+      }
+
       if (pendingTransactions.get(transactionID) != null) {
          // Sanity check, this should never happen
          throw new IllegalStateException("Inconsistency during compacting: RollbackRecord ID = " + transactionID +
@@ -378,6 +423,10 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
 
    @Override
    public void onReadUpdateRecord(final RecordInfo info) throws Exception {
+      if (logger.isTraceEnabled()) {
+         logger.trace("onReadUpdateRecord " + info);
+      }
+
       if (lookupRecord(info.id)) {
          JournalInternalRecord updateRecord = new JournalAddRecord(false, info.id, info.userRecordType, EncoderPersister.getInstance(), new ByteArrayEncoding(info.data));
 
@@ -399,6 +448,10 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
 
    @Override
    public void onReadUpdateRecordTX(final long transactionID, final RecordInfo info) throws Exception {
+      if (logger.isTraceEnabled()) {
+         logger.trace("onReadUpdateRecordTX " + info);
+      }
+
       if (pendingTransactions.get(transactionID) != null || lookupRecord(info.id)) {
          JournalTransaction newTransaction = getNewJournalTransaction(transactionID);
 
@@ -423,8 +476,15 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
    private JournalTransaction getNewJournalTransaction(final long transactionID) {
       JournalTransaction newTransaction = newTransactions.get(transactionID);
       if (newTransaction == null) {
+         if (logger.isTraceEnabled()) {
+            logger.trace("creating new journal Transaction " + transactionID);
+         }
          newTransaction = new JournalTransaction(transactionID, this);
          newTransactions.put(transactionID, newTransaction);
+      } else if (logger.isTraceEnabled()) {
+         // just logging
+         logger.trace("reusing TX " + transactionID);
+
       }
       return newTransaction;
    }
@@ -485,6 +545,15 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
          JournalRecord updateRecord = journal.getRecords().get(id);
          updateRecord.addUpdateFile(usedFile, size);
       }
+
+      @Override
+      public String toString() {
+         return "UpdateCompactCommand{" +
+            "id=" + id +
+            ", usedFile=" + usedFile +
+            ", size=" + size +
+            '}';
+      }
    }
 
    private class CommitCompactCommand extends CompactCommand {
@@ -510,6 +579,14 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
          }
          newTransactions.remove(liveTransaction.getId());
       }
+
+      @Override
+      public String toString() {
+         return "CommitCompactCommand{" +
+            "commitFile=" + commitFile +
+            ", liveTransaction=" + liveTransaction +
+            '}';
+      }
    }
 
    private class RollbackCompactCommand extends CompactCommand {
@@ -535,6 +612,14 @@ public class JournalCompactor extends AbstractJournalUpdateTask implements Journ
          }
          newTransactions.remove(liveTransaction.getId());
       }
+
+      @Override
+      public String toString() {
+         return "RollbackCompactCommand{" +
+            "liveTransaction=" + liveTransaction +
+            ", rollbackFile=" + rollbackFile +
+            '}';
+      }
    }
 
    @Override
diff --git a/artemis-journal/src/main/java/org/apache/activemq/artemis/core/journal/impl/JournalImpl.java b/artemis-journal/src/main/java/org/apache/activemq/artemis/core/journal/impl/JournalImpl.java
index 24bb91607..81ae9c0fe 100644
--- a/artemis-journal/src/main/java/org/apache/activemq/artemis/core/journal/impl/JournalImpl.java
+++ b/artemis-journal/src/main/java/org/apache/activemq/artemis/core/journal/impl/JournalImpl.java
@@ -78,6 +78,7 @@ import org.apache.activemq.artemis.utils.DataConstants;
 import org.apache.activemq.artemis.utils.ExecutorFactory;
 import org.apache.activemq.artemis.utils.OrderedExecutorFactory;
 import org.apache.activemq.artemis.utils.SimpleFuture;
+import org.apache.activemq.artemis.utils.SimpleFutureImpl;
 import org.jboss.logging.Logger;
 
 /**
@@ -619,6 +620,10 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
             // At this point everything is checked. So we relax and just load
             // the data now.
 
+            if (logger.isTraceEnabled()) {
+               logger.trace("reading " + recordID + ", userRecordType=" + userRecordType + ", compactCount=" + compactCount);
+            }
+
             switch (recordType) {
                case ADD_RECORD: {
                   reader.onReadAddRecord(new RecordInfo(recordID, userRecordType, record, false, compactCount));
@@ -721,6 +726,13 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
       lineUpContext(callback);
       pendingRecords.add(id);
 
+      if (logger.isTraceEnabled()) {
+         logger.trace("scheduling appendAddRecord::id=" + id +
+                         ", userRecordType=" +
+                         recordType +
+                         ", record = " + record);
+      }
+
 
       final SimpleFuture<Boolean> result = newSyncAndCallbackResult(sync, callback);
       appendExecutor.execute(new Runnable() {
@@ -740,13 +752,10 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
                                              ", usedFile = " +
                                              usedFile);
                }
-               if (result != null) {
-                  result.set(true);
-               }
-            } catch (Exception e) {
-               if (result != null) {
-                  result.fail(e);
-               }
+               result.set(true);
+            } catch (Throwable e) {
+               result.fail(e);
+               setErrorCondition(callback, null, e);
                logger.error("appendAddRecord::"  + e, e);
             } finally {
                pendingRecords.remove(id);
@@ -755,9 +764,7 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
          }
       });
 
-      if (result != null) {
-         result.get();
-      }
+      result.get();
    }
 
    @Override
@@ -771,6 +778,12 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
       lineUpContext(callback);
       checkKnownRecordID(id);
 
+      if (logger.isTraceEnabled()) {
+         logger.trace("scheduling appendUpdateRecord::id=" + id +
+                         ", userRecordType=" +
+                         recordType);
+      }
+
       final SimpleFuture<Boolean> result = newSyncAndCallbackResult(sync, callback);
 
       appendExecutor.execute(new Runnable() {
@@ -798,13 +811,10 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
                   jrnRecord.addUpdateFile(usedFile, updateRecord.getEncodeSize());
                }
 
-               if (result != null) {
-                  result.set(true);
-               }
+               result.set(true);
             } catch (Exception e) {
-               if (result != null) {
-                  result.fail(e);
-               }
+               result.fail(e);
+               setErrorCondition(callback, null, e);
                logger.error("appendUpdateRecord:" + e, e);
             } finally {
                journalLock.readLock().unlock();
@@ -812,13 +822,17 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
          }
       });
 
-      if (result != null) {
-         result.get();
-      }
+      result.get();
    }
 
    @Override
    public void appendDeleteRecord(final long id, final boolean sync, final IOCompletion callback) throws Exception {
+
+      if (logger.isTraceEnabled()) {
+         logger.trace("scheduling appendDeleteRecord::id=" + id);
+      }
+
+
       checkJournalIsLoaded();
       lineUpContext(callback);
       checkKnownRecordID(id);
@@ -848,13 +862,9 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
                } else {
                   record.delete(usedFile);
                }
-               if (result != null) {
-                  result.set(true);
-               }
+               result.set(true);
             } catch (Exception e) {
-               if (result != null) {
-                  result.fail(e);
-               }
+               result.fail(e);
                logger.error("appendDeleteRecord:" + e, e);
             } finally {
                journalLock.readLock().unlock();
@@ -862,13 +872,11 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
          }
       });
 
-      if (result != null) {
-         result.get();
-      }
+      result.get();
    }
 
-   private static SimpleFuture<Boolean> newSyncAndCallbackResult(boolean sync, IOCompletion callback) {
-      return (sync && callback == null) ? new SimpleFuture<Boolean>() : null;
+   private static SimpleFuture newSyncAndCallbackResult(boolean sync, IOCompletion callback) {
+      return (sync && callback == null) ? new SimpleFutureImpl<>() : SimpleFuture.dumb();
    }
 
    @Override
@@ -878,16 +886,28 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
                                             final Persister persister,
                                             final Object record) throws Exception {
       checkJournalIsLoaded();
+      if (logger.isTraceEnabled()) {
+         logger.trace("scheduling appendAddRecordTransactional:txID=" + txID +
+                         ",id=" +
+                         id +
+                         ", userRecordType=" +
+                         recordType +
+                         ", record = " + record);
+      }
 
-      final JournalTransaction tx = getTransactionInfo(txID);
-      tx.checkErrorCondition();
 
       appendExecutor.execute(new Runnable() {
 
          @Override
          public void run() {
             journalLock.readLock().lock();
+
+            final JournalTransaction tx = getTransactionInfo(txID);
+
             try {
+               if (tx != null) {
+                  tx.checkErrorCondition();
+               }
                JournalInternalRecord addRecord = new JournalAddRecordTX(true, txID, id, recordType, persister, record);
                JournalFile usedFile = appendRecord(addRecord, false, false, tx, null);
 
@@ -905,7 +925,7 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
                tx.addPositive(usedFile, id, addRecord.getEncodeSize());
             } catch (Exception e) {
                logger.error("appendAddRecordTransactional:" + e, e);
-               setErrorCondition(tx, e);
+               setErrorCondition(null, tx, e);
             } finally {
                journalLock.readLock().unlock();
             }
@@ -918,7 +938,7 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
          return;
       }
 
-      final SimpleFuture<Boolean> known = new SimpleFuture<>();
+      final SimpleFuture<Boolean> known = new SimpleFutureImpl<>();
 
       // retry on the append thread. maybe the appender thread is not keeping up.
       appendExecutor.execute(new Runnable() {
@@ -957,17 +977,28 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
                                                final byte recordType,
                                                final Persister persister,
                                                final Object record) throws Exception {
+      if ( logger.isTraceEnabled() ) {
+         logger.trace( "scheduling appendUpdateRecordTransactional::txID=" + txID +
+                          ",id=" +
+                          id +
+                          ", userRecordType=" +
+                          recordType +
+                          ", record = " + record);
+      }
+
       checkJournalIsLoaded();
 
-      final JournalTransaction tx = getTransactionInfo(txID);
-      tx.checkErrorCondition();
 
       appendExecutor.execute(new Runnable() {
 
          @Override
          public void run() {
             journalLock.readLock().lock();
+
+            final JournalTransaction tx = getTransactionInfo(txID);
+
             try {
+               tx.checkErrorCondition();
 
                JournalInternalRecord updateRecordTX = new JournalAddRecordTX( false, txID, id, recordType, persister, record );
                JournalFile usedFile = appendRecord( updateRecordTX, false, false, tx, null );
@@ -986,7 +1017,7 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
                tx.addPositive( usedFile, id, updateRecordTX.getEncodeSize() );
             } catch ( Exception e ) {
                logger.error("appendUpdateRecordTransactional:" +  e.getMessage(), e );
-               setErrorCondition( tx, e );
+               setErrorCondition(null, tx, e );
             } finally {
                journalLock.readLock().unlock();
             }
@@ -998,16 +1029,26 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
    public void appendDeleteRecordTransactional(final long txID,
                                                final long id,
                                                final EncodingSupport record) throws Exception {
-      checkJournalIsLoaded();
+      if (logger.isTraceEnabled()) {
+         logger.trace("scheduling appendDeleteRecordTransactional::txID=" + txID +
+                         ", id=" +
+                         id);
+      }
+
 
-      final JournalTransaction tx = getTransactionInfo(txID);
-      tx.checkErrorCondition();
+      checkJournalIsLoaded();
 
       appendExecutor.execute(new Runnable() {
          @Override
          public void run() {
             journalLock.readLock().lock();
+
+            final JournalTransaction tx = getTransactionInfo(txID);
+
             try {
+               if (tx != null) {
+                  tx.checkErrorCondition();
+               }
 
                JournalInternalRecord deleteRecordTX = new JournalDeleteRecordTX(txID, id, record);
                JournalFile usedFile = appendRecord(deleteRecordTX, false, false, tx, null);
@@ -1023,7 +1064,7 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
                tx.addNegative(usedFile, id);
             } catch (Exception e) {
                logger.error("appendDeleteRecordTransactional:" + e, e);
-               setErrorCondition(tx, e);
+               setErrorCondition(null, tx, e);
             } finally {
                journalLock.readLock().unlock();
             }
@@ -1050,16 +1091,22 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
       checkJournalIsLoaded();
       lineUpContext(callback);
 
-      final JournalTransaction tx = getTransactionInfo(txID);
-      tx.checkErrorCondition();
+      if (logger.isTraceEnabled()) {
+         logger.trace("scheduling appendPrepareRecord::txID=" + txID);
+      }
 
-      final SimpleFuture<Boolean> result = newSyncAndCallbackResult(sync, callback);
+      final SimpleFuture<JournalTransaction> result = newSyncAndCallbackResult(sync, callback);
 
       appendExecutor.execute(new Runnable() {
          @Override
          public void run() {
             journalLock.readLock().lock();
+
+
+            final JournalTransaction tx = getTransactionInfo(txID);
+
             try {
+               tx.checkErrorCondition();
                JournalInternalRecord prepareRecord = new JournalCompleteRecordTX(TX_RECORD_TYPE.PREPARE, txID, transactionData);
                JournalFile usedFile = appendRecord(prepareRecord, true, sync, tx, callback);
 
@@ -1068,23 +1115,19 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
                }
 
                tx.prepare(usedFile);
-               if (result != null) {
-                  result.set(true);
-               }
             } catch (Exception e) {
-               if (result != null) {
-                  result.fail(e);
-               }
+               result.fail(e);
                logger.error("appendPrepareRecord:" + e, e);
-               setErrorCondition(tx, e);
+               setErrorCondition(callback, tx, e);
             } finally {
                journalLock.readLock().unlock();
+               result.set(tx);
             }
          }
       });
 
-      if (result != null) {
-         result.get();
+      JournalTransaction tx = result.get();
+      if (tx != null) {
          tx.checkErrorCondition();
       }
    }
@@ -1096,12 +1139,18 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
       }
    }
 
-   private void setErrorCondition(JournalTransaction jt, Throwable t) {
+   private void setErrorCondition(IOCallback otherCallback, JournalTransaction jt, Throwable t) {
+      TransactionCallback callback = null;
       if (jt != null) {
-         TransactionCallback callback = jt.getCurrentCallback();
+         callback = jt.getCurrentCallback();
          if (callback != null && callback.getErrorMessage() != null) {
             callback.onError(ActiveMQExceptionType.IO_ERROR.getCode(), t.getMessage());
          }
+
+      }
+
+      if (otherCallback != null && otherCallback != callback) {
+         otherCallback.onError(ActiveMQExceptionType.IO_ERROR.getCode(), t.getMessage());
       }
    }
 
@@ -1118,46 +1167,49 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
          lineUpContext(callback);
       }
 
-      final JournalTransaction tx = transactions.remove(txID);
 
-      if (tx == null) {
-         throw new IllegalStateException("Cannot find tx with id " + txID);
+      if (logger.isTraceEnabled()) {
+         logger.trace("scheduling appendCommitRecord::txID=" + txID );
       }
 
-      tx.checkErrorCondition();
-      final SimpleFuture<Boolean> result = newSyncAndCallbackResult(sync, callback);
+      JournalTransaction txcheck = transactions.get(txID);
+      if (txcheck != null) {
+         txcheck.checkErrorCondition();
+      }
+
+
+      final SimpleFuture<JournalTransaction> result = newSyncAndCallbackResult(sync, callback);
 
       appendExecutor.execute(new Runnable() {
          @Override
          public void run() {
             journalLock.readLock().lock();
+            // cannot remove otherwise compact may get lost
+            final JournalTransaction tx = transactions.remove(txID);
+
             try {
+               if (tx == null) {
+                  throw new IllegalStateException("Cannot find tx with id " + txID);
+               }
+
                JournalInternalRecord commitRecord = new JournalCompleteRecordTX(TX_RECORD_TYPE.COMMIT, txID, null);
                JournalFile usedFile = appendRecord(commitRecord, true, sync, tx, callback);
 
 
-               if (logger.isTraceEnabled()) {
-                  logger.trace("appendCommitRecord::txID=" + txID + ", usedFile = " + usedFile);
-               }
-
                tx.commit(usedFile);
-               if (result != null) {
-                  result.set(true);
-               }
-            } catch (Exception e) {
-               if (result != null) {
-                  result.fail(e);
-               }
+            } catch (Throwable e) {
+               result.fail(e);
                logger.error("appendCommitRecord:" + e, e);
-               setErrorCondition(tx, e);
+               setErrorCondition(callback, tx, e);
             } finally {
                journalLock.readLock().unlock();
+               result.set(tx);
             }
          }
       });
 
-      if (result != null) {
-         result.get();
+      JournalTransaction tx = result.get();
+      if (tx != null) {
          tx.checkErrorCondition();
       }
    }
@@ -1167,40 +1219,47 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
       checkJournalIsLoaded();
       lineUpContext(callback);
 
-      final JournalTransaction tx = transactions.remove(txID);
 
-      if (tx == null) {
-         throw new IllegalStateException("Cannot find tx with id " + txID);
+      if (logger.isTraceEnabled()) {
+         logger.trace("scheduling appendRollbackRecord::txID=" + txID );
       }
 
-      tx.checkErrorCondition();
-      final SimpleFuture<Boolean> result = newSyncAndCallbackResult(sync, callback);
+
+
+      final SimpleFuture<JournalTransaction> result = newSyncAndCallbackResult(sync, callback);
       appendExecutor.execute(new Runnable() {
          @Override
          public void run() {
             journalLock.readLock().lock();
+
+            final JournalTransaction tx = transactions.remove(txID);
             try {
+               if (logger.isTraceEnabled()) {
+                  logger.trace("appendRollbackRecord::txID=" + txID );
+               }
+
+               if (tx == null) {
+                  throw new IllegalStateException("Cannot find tx with id " + txID);
+               }
+
+
                JournalInternalRecord rollbackRecord = new JournalRollbackRecordTX(txID);
                JournalFile usedFile = appendRecord(rollbackRecord, false, sync, tx, callback);
 
                tx.rollback(usedFile);
-               if (result != null) {
-                  result.set(true);
-               }
-            } catch (Exception e) {
-               if (result != null) {
-                  result.fail(e);
-               }
+            } catch (Throwable e) {
+               result.fail(e);
                logger.error("appendRollbackRecord:" + e, e);
-               setErrorCondition(tx, e);
+               setErrorCondition(callback, tx, e);
             }  finally {
                journalLock.readLock().unlock();
+               result.set(tx);
             }
          }
       });
 
-      if (result != null) {
-         result.get();
+      JournalTransaction tx = result.get();
+      if (tx != null) {
          tx.checkErrorCondition();
       }
    }
@@ -1545,6 +1604,11 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
          }
       } finally {
          compactorLock.writeLock().unlock();
+         if (ActiveMQJournalLogger.LOGGER.isDebugEnabled()) {
+            ActiveMQJournalLogger.LOGGER.debug("JournalImpl::compact finishing");
+         }
+
+
       }
 
    }
@@ -2544,7 +2608,7 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
             }
             callback = txcallback;
          } else {
-            callback = null;
+            callback = parameterCallback;
          }
 
          // We need to add the number of records on currentFile if prepare or commit
@@ -2591,19 +2655,24 @@ public class JournalImpl extends JournalBase implements TestableJournal, Journal
    }
 
    private JournalTransaction getTransactionInfo(final long txID) {
-      JournalTransaction tx = transactions.get(txID);
+      journalLock.readLock().lock();
+      try {
+         JournalTransaction tx = transactions.get(txID);
 
-      if (tx == null) {
-         tx = new JournalTransaction(txID, this);
+         if (tx == null) {
+            tx = new JournalTransaction(txID, this);
 
-         JournalTransaction trans = transactions.putIfAbsent(txID, tx);
+            JournalTransaction trans = transactions.putIfAbsent(txID, tx);
 
-         if (trans != null) {
-            tx = trans;
+            if (trans != null) {
+               tx = trans;
+            }
          }
-      }
 
-      return tx;
+         return tx;
+      } finally {
+         journalLock.readLock().unlock();
+      }
    }
 
    /**
diff --git a/artemis-journal/src/main/java/org/apache/activemq/artemis/core/journal/impl/JournalTransaction.java b/artemis-journal/src/main/java/org/apache/activemq/artemis/core/journal/impl/JournalTransaction.java
index 8e40f3b96..36d585a80 100644
--- a/artemis-journal/src/main/java/org/apache/activemq/artemis/core/journal/impl/JournalTransaction.java
+++ b/artemis-journal/src/main/java/org/apache/activemq/artemis/core/journal/impl/JournalTransaction.java
@@ -28,9 +28,12 @@ import java.util.concurrent.atomic.AtomicInteger;
 
 import org.apache.activemq.artemis.api.core.ActiveMQExceptionType;
 import org.apache.activemq.artemis.core.journal.impl.dataformat.JournalInternalRecord;
+import org.jboss.logging.Logger;
 
 public class JournalTransaction {
 
+   private static final Logger logger = Logger.getLogger(JournalTransaction.class);
+
    private JournalRecordProvider journal;
 
    private List<JournalUpdate> pos;
@@ -229,10 +232,17 @@ public class JournalTransaction {
    public void commit(final JournalFile file) {
       JournalCompactor compactor = journal.getCompactor();
 
+      // The race lies here....
       if (compacting && compactor != null) {
+         if (logger.isTraceEnabled()) {
+            logger.trace("adding tx " + this.id + " into compacting");
+         }
          compactor.addCommandCommit(this, file);
       } else {
 
+         if (logger.isTraceEnabled()) {
+            logger.trace("no compact commit " + this.id);
+         }
          if (pos != null) {
             for (JournalUpdate trUpdate : pos) {
                JournalRecord posFiles = journal.getRecords().get(trUpdate.id);
diff --git a/tests/integration-tests/src/test/java/org/apache/activemq/artemis/tests/integration/journal/NIOJournalCompactTest.java b/tests/integration-tests/src/test/java/org/apache/activemq/artemis/tests/integration/journal/NIOJournalCompactTest.java
index a0f23d0ef..14f339358 100644
--- a/tests/integration-tests/src/test/java/org/apache/activemq/artemis/tests/integration/journal/NIOJournalCompactTest.java
+++ b/tests/integration-tests/src/test/java/org/apache/activemq/artemis/tests/integration/journal/NIOJournalCompactTest.java
@@ -29,6 +29,7 @@ import java.util.concurrent.TimeUnit;
 import java.util.concurrent.atomic.AtomicBoolean;
 import java.util.concurrent.atomic.AtomicInteger;
 import java.util.concurrent.atomic.AtomicLong;
+import java.util.concurrent.locks.LockSupport;
 
 import org.apache.activemq.artemis.api.core.Pair;
 import org.apache.activemq.artemis.core.config.Configuration;
@@ -53,12 +54,15 @@ import org.apache.activemq.artemis.utils.ActiveMQThreadFactory;
 import org.apache.activemq.artemis.utils.IDGenerator;
 import org.apache.activemq.artemis.utils.OrderedExecutorFactory;
 import org.apache.activemq.artemis.utils.SimpleIDGenerator;
+import org.jboss.logging.Logger;
 import org.junit.After;
 import org.junit.Assert;
 import org.junit.Test;
 
 public class NIOJournalCompactTest extends JournalImplTestBase {
 
+   private static final Logger logger = Logger.getLogger(NIOJournalCompactTest.class);
+
    private static final int NUMBER_OF_RECORDS = 1000;
 
    IDGenerator idGenerator = new SimpleIDGenerator(100000);
@@ -782,6 +786,97 @@ public class NIOJournalCompactTest extends JournalImplTestBase {
       loadAndCheck();
    }
 
+   @Test
+   public void testLoopStressAppends() throws Exception {
+      for (int i = 0; i < 10; i++) {
+         logger.info("repetition " + i);
+         testStressAppends();
+         tearDown();
+         setUp();
+      }
+   }
+
+   @Test
+   public void testStressAppends() throws Exception {
+      setup(2, 60 * 1024, true);
+
+      final int NUMBER_OF_RECORDS = 200;
+
+      SimpleIDGenerator idGen = new SimpleIDGenerator(1000);
+
+      createJournal();
+      journal.setAutoReclaim(false);
+
+      startJournal();
+      load();
+
+      AtomicBoolean running = new AtomicBoolean(true);
+      Thread t = new Thread() {
+         @Override
+         public void run() {
+            while (running.get()) {
+               journal.testCompact();
+            }
+         }
+      };
+      t.start();
+
+
+      for (int i = 0; i < NUMBER_OF_RECORDS; i++) {
+         long tx = idGen.generateID();
+         addTx(tx, idGen.generateID());
+         LockSupport.parkNanos(1000);
+         commit(tx);
+      }
+
+
+      running.set(false);
+
+      t.join(50000);
+      if (t.isAlive()) {
+         t.interrupt();
+         Assert.fail("supposed to join thread");
+      }
+
+      stopJournal();
+      createJournal();
+      startJournal();
+      loadAndCheck();
+   }
+
+   @Test
+   public void testSimpleCommitCompactInBetween() throws Exception {
+      setup(2, 60 * 1024, false);
+
+      final int NUMBER_OF_RECORDS = 1;
+
+      SimpleIDGenerator idGen = new SimpleIDGenerator(1000);
+
+      createJournal();
+      journal.setAutoReclaim(false);
+
+      startJournal();
+      load();
+
+
+      for (int i = 0; i < NUMBER_OF_RECORDS; i++) {
+         long tx = idGen.generateID();
+         addTx(tx, idGen.generateID());
+         journal.testCompact();
+         journal.testCompact();
+         journal.testCompact();
+         journal.testCompact();
+         logger.info("going to commit");
+         commit(tx);
+      }
+
+
+      stopJournal();
+      createJournal();
+      startJournal();
+      loadAndCheck();
+   }
+
    @Test
    public void testCompactAddAndUpdateFollowedByADelete2() throws Exception {
 
@@ -917,8 +1012,6 @@ public class NIOJournalCompactTest extends JournalImplTestBase {
 
       journal.testCompact();
 
-      System.out.println("Debug after compact\n" + journal.debug());
-
       stopJournal();
       createJournal();
       startJournal();
@@ -1666,10 +1759,14 @@ public class NIOJournalCompactTest extends JournalImplTestBase {
 
                      survivingMsgs.add(message.getMessageID());
 
+                     logger.info("Going to store " + message);
                      // This one will stay here forever
                      storage.storeMessage(message);
+                     logger.info("message storeed " + message);
 
+                     logger.info("Going to commit " + tx);
                      storage.commit(tx);
+                     logger.info("Commited " + tx);
 
                      ctx.executeOnCompletion(new IOCallback() {
                         @Override
@@ -1749,6 +1846,8 @@ public class NIOJournalCompactTest extends JournalImplTestBase {
 
          assertTrue("ioexecutor failed to terminate", ioexecutor.awaitTermination(30, TimeUnit.SECONDS));
 
+         Assert.assertEquals(0, errors.get());
+
       } catch (Throwable e) {
          e.printStackTrace();
          throw e;
diff --git a/tests/unit-tests/src/test/java/org/apache/activemq/artemis/tests/unit/core/journal/impl/AlignedJournalImplTest.java b/tests/unit-tests/src/test/java/org/apache/activemq/artemis/tests/unit/core/journal/impl/AlignedJournalImplTest.java
index be6e5b3d1..b85be80cd 100644
--- a/tests/unit-tests/src/test/java/org/apache/activemq/artemis/tests/unit/core/journal/impl/AlignedJournalImplTest.java
+++ b/tests/unit-tests/src/test/java/org/apache/activemq/artemis/tests/unit/core/journal/impl/AlignedJournalImplTest.java
@@ -371,7 +371,7 @@ public class AlignedJournalImplTest extends ActiveMQTestBase {
       Assert.assertEquals(0, transactions.size());
 
       try {
-         journalImpl.appendCommitRecord(1L, false);
+         journalImpl.appendCommitRecord(1L, true);
          // This was supposed to throw an exception, as the transaction was
          // forgotten (interrupted by a reload).
          Assert.fail("Supposed to throw exception");
@@ -419,7 +419,7 @@ public class AlignedJournalImplTest extends ActiveMQTestBase {
       Assert.assertEquals((Long) 78L, incompleteTransactions.get(1));
 
       try {
-         journalImpl.appendCommitRecord(77L, false);
+         journalImpl.appendCommitRecord(77L, true);
          // This was supposed to throw an exception, as the transaction was
          // forgotten (interrupted by a reload).
          Assert.fail("Supposed to throw exception");
diff --git a/tests/unit-tests/src/test/java/org/apache/activemq/artemis/tests/unit/core/journal/impl/JournalAsyncTest.java b/tests/unit-tests/src/test/java/org/apache/activemq/artemis/tests/unit/core/journal/impl/JournalAsyncTest.java
index 204600e2f..00539a709 100644
--- a/tests/unit-tests/src/test/java/org/apache/activemq/artemis/tests/unit/core/journal/impl/JournalAsyncTest.java
+++ b/tests/unit-tests/src/test/java/org/apache/activemq/artemis/tests/unit/core/journal/impl/JournalAsyncTest.java
@@ -138,6 +138,7 @@ public class JournalAsyncTest extends ActiveMQTestBase {
 
       try {
          journalImpl.appendAddRecordTransactional(1L, 2, (byte) 1, new SimpleEncoding(1, (byte) 0));
+         journalImpl.appendCommitRecord(1L, true);
          Assert.fail("Exception expected");
          // An exception already happened in one of the elements on this transaction.
          // We can't accept any more elements on the transaction
diff --git a/tests/unit-tests/src/test/java/org/apache/activemq/artemis/tests/unit/core/journal/impl/JournalImplTestBase.java b/tests/unit-tests/src/test/java/org/apache/activemq/artemis/tests/unit/core/journal/impl/JournalImplTestBase.java
index 3d70b1a63..e5650cbe7 100644
--- a/tests/unit-tests/src/test/java/org/apache/activemq/artemis/tests/unit/core/journal/impl/JournalImplTestBase.java
+++ b/tests/unit-tests/src/test/java/org/apache/activemq/artemis/tests/unit/core/journal/impl/JournalImplTestBase.java
@@ -19,6 +19,7 @@ package org.apache.activemq.artemis.tests.unit.core.journal.impl;
 import java.io.File;
 import java.io.FilenameFilter;
 import java.util.ArrayList;
+import java.util.HashSet;
 import java.util.Iterator;
 import java.util.LinkedHashMap;
 import java.util.LinkedList;
@@ -36,12 +37,15 @@ import org.apache.activemq.artemis.core.journal.TestableJournal;
 import org.apache.activemq.artemis.core.journal.impl.JournalImpl;
 import org.apache.activemq.artemis.tests.util.ActiveMQTestBase;
 import org.apache.activemq.artemis.utils.ReusableLatch;
+import org.jboss.logging.Logger;
 import org.junit.After;
 import org.junit.Assert;
 import org.junit.Before;
 
 public abstract class JournalImplTestBase extends ActiveMQTestBase {
 
+   private static final Logger logger = Logger.getLogger(JournalImplTestBase.class);
+
    protected List<RecordInfo> records = new LinkedList<>();
 
    protected TestableJournal journal;
@@ -156,13 +160,11 @@ public abstract class JournalImplTestBase extends ActiveMQTestBase {
          @Override
          public void onCompactDone() {
             latchDone.countDown();
-            System.out.println("Waiting on Compact");
             try {
                latchWait.await();
             } catch (InterruptedException e) {
                e.printStackTrace();
             }
-            System.out.println("Waiting on Compact Done");
          }
       };
 
@@ -520,19 +522,31 @@ public abstract class JournalImplTestBase extends ActiveMQTestBase {
     * @param actual
     */
    protected void printJournalLists(final List<RecordInfo> expected, final List<RecordInfo> actual) {
-      System.out.println("***********************************************");
-      System.out.println("Expected list:");
-      for (RecordInfo info : expected) {
-         System.out.println("Record " + info.id + " isUpdate = " + info.isUpdate);
-      }
-      if (actual != null) {
-         System.out.println("***********************************************");
-         System.out.println("Actual list:");
-         for (RecordInfo info : actual) {
-            System.out.println("Record " + info.id + " isUpdate = " + info.isUpdate);
-         }
+
+      HashSet<RecordInfo> expectedSet = new HashSet<>();
+      expectedSet.addAll(expected);
+
+
+      Assert.assertEquals("There are duplicated on the expected list", expectedSet.size(), expected.size());
+
+      HashSet<RecordInfo> actualSet = new HashSet<>();
+      actualSet.addAll(actual);
+
+      expectedSet.removeAll(actualSet);
+
+      for (RecordInfo info: expectedSet) {
+         logger.warn("The following record is missing:: " + info);
       }
-      System.out.println("***********************************************");
+
+
+      Assert.assertEquals("There are duplicates on the actual list", actualSet.size(), actualSet.size());
+
+
+
+      RecordInfo[] expectedArray = expected.toArray(new RecordInfo[expected.size()]);
+      RecordInfo[] actualArray = actual.toArray(new RecordInfo[actual.size()]);
+      Assert.assertArrayEquals(expectedArray, actualArray);
+
    }
 
    protected byte[] generateRecord(final int length) {
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
