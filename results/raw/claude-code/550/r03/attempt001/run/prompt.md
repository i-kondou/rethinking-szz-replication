This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 94af9270313a940dfe4d9b0f9d9e6b1856cc1cdf
- Commit message: Instructor Detail: Class Assignments

- fixed an ArrayIndexOutOfBoundsException thrown when the instructor is assigned to one or more classes, but there is no committed timetable yet
- this fixes issue #27
- Diff:
```
commit 94af9270313a940dfe4d9b0f9d9e6b1856cc1cdf
Author: tomas-muller <muller@unitime.org>
Date:   Wed Mar 1 15:22:31 2017 +0100

    Instructor Detail: Class Assignments
    
    - fixed an ArrayIndexOutOfBoundsException thrown when the instructor is assigned to one or more classes, but there is no committed timetable yet
    - this fixes issue #27
---
 JavaSource/org/unitime/timetable/action/InstructorDetailAction.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/JavaSource/org/unitime/timetable/action/InstructorDetailAction.java b/JavaSource/org/unitime/timetable/action/InstructorDetailAction.java
index 49fbecdf3..54ecbf884 100644
--- a/JavaSource/org/unitime/timetable/action/InstructorDetailAction.java
+++ b/JavaSource/org/unitime/timetable/action/InstructorDetailAction.java
@@ -253,7 +253,7 @@ public class InstructorDetailAction extends PreferencesAction {
 		    					null,
 		    					new String[] {MSG.columnClass(), MSG.columnInstructorCheckConflicts(), MSG.columnInstructorShare(), MSG.columnTeachingResponsibility(),
 		    							MSG.columnLimit(), MSG.columnManager()},
-		    					new String[] {"left", "left","left", "left", "left"},
+		    					new String[] {"left", "left","left", "left", "left", "left"},
 		    					null )
 			    	);
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
