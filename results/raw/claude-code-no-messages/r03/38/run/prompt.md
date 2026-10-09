This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: b53abc9a03fdf31635660bc6584716527ecfd1a5
- Commit message: 
- Diff:
```
commit b53abc9a03fdf31635660bc6584716527ecfd1a5
Author: Vincent Breitmoser <valodim@mugenguild.com>
Date:   Tue Mar 15 23:30:50 2016 +0100
---
 .../keychain/provider/KeychainDatabase.java              | 16 +++++++---------
 1 file changed, 7 insertions(+), 9 deletions(-)

diff --git a/OpenKeychain/src/main/java/org/sufficientlysecure/keychain/provider/KeychainDatabase.java b/OpenKeychain/src/main/java/org/sufficientlysecure/keychain/provider/KeychainDatabase.java
index 2a4d898bc..c3697997f 100644
--- a/OpenKeychain/src/main/java/org/sufficientlysecure/keychain/provider/KeychainDatabase.java
+++ b/OpenKeychain/src/main/java/org/sufficientlysecure/keychain/provider/KeychainDatabase.java
@@ -279,37 +279,35 @@ public class KeychainDatabase extends SQLiteOpenHelper {
                 db.execSQL("ALTER TABLE user_ids ADD COLUMN type INTEGER");
                 db.execSQL("ALTER TABLE user_ids ADD COLUMN attribute_data BLOB");
             case 7:
-                // consolidate
-            case 8:
                 // new table for allowed key ids in API
                 try {
                     db.execSQL(CREATE_API_APPS_ALLOWED_KEYS);
                 } catch (Exception e) {
                     // never mind, the column probably already existed
                 }
-            case 9:
+            case 8:
                 // tbale name for user_ids changed to user_packets
                 db.execSQL("DROP TABLE IF EXISTS certs");
                 db.execSQL("DROP TABLE IF EXISTS user_ids");
                 db.execSQL(CREATE_USER_PACKETS);
                 db.execSQL(CREATE_CERTS);
-            case 10:
+            case 9:
                 // do nothing here, just consolidate
-            case 11:
+            case 10:
                 // fix problems in database, see #1402 for details
                 // https://github.com/open-keychain/open-keychain/issues/1402
                 db.execSQL("DELETE FROM api_accounts WHERE key_id BETWEEN 0 AND 3");
-            case 12:
+            case 11:
                 db.execSQL(CREATE_UPDATE_KEYS);
-            case 13:
+            case 12:
                 // do nothing here, just consolidate
-            case 14:
+            case 13:
                 db.execSQL("CREATE INDEX keys_by_rank ON keys (" + KeysColumns.RANK + ");");
                 db.execSQL("CREATE INDEX uids_by_rank ON user_packets (" + UserPacketsColumns.RANK + ", "
                         + UserPacketsColumns.USER_ID + ", " + UserPacketsColumns.MASTER_KEY_ID + ");");
                 db.execSQL("CREATE INDEX verified_certs ON certs ("
                         + CertsColumns.VERIFIED + ", " + CertsColumns.MASTER_KEY_ID + ");");
-            case 15:
+            case 14:
                 db.execSQL("ALTER TABLE user_packets ADD COLUMN name TEXT");
                 db.execSQL("ALTER TABLE user_packets ADD COLUMN email TEXT");
                 db.execSQL("ALTER TABLE user_packets ADD COLUMN comment TEXT");
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
