This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 9e0625d8d0827221dea0a9f6114ad8376ccc76b1
- Commit message: fixing a bug
- Diff:
```
commit 9e0625d8d0827221dea0a9f6114ad8376ccc76b1
Author: Julien Chastang <julien.c.chastang@gmail.com>
Date:   Thu Oct 18 15:23:45 2012 -0600

    fixing a bug
---
 .../unidata/idv/control/DisplayControlImpl.java    | 36 ++++++++++++----------
 1 file changed, 20 insertions(+), 16 deletions(-)

diff --git a/src/ucar/unidata/idv/control/DisplayControlImpl.java b/src/ucar/unidata/idv/control/DisplayControlImpl.java
index 7ffcabb77..6148ad531 100644
--- a/src/ucar/unidata/idv/control/DisplayControlImpl.java
+++ b/src/ucar/unidata/idv/control/DisplayControlImpl.java
@@ -1136,28 +1136,32 @@ public abstract class DisplayControlImpl extends DisplayControlBase implements D
             return;
         }
 
-        if ((myDataChoices.size() > 0)
-                && (myDataChoices.get(0) instanceof DerivedDataChoice)) {
-            List cdcs =
-                ((DerivedDataChoice) myDataChoices.get(0)).getChoices();
-            if (cdcs.size() > 0) {
-                DataChoice    dc = (DataChoice) cdcs.get(0);
-                DataSelection ds = dc.getDataSelection();
-                if (ds != null) {
-                    List   dtimes = ds.getTimeDriverTimes();
-                    Object ud1    =
-                        ds.getProperty(DataSelection.PROP_USESTIMEDRIVER);
-                    //if ((dtimes != null) && (dtimes.size() > 0)
-                    //        && (ud1 != null)) {
-                    if (ud1 != null) {
-                        this.usesTimeDriver = ((Boolean) ud1).booleanValue();
+        if (myDataChoices != null) {
+            if ((myDataChoices.size() > 0)
+                    && (myDataChoices.get(0) instanceof DerivedDataChoice)) {
+                List cdcs =
+                    ((DerivedDataChoice) myDataChoices.get(0)).getChoices();
+                if (cdcs.size() > 0) {
+                    DataChoice    dc = (DataChoice) cdcs.get(0);
+                    DataSelection ds = dc.getDataSelection();
+                    if (ds != null) {
+                        List   dtimes = ds.getTimeDriverTimes();
+                        Object ud1    =
+                            ds.getProperty(DataSelection.PROP_USESTIMEDRIVER);
+                        //if ((dtimes != null) && (dtimes.size() > 0)
+                        //        && (ud1 != null)) {
+                        if (ud1 != null) {
+                            this.usesTimeDriver =
+                                ((Boolean) ud1).booleanValue();
+                        }
+                        //}
                     }
-                    //}
                 }
             }
         }
 
 
+
         //Check if we have been removed
         if (hasBeenRemoved) {
             return;
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
