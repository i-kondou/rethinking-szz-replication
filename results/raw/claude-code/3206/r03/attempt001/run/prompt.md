This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 46eeb00df531767ad44c996a57af576468ab9c3f
- Commit message: Batch Student Scheduling: Section Names

- fill in the course-dependent section name only when it is set (not null)
- this fixes an issue with the passivation / XML export (adding text to an XML document must not be null)
- Diff:
```
commit 46eeb00df531767ad44c996a57af576468ab9c3f
Author: tomas-muller <muller@unitime.org>
Date:   Tue Jul 18 17:36:17 2017 +0200

    Batch Student Scheduling: Section Names
    
    - fill in the course-dependent section name only when it is set (not null)
    - this fixes an issue with the passivation / XML export (adding text to an XML document must not be null)
---
 .../solver/studentsct/StudentSectioningDatabaseLoader.java         | 7 +++++--
 1 file changed, 5 insertions(+), 2 deletions(-)

diff --git a/JavaSource/org/unitime/timetable/solver/studentsct/StudentSectioningDatabaseLoader.java b/JavaSource/org/unitime/timetable/solver/studentsct/StudentSectioningDatabaseLoader.java
index 1a4adc738..98a5641b8 100644
--- a/JavaSource/org/unitime/timetable/solver/studentsct/StudentSectioningDatabaseLoader.java
+++ b/JavaSource/org/unitime/timetable/solver/studentsct/StudentSectioningDatabaseLoader.java
@@ -458,8 +458,11 @@ public class StudentSectioningDatabaseLoader extends StudentSectioningLoader {
                     if (iCheckEnabledForScheduling && !c.isEnabledForStudentScheduling()) limit = 0;
                     Section section = new Section(c.getUniqueId().longValue(), limit, (c.getExternalUniqueId() == null ? c.getClassSuffix() == null ? c.getSectionNumberString() : c.getClassSuffix() : c.getExternalUniqueId()), subpart, p,
                     		getInstructors(c), parentSection);
-                    for (CourseOffering course: io.getCourseOfferings())
-                    	section.setName(course.getUniqueId(), c.getClassSuffix(course));
+                    for (CourseOffering course: io.getCourseOfferings()) {
+                    	String suffix = c.getClassSuffix(course);
+                    	if (suffix != null)
+                    		section.setName(course.getUniqueId(), suffix);
+                    }
                     section.setCancelled(c.isCancelled());
                     class2section.put(c.getUniqueId(), section);
                     classTable.put(c.getUniqueId(), section);
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
