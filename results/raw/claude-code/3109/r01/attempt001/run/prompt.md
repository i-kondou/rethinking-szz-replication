This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 395d7ef9ff15d70632f75e4eb4816680e612f9e1
- Commit message: HQL Reports: Export CSV

- fixed ability to export HQL report as CSV when the query contains a signle-choice parameter (like SUBJECT or DEPARTMENT)
- Diff:
```
commit 395d7ef9ff15d70632f75e4eb4816680e612f9e1
Author: tomas-muller <muller@unitime.org>
Date:   Fri Sep 21 13:06:59 2018 +0200

    HQL Reports: Export CSV
    
    - fixed ability to export HQL report as CSV when the query contains a signle-choice parameter (like SUBJECT or DEPARTMENT)
---
 .../timetable/export/hql/SavedHqlExportToCSV.java    | 20 +++++++++++---------
 1 file changed, 11 insertions(+), 9 deletions(-)

diff --git a/JavaSource/org/unitime/timetable/export/hql/SavedHqlExportToCSV.java b/JavaSource/org/unitime/timetable/export/hql/SavedHqlExportToCSV.java
index 2f093afe5..857ee9502 100644
--- a/JavaSource/org/unitime/timetable/export/hql/SavedHqlExportToCSV.java
+++ b/JavaSource/org/unitime/timetable/export/hql/SavedHqlExportToCSV.java
@@ -136,16 +136,18 @@ public class SavedHqlExportToCSV implements Exporter {
 				}
 			} else {
 				String value = helper.getParameter(option.name());
-				SavedHQLInterface.IdValue v = new SavedHQLInterface.IdValue();
-				v.setValue(option.name());
-				Long id = option.lookupValue(context.getUser(), value);
-				if (id == null) {
-					try {
-						id = Long.valueOf(value);
-					} catch (NumberFormatException e) {}
+				if (value != null) {
+					SavedHQLInterface.IdValue v = new SavedHQLInterface.IdValue();
+					v.setValue(option.name());
+					Long id = option.lookupValue(context.getUser(), value);
+					if (id == null) {
+						try {
+							id = Long.valueOf(value);
+						} catch (NumberFormatException e) {}
+					}
+					v.setText(id == null ? "" : id.toString());
+					params.add(v);
 				}
-				v.setText(id == null ? "" : id.toString());
-				params.add(v);
 			}
 		}
 		for (SavedHQLParameter p: hql.getParameters()) {
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
