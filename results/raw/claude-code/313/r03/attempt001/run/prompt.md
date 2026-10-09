This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 6a2dd27d7b12117f21ad7b9fd3f42327958ba1bc
- Commit message: Alarms: small refactoring

this fixes issue
- Diff:
```
commit 6a2dd27d7b12117f21ad7b9fd3f42327958ba1bc
Author: Yuriy Kulikov <yuriy.kulikov.87@googlemail.com>
Date:   Sat Aug 4 21:06:53 2012 +0200

    Alarms: small refactoring
    
    this fixes issue
---
 src/com/better/alarm/model/Alarms.java | 71 +++++++++++++++-------------------
 1 file changed, 32 insertions(+), 39 deletions(-)

diff --git a/src/com/better/alarm/model/Alarms.java b/src/com/better/alarm/model/Alarms.java
index c55e804..a90f26f 100644
--- a/src/com/better/alarm/model/Alarms.java
+++ b/src/com/better/alarm/model/Alarms.java
@@ -80,12 +80,26 @@ public class Alarms implements IAlarmsManager {
         for (Alarm alarm : set) {
             boolean isExpired = alarm.getNextTimeInMillis() < now;
             if (isExpired && !alarm.isEnabled()) {
-                enable(alarm.getId(), false);
+                alarm.setEnabled(false);
+                writeToDb(alarm.getId());
             }
         }
         setNextAlert();
     }
 
+    private void writeToDb(int id) {
+        ContentValues values = getAlarm(id).createContentValues();
+        Uri uriWithAppendedId = ContentUris.withAppendedId(Alarm.Columns.CONTENT_URI, id);
+        mContentResolver.update(uriWithAppendedId, values, null, null);
+    }
+
+    private void deleteAlarm(int alarmId) {
+        Alarm alarm = getAlarm(alarmId);
+        set.remove(alarm);
+        Uri uri = ContentUris.withAppendedId(Alarm.Columns.CONTENT_URI, alarmId);
+        mContentResolver.delete(uri, "", null);
+    }
+
     @Override
     public int createNewAlarm() {
         Alarm alarm = new Alarm();
@@ -109,19 +123,16 @@ public class Alarms implements IAlarmsManager {
         alarm.setLabel(label);
         alarm.setAlert(alert);
         alarm.setPrealarm(preAlarm);
-        changeAlarm(alarm);
+        writeToDb(alarm.getId());
+        setNextAlert();
+        notifyAlarmListChangedListeners();
     }
 
     @Override
     public void delete(int alarmId) {
-        Alarm alarm = getAlarm(alarmId);
-        set.remove(alarm);
-        Uri uri = ContentUris.withAppendedId(Alarm.Columns.CONTENT_URI, alarmId);
-        mContentResolver.delete(uri, "", null);
-
+        deleteAlarm(alarmId);
         broadcastAlarmState(alarmId, Intents.ALARM_DISMISS_ACTION);
         notifyAlarmListChangedListeners();
-
         setNextAlert();
     }
 
@@ -139,7 +150,9 @@ public class Alarms implements IAlarmsManager {
         if (!alarm.getDaysOfWeek().isRepeatSet()) {
             alarm.setEnabled(false);
         }
-        changeAlarm(alarm);
+        writeToDb(alarm.getId());
+        setNextAlert();
+        notifyAlarmListChangedListeners();
     }
 
     void onAlarmSnoozedFired(int id) {
@@ -161,32 +174,6 @@ public class Alarms implements IAlarmsManager {
         return null;
     }
 
-    private int changeAlarm(Alarm alarm) {
-        // first add to the DB
-        ContentValues values = alarm.createContentValues();
-
-        // this is an existing alarm
-        mContentResolver.update(ContentUris.withAppendedId(Alarm.Columns.CONTENT_URI, alarm.getId()), values, null,
-                null);
-        set.remove(alarm);
-        set.add(alarm);
-
-        if (alarm.isEnabled()) {
-            // Disable the snooze if we just changed the snoozed alarm. This
-            // only does work if the snoozed alarm is the same as the given
-            // alarm.
-            // TODO: disableSnoozeAlert should have a better name.
-
-            // Disable the snooze if this alarm fires before the snoozed alarm.
-            // This works on every alarm since the user most likely intends to
-            // have the modified alarm fire next.
-            // clearSnoozeIfNeeded(timeInMillis);
-        }
-        setNextAlert();
-        notifyAlarmListChangedListeners();
-        return alarm.getId();
-    }
-
     /**
      * A convenience method to enable or disable an alarm.
      * 
@@ -199,7 +186,9 @@ public class Alarms implements IAlarmsManager {
     public void enable(int id, boolean enable) {
         Alarm alarm = getAlarm(id);
         alarm.setEnabled(enable);
-        changeAlarm(alarm);
+        writeToDb(alarm.getId());
+        setNextAlert();
+        notifyAlarmListChangedListeners();
     }
 
     @Override
@@ -212,14 +201,18 @@ public class Alarms implements IAlarmsManager {
         alarm.setSnoozedHour(calendar.get(Calendar.HOUR_OF_DAY));
         alarm.setSnoozedminutes(calendar.get(Calendar.MINUTE));
         broadcastAlarmState(alarm.getId(), Intents.ALARM_SNOOZE_ACTION);
-        changeAlarm(alarm);
+        writeToDb(alarm.getId());
+        setNextAlert();
+        notifyAlarmListChangedListeners();
     }
 
     @Override
     public void dismiss(Alarm alarm) {
         broadcastAlarmState(alarm.getId(), Intents.ALARM_DISMISS_ACTION);
         alarm.setSnoozed(false);
-        changeAlarm(alarm);
+        writeToDb(alarm.getId());
+        setNextAlert();
+        notifyAlarmListChangedListeners();
     }
 
     private Alarm calculateNextAlert() {
@@ -244,7 +237,7 @@ public class Alarms implements IAlarmsManager {
      * changes alarm settings. Activates snooze if set, otherwise loads all
      * alarms, activates next alert.
      */
-    void setNextAlert() {
+    private void setNextAlert() {
         final Alarm alarm = calculateNextAlert();
         if (alarm != null) {
             long timeInMillis = alarm.isSnoozed() ? alarm.getSnoozedTimeInMillis() : alarm.getTimeInMillis();
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
