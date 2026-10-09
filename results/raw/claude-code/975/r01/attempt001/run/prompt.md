This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 522101e32778b0f66dbfaeb6d6b5d38df50954f7
- Commit message: Event Management: Create Course-related Event Bugfix

- fixed a Null exception when creating a course-related event
- this fixed a problem (CourseRelatedEvent.getSession() throws a null because the event is not fully created yet)
- Diff:
```
commit 522101e32778b0f66dbfaeb6d6b5d38df50954f7
Author: tomas-muller <muller@unitime.org>
Date:   Mon Jul 9 13:41:15 2018 +0200

    Event Management: Create Course-related Event Bugfix
    
    - fixed a Null exception when creating a course-related event
    - this fixed a problem (CourseRelatedEvent.getSession() throws a null because the event is not fully created yet)
---
 JavaSource/org/unitime/timetable/model/CourseEvent.java | 1 +
 1 file changed, 1 insertion(+)

diff --git a/JavaSource/org/unitime/timetable/model/CourseEvent.java b/JavaSource/org/unitime/timetable/model/CourseEvent.java
index 37ae9e2e4..87c8fe676 100644
--- a/JavaSource/org/unitime/timetable/model/CourseEvent.java
+++ b/JavaSource/org/unitime/timetable/model/CourseEvent.java
@@ -83,6 +83,7 @@ public class CourseEvent extends BaseCourseEvent {
 	}
 	
 	public Session getSession() {
+		if (getRelatedCourses() == null) return null;
 		for (RelatedCourseInfo rc: getRelatedCourses())
 			return rc.getCourse().getInstructionalOffering().getSession();
 		return null;
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
