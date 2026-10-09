This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 3ee6d03d40bf4ac6b8230d6c735f50527e1e93cc
- Commit message: Speed up deletes and updates of the 'words' table

FTS3 virtual tables don't support user-defined indices -- not even a
primary key. So let's use the rowid instead, which will significantly
speed up the delete/update-cascading triggers.

Also, fix two bugs. The row's
ID was intended to be equal to the corresponding sms._id, or the
corresponding part._id+(2<<32) for mms. However:

* In Java, the second operator for int shifts is modulo 32, so
  (2<<32) == (2<<0) == 2. Making the shifted value a long fixes it.
* The populateWordsTable method (which ran on upgrade) didn't add the
  offset at all.

With this fixed, we can get rid of the unindexable source_id and
table_to_use columns, which I can only assume were added because the
id offsetting scheme was not working as intended. We have no use for
the _id column either. We can drop and recreate the table easily, since
all the data is present in other tables anyway.

Before:
adb shell appops set root READ_SMS allow
adb shell appops set root WRITE_SMS allow
adb shell 'time content query --uri '\''content://mms-sms/search?pattern=sms 1 in thread 150'\'' > /dev/null'
    0m1.13s real     0m0.61s user     0m0.11s system
adb shell 'time content delete --uri content://sms --where '\''_id IN (1,2,3,4,5,6,7,8,9,10)'\'''
    0m3.08s real     0m0.51s user     0m0.17s system
adb shell 'time content delete --uri content://mms --where '\''_id IN (1,2,3,4,5,6,7,8,9,10)'\'''
    1m37.34s real     0m0.53s user     0m0.16s system
adb shell 'time content delete --uri content://mms-sms/conversations/110' # contains 20sms+1mms
    0m13.32s real     0m0.54s user     0m0.14s system
adb shell 'time content delete --uri content://mms-sms/conversations/25' # contains 500sms+10mms
    3m6.31s real     0m0.59s user     0m0.06s system
adb shell 'time content delete --uri content://mms-sms/conversations/1' # contains 990sms+40mms
    9m20.52s real     0m0.54s user     0m0.12s system

After:

adb shell appops set root READ_SMS allow
adb shell appops set root WRITE_SMS allow
adb shell 'time content query --uri '\''content://mms-sms/search?pattern=sms 1 in thread 150'\'' > /dev/null'
    0m1.09s real     0m0.59s user     0m0.13s system
adb shell 'time content delete --uri content://sms --where '\''_id IN (1,2,3,4,5,6,7,8,9,10)'\'''
    0m1.09s real     0m0.57s user     0m0.09s system
adb shell 'time content delete --uri content://mms --where '\''_id IN (1,2,3,4,5,6,7,8,9,10)'\'''
    1m35.69s real     0m0.58s user     0m0.13s system
adb shell 'time content delete --uri content://mms-sms/conversations/110' # contains 20sms+1mms
    0m9.51s real     0m0.56s user     0m0.11s system
adb shell 'time content delete --uri content://mms-sms/conversations/25' # contains 500sms+10mms
    1m21.99s real     0m0.57s user     0m0.09s system
adb shell 'time content delete --uri content://mms-sms/conversations/1' # contains 990sms+40mms
    5m31.34s real     0m0.56s user     0m0.09s system

These timings are on the "content" command, which includes all the
overhead of starting that process and communicating with the provider.
The time spent executing actual SQL statements is 800-900 ms lower.

(Depends on commit in frameworks/opt/telephony with the same Change-Id.)

Change-Id: Ia0f087f469775ca5864d85afde09b97a9f126862
Signed-off-by: mydongistiny <jaysonedson@gmail.com>
- Diff:
```
commit 3ee6d03d40bf4ac6b8230d6c735f50527e1e93cc
Author: Snild Dolkow <snild.dolkow@sonymobile.com>
Date:   Fri Oct 30 09:26:09 2015 +0100

    Speed up deletes and updates of the 'words' table
    
    FTS3 virtual tables don't support user-defined indices -- not even a
    primary key. So let's use the rowid instead, which will significantly
    speed up the delete/update-cascading triggers.
    
    Also, fix two bugs. The row's
    ID was intended to be equal to the corresponding sms._id, or the
    corresponding part._id+(2<<32) for mms. However:
    
    * In Java, the second operator for int shifts is modulo 32, so
      (2<<32) == (2<<0) == 2. Making the shifted value a long fixes it.
    * The populateWordsTable method (which ran on upgrade) didn't add the
      offset at all.
    
    With this fixed, we can get rid of the unindexable source_id and
    table_to_use columns, which I can only assume were added because the
    id offsetting scheme was not working as intended. We have no use for
    the _id column either. We can drop and recreate the table easily, since
    all the data is present in other tables anyway.
    
    Before:
    adb shell appops set root READ_SMS allow
    adb shell appops set root WRITE_SMS allow
    adb shell 'time content query --uri '\''content://mms-sms/search?pattern=sms 1 in thread 150'\'' > /dev/null'
        0m1.13s real     0m0.61s user     0m0.11s system
    adb shell 'time content delete --uri content://sms --where '\''_id IN (1,2,3,4,5,6,7,8,9,10)'\'''
        0m3.08s real     0m0.51s user     0m0.17s system
    adb shell 'time content delete --uri content://mms --where '\''_id IN (1,2,3,4,5,6,7,8,9,10)'\'''
        1m37.34s real     0m0.53s user     0m0.16s system
    adb shell 'time content delete --uri content://mms-sms/conversations/110' # contains 20sms+1mms
        0m13.32s real     0m0.54s user     0m0.14s system
    adb shell 'time content delete --uri content://mms-sms/conversations/25' # contains 500sms+10mms
        3m6.31s real     0m0.59s user     0m0.06s system
    adb shell 'time content delete --uri content://mms-sms/conversations/1' # contains 990sms+40mms
        9m20.52s real     0m0.54s user     0m0.12s system
    
    After:
    
    adb shell appops set root READ_SMS allow
    adb shell appops set root WRITE_SMS allow
    adb shell 'time content query --uri '\''content://mms-sms/search?pattern=sms 1 in thread 150'\'' > /dev/null'
        0m1.09s real     0m0.59s user     0m0.13s system
    adb shell 'time content delete --uri content://sms --where '\''_id IN (1,2,3,4,5,6,7,8,9,10)'\'''
        0m1.09s real     0m0.57s user     0m0.09s system
    adb shell 'time content delete --uri content://mms --where '\''_id IN (1,2,3,4,5,6,7,8,9,10)'\'''
        1m35.69s real     0m0.58s user     0m0.13s system
    adb shell 'time content delete --uri content://mms-sms/conversations/110' # contains 20sms+1mms
        0m9.51s real     0m0.56s user     0m0.11s system
    adb shell 'time content delete --uri content://mms-sms/conversations/25' # contains 500sms+10mms
        1m21.99s real     0m0.57s user     0m0.09s system
    adb shell 'time content delete --uri content://mms-sms/conversations/1' # contains 990sms+40mms
        5m31.34s real     0m0.56s user     0m0.09s system
    
    These timings are on the "content" command, which includes all the
    overhead of starting that process and communicating with the provider.
    The time spent executing actual SQL statements is 800-900 ms lower.
    
    (Depends on commit in frameworks/opt/telephony with the same Change-Id.)
    
    Change-Id: Ia0f087f469775ca5864d85afde09b97a9f126862
    Signed-off-by: mydongistiny <jaysonedson@gmail.com>
---
 .../android/providers/telephony/MmsProvider.java   |  6 ++--
 .../providers/telephony/MmsSmsDatabaseHelper.java  | 40 +++++++++++++++-------
 .../providers/telephony/MmsSmsProvider.java        | 10 +++---
 .../android/providers/telephony/SmsProvider.java   |  2 --
 4 files changed, 34 insertions(+), 24 deletions(-)

diff --git a/src/com/android/providers/telephony/MmsProvider.java b/src/com/android/providers/telephony/MmsProvider.java
index 5acfe13..ef3b3d6 100644
--- a/src/com/android/providers/telephony/MmsProvider.java
+++ b/src/com/android/providers/telephony/MmsProvider.java
@@ -504,11 +504,9 @@ public class MmsProvider extends ContentProvider {
 
                 // we're using the row id of the part table row but we're also using ids
                 // from the sms table so this divides the space into two large chunks.
-                // The row ids from the part table start at 2 << 32.
-                cv.put(Telephony.MmsSms.WordsTable.ID, (2 << 32) + rowId);
+                // The row ids from the part table start at 2^33.
+                cv.put(Telephony.MmsSms.WordsTable.ID, (1L << 33) + rowId);
                 cv.put(Telephony.MmsSms.WordsTable.INDEXED_TEXT, values.getAsString("text"));
-                cv.put(Telephony.MmsSms.WordsTable.SOURCE_ROW_ID, rowId);
-                cv.put(Telephony.MmsSms.WordsTable.TABLE_ID, 2);
                 db.insert(TABLE_WORDS, Telephony.MmsSms.WordsTable.INDEXED_TEXT, cv);
             }
 
diff --git a/src/com/android/providers/telephony/MmsSmsDatabaseHelper.java b/src/com/android/providers/telephony/MmsSmsDatabaseHelper.java
index 610418e..3c39254 100644
--- a/src/com/android/providers/telephony/MmsSmsDatabaseHelper.java
+++ b/src/com/android/providers/telephony/MmsSmsDatabaseHelper.java
@@ -235,7 +235,7 @@ public class MmsSmsDatabaseHelper extends SQLiteOpenHelper {
     private static boolean sFakeLowStorageTest = false;     // for testing only
 
     static final String DATABASE_NAME = "mmssms.db";
-    static final int DATABASE_VERSION = 64;
+    static final int DATABASE_VERSION = 65;
     private final Context mContext;
     private LowStorageMonitor mLowStorageMonitor;
 
@@ -512,8 +512,6 @@ public class MmsSmsDatabaseHelper extends SQLiteOpenHelper {
 
                         cv.put(Telephony.MmsSms.WordsTable.ID, id);
                         cv.put(Telephony.MmsSms.WordsTable.INDEXED_TEXT, body);
-                        cv.put(Telephony.MmsSms.WordsTable.SOURCE_ROW_ID, id);
-                        cv.put(Telephony.MmsSms.WordsTable.TABLE_ID, 1);
                         db.insert(TABLE_WORDS, Telephony.MmsSms.WordsTable.INDEXED_TEXT, cv);
                     }
                 }
@@ -543,10 +541,9 @@ public class MmsSmsDatabaseHelper extends SQLiteOpenHelper {
                         long id = mmsRows.getLong(0);         // 0 for Part._ID
                         String body = mmsRows.getString(1);   // 1 for Part.TEXT
 
-                        cv.put(Telephony.MmsSms.WordsTable.ID, id);
+                        // mms ID:s are offset at 2^33.
+                        cv.put(Telephony.MmsSms.WordsTable.ID, (1L << 33) + id);
                         cv.put(Telephony.MmsSms.WordsTable.INDEXED_TEXT, body);
-                        cv.put(Telephony.MmsSms.WordsTable.SOURCE_ROW_ID, id);
-                        cv.put(Telephony.MmsSms.WordsTable.TABLE_ID, 1);
                         db.insert(TABLE_WORDS, Telephony.MmsSms.WordsTable.INDEXED_TEXT, cv);
                     }
                 }
@@ -560,18 +557,19 @@ public class MmsSmsDatabaseHelper extends SQLiteOpenHelper {
 
     private void createWordsTables(SQLiteDatabase db) {
         try {
-            db.execSQL("CREATE VIRTUAL TABLE words USING FTS3 (_id INTEGER PRIMARY KEY, index_text TEXT, source_id INTEGER, table_to_use INTEGER);");
+            db.execSQL("CREATE VIRTUAL TABLE words USING FTS3 (index_text TEXT);");
 
             // monitor the sms table
             // NOTE don't handle inserts using a trigger because it has an unwanted
             // side effect:  the value returned for the last row ends up being the
             // id of one of the trigger insert not the original row insert.
             // Handle inserts manually in the provider.
+            db.execSQL("DROP TRIGGER IF EXISTS sms_words_update");
             db.execSQL("CREATE TRIGGER sms_words_update AFTER UPDATE ON sms BEGIN UPDATE words " +
-                    " SET index_text = NEW.body WHERE (source_id=NEW._id AND table_to_use=1); " +
-                    " END;");
+                    " SET index_text = NEW.body WHERE words.rowid=NEW._id; END;");
+            db.execSQL("DROP TRIGGER IF EXISTS sms_words_delete");
             db.execSQL("CREATE TRIGGER sms_words_delete AFTER DELETE ON sms BEGIN DELETE FROM " +
-                    "  words WHERE source_id = OLD._id AND table_to_use = 1; END;");
+                    "  words WHERE words.rowid = OLD._id; END;");
 
             populateWordsTable(db);
         } catch (Exception ex) {
@@ -789,12 +787,12 @@ public class MmsSmsDatabaseHelper extends SQLiteOpenHelper {
         // monitor the mms table
         db.execSQL("DROP TRIGGER IF EXISTS mms_words_update");
         db.execSQL("CREATE TRIGGER mms_words_update AFTER UPDATE ON part BEGIN UPDATE words " +
-                " SET index_text = NEW.text WHERE (source_id=NEW._id AND table_to_use=2); " +
+                " SET index_text = NEW.text WHERE words.rowid = (1 << 33) + NEW._id; " +
                 " END;");
 
         db.execSQL("DROP TRIGGER IF EXISTS mms_words_delete");
         db.execSQL("CREATE TRIGGER mms_words_delete AFTER DELETE ON part BEGIN DELETE FROM " +
-                " words WHERE source_id = OLD._id AND table_to_use = 2; END;");
+                " words WHERE words.rowid = (1 << 33) + OLD._id; END;");
 
         // Updates threads table whenever a message in pdu is updated.
         db.execSQL("DROP TRIGGER IF EXISTS pdu_update_thread_date_subject_on_update");
@@ -1447,7 +1445,25 @@ public class MmsSmsDatabaseHelper extends SQLiteOpenHelper {
             } finally {
                 db.endTransaction();
             }
+            // fall through
+        case 64:
+            if (currentVersion <= 64) {
+                return;
+            }
 
+            db.beginTransaction();
+            try {
+                // the words table contains no unique data -- we can just drop and recrate it.
+                db.execSQL("DROP TABLE IF EXISTS words");
+                createWordsTables(db);
+                createMmsTriggers(db); // drops and recreates the words triggers (among others)
+                db.setTransactionSuccessful();
+            } catch (Throwable ex) {
+                Log.e(TAG, ex.getMessage(), ex);
+                break;
+            } finally {
+                db.endTransaction();
+            }
             return;
         }
 
diff --git a/src/com/android/providers/telephony/MmsSmsProvider.java b/src/com/android/providers/telephony/MmsSmsProvider.java
index d5e0ef9..eeb040e 100644
--- a/src/com/android/providers/telephony/MmsSmsProvider.java
+++ b/src/com/android/providers/telephony/MmsSmsProvider.java
@@ -200,11 +200,10 @@ public class MmsSmsProvider extends ContentProvider {
                 + "date,"
                 + "date_sent,"
                 + "index_text,"
-                + "words._id "
+                + "words.rowid "
                 + "FROM " + smsTable + ",words "
                 + "WHERE (index_text MATCH ? "
-                + "AND " + smsTable + "._id=words.source_id "
-                + "AND words.table_to_use=1)";
+                + "AND " + smsTable + "._id=words.rowid)";
 
         // Search on the words table but return the rows from the corresponding parts table
         final String mmsQuery = "SELECT "
@@ -215,15 +214,14 @@ public class MmsSmsProvider extends ContentProvider {
                 + pduTable + ".date,"
                 + pduTable + ".date_sent,"
                 + "index_text,"
-                + "words._id "
+                + "words.rowid "
                 + "FROM " + pduTable + ",part,addr,words "
                 + "WHERE ((part.mid=" + pduTable + "._id) "
                 + "AND (addr.msg_id=" + pduTable + "._id) "
                 + "AND (addr.type=" + PduHeaders.TO + ") "
                 + "AND (part.ct='text/plain') "
                 + "AND (index_text MATCH ?) "
-                + "AND (part._id = words.source_id) "
-                + "AND (words.table_to_use=2))";
+                + "AND (part._id = words.rowid - (1<<33) ))";
 
         // This code queries the sms and mms tables and returns a unified result set
         // of text matches.  We query the sms table which is pretty simple.  We also
diff --git a/src/com/android/providers/telephony/SmsProvider.java b/src/com/android/providers/telephony/SmsProvider.java
index f50f804..d893f67 100644
--- a/src/com/android/providers/telephony/SmsProvider.java
+++ b/src/com/android/providers/telephony/SmsProvider.java
@@ -627,8 +627,6 @@ public class SmsProvider extends ContentProvider {
             ContentValues cv = new ContentValues();
             cv.put(Telephony.MmsSms.WordsTable.ID, rowID);
             cv.put(Telephony.MmsSms.WordsTable.INDEXED_TEXT, values.getAsString("body"));
-            cv.put(Telephony.MmsSms.WordsTable.SOURCE_ROW_ID, rowID);
-            cv.put(Telephony.MmsSms.WordsTable.TABLE_ID, 1);
             db.insert(TABLE_WORDS, Telephony.MmsSms.WordsTable.INDEXED_TEXT, cv);
         }
         if (rowID > 0) {
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
