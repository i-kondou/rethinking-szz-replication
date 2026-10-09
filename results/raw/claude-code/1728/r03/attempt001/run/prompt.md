This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 153acab91e5c096399e0302dbc7ea91293281536
- Commit message: Dispose of DownloadManagerInterface in onDestroy.

This fixes a bug.
- Diff:
```
commit 153acab91e5c096399e0302dbc7ea91293281536
Author: Barend Garvelink <bgarvelink@xebia.com>
Date:   Sun Oct 23 11:36:54 2016 +0200

    Dispose of DownloadManagerInterface in onDestroy.
    
    This fixes a bug.
---
 .../src/main/java/nl/sebastiaanschool/contact/app/MainActivity.java | 6 ++++++
 .../contact/app/data/downloadmanager/DownloadManagerInterface.java  | 5 +++++
 2 files changed, 11 insertions(+)

diff --git a/Sebastiaanschool/src/main/java/nl/sebastiaanschool/contact/app/MainActivity.java b/Sebastiaanschool/src/main/java/nl/sebastiaanschool/contact/app/MainActivity.java
index 66df028..6310e86 100644
--- a/Sebastiaanschool/src/main/java/nl/sebastiaanschool/contact/app/MainActivity.java
+++ b/Sebastiaanschool/src/main/java/nl/sebastiaanschool/contact/app/MainActivity.java
@@ -62,6 +62,12 @@ public class MainActivity extends AppCompatActivity {
         }
     }
 
+    @Override
+    protected void onDestroy() {
+        super.onDestroy();
+        DownloadManagerInterface.getInstance().destroy(this);
+    }
+
     private void initializeStrictMode() {
         if (BuildConfig.DEBUG) {
             StrictMode.setThreadPolicy(new StrictMode.ThreadPolicy.Builder()
diff --git a/Sebastiaanschool/src/main/java/nl/sebastiaanschool/contact/app/data/downloadmanager/DownloadManagerInterface.java b/Sebastiaanschool/src/main/java/nl/sebastiaanschool/contact/app/data/downloadmanager/DownloadManagerInterface.java
index 57c350f..fcf09e2 100644
--- a/Sebastiaanschool/src/main/java/nl/sebastiaanschool/contact/app/data/downloadmanager/DownloadManagerInterface.java
+++ b/Sebastiaanschool/src/main/java/nl/sebastiaanschool/contact/app/data/downloadmanager/DownloadManagerInterface.java
@@ -63,6 +63,11 @@ public class DownloadManagerInterface {
         context.registerReceiver(downloadCompletionReceiver, filter);
     }
 
+    public void destroy(Context context) {
+        context.unregisterReceiver(downloadCompletionReceiver);
+        instance = null;
+    }
+
     /**
      * Returns a hot observable that emits status updates for downloaded files.
      * @return download observable.
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
