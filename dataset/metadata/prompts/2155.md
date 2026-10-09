This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 4b22f1835171516ac4b683c050a2e24f959d8c6c
- Commit message: Online Student Scheduling: Reservations

- fixed an issue taking all the properties (reservation priority, must be used, can assign over limit, allow overlap) from individual reservation
  - this fixes an issue
- Diff:
```
commit 4b22f1835171516ac4b683c050a2e24f959d8c6c
Author: tomas-muller <muller@unitime.org>
Date:   Mon Feb 22 14:48:28 2016 +0100

    Online Student Scheduling: Reservations
    
    - fixed an issue taking all the properties (reservation priority, must be used, can assign over limit, allow overlap) from individual reservation
      - this fixes an issue
---
 .../onlinesectioning/model/XReservation.java       | 24 +++++++++++-----------
 1 file changed, 12 insertions(+), 12 deletions(-)

diff --git a/JavaSource/org/unitime/timetable/onlinesectioning/model/XReservation.java b/JavaSource/org/unitime/timetable/onlinesectioning/model/XReservation.java
index f3111128..2f2ace94 100644
--- a/JavaSource/org/unitime/timetable/onlinesectioning/model/XReservation.java
+++ b/JavaSource/org/unitime/timetable/onlinesectioning/model/XReservation.java
@@ -125,22 +125,22 @@ public abstract class XReservation extends XReservationId implements Comparable<
         	setAllowOverlap(ApplicationProperty.ReservationAllowOverlapIndividual.isTrue());
         	break;
         case Group:
-        	setPriority(ApplicationProperty.ReservationPriorityIndividual.intValue());
-        	setCanAssignOverLimit(ApplicationProperty.ReservationCanOverLimitIndividual.isTrue());
-        	setMustBeUsed(ApplicationProperty.ReservationMustBeUsedIndividual.isTrue());
-        	setAllowOverlap(ApplicationProperty.ReservationAllowOverlapIndividual.isTrue());
+        	setPriority(ApplicationProperty.ReservationPriorityGroup.intValue());
+        	setCanAssignOverLimit(ApplicationProperty.ReservationCanOverLimitGroup.isTrue());
+        	setMustBeUsed(ApplicationProperty.ReservationMustBeUsedGroup.isTrue());
+        	setAllowOverlap(ApplicationProperty.ReservationAllowOverlapGroup.isTrue());
         	break;
         case Curriculum:
-        	setPriority(ApplicationProperty.ReservationPriorityIndividual.intValue());
-        	setCanAssignOverLimit(ApplicationProperty.ReservationCanOverLimitIndividual.isTrue());
-        	setMustBeUsed(ApplicationProperty.ReservationMustBeUsedIndividual.isTrue());
-        	setAllowOverlap(ApplicationProperty.ReservationAllowOverlapIndividual.isTrue());
+        	setPriority(ApplicationProperty.ReservationPriorityCurriculum.intValue());
+        	setCanAssignOverLimit(ApplicationProperty.ReservationCanOverLimitCurriculum.isTrue());
+        	setMustBeUsed(ApplicationProperty.ReservationMustBeUsedCurriculum.isTrue());
+        	setAllowOverlap(ApplicationProperty.ReservationAllowOverlapCurriculum.isTrue());
         	break;
         case Course:
-        	setPriority(ApplicationProperty.ReservationPriorityIndividual.intValue());
-        	setCanAssignOverLimit(ApplicationProperty.ReservationCanOverLimitIndividual.isTrue());
-        	setMustBeUsed(ApplicationProperty.ReservationMustBeUsedIndividual.isTrue());
-        	setAllowOverlap(ApplicationProperty.ReservationAllowOverlapIndividual.isTrue());
+        	setPriority(ApplicationProperty.ReservationPriorityCourse.intValue());
+        	setCanAssignOverLimit(ApplicationProperty.ReservationCanOverLimitCourse.isTrue());
+        	setMustBeUsed(ApplicationProperty.ReservationMustBeUsedCourse.isTrue());
+        	setAllowOverlap(ApplicationProperty.ReservationAllowOverlapCourse.isTrue());
         	break;
         case Override:
         	setPriority(ApplicationProperty.ReservationPriorityOverride.intValue());
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
