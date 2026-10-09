This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 04a68cf8a934f27cd6c59fee3267ff17751bd9db
- Commit message: fix bug where saved SpimDataFilteringAndGrouping was discarded before it could be used by the asynchronous global optimization
- Diff:
```
commit 04a68cf8a934f27cd6c59fee3267ff17751bd9db
Author: David Hörl <hoerldavid@gmail.com>
Date:   Wed Aug 23 17:47:37 2017 +0200

    fix bug where saved SpimDataFilteringAndGrouping was discarded before it could be used by the asynchronous global optimization
---
 src/main/java/gui/StitchingExplorerPanel.java                 | 9 +++++++--
 src/main/java/gui/popup/OptimizeGloballyPopupExpertBatch.java | 9 ++++++++-
 2 files changed, 15 insertions(+), 3 deletions(-)

diff --git a/src/main/java/gui/StitchingExplorerPanel.java b/src/main/java/gui/StitchingExplorerPanel.java
index 80df11b..a0d3eb6 100644
--- a/src/main/java/gui/StitchingExplorerPanel.java
+++ b/src/main/java/gui/StitchingExplorerPanel.java
@@ -228,8 +228,13 @@ public class StitchingExplorerPanel<AS extends AbstractSpimData< ? >, X extends
 				OptimizeGloballyPopupExpertBatch globalOptPopup = (OptimizeGloballyPopupExpertBatch) globalOptPopupOpt.get();
 				globalOptPopup.doClick();
 			}
-			// discard the temp. SpimDataFilteringAndGrouping
-			savedFilteringAndGrouping = null;
+			else
+			{
+				// discard the temp. SpimDataFilteringAndGrouping
+				// if we discard it right now, but want to do global opt (which runs asynchronously)
+				// it would not work. therefore, the global optimization will take care of this
+				savedFilteringAndGrouping = null;
+			}
 		}
 	}
 
diff --git a/src/main/java/gui/popup/OptimizeGloballyPopupExpertBatch.java b/src/main/java/gui/popup/OptimizeGloballyPopupExpertBatch.java
index b7ebfbb..ff479a8 100644
--- a/src/main/java/gui/popup/OptimizeGloballyPopupExpertBatch.java
+++ b/src/main/java/gui/popup/OptimizeGloballyPopupExpertBatch.java
@@ -97,7 +97,8 @@ public class OptimizeGloballyPopupExpertBatch extends JMenuItem
 						return;
 
 					SpimDataFilteringAndGrouping< AbstractSpimData< ? > > filteringAndGrouping;
-					if ( ( (StitchingExplorerPanel< ?, ? >) panel ).getSavedFilteringAndGrouping() == null )
+					final boolean isSavedFaG = ( ( (StitchingExplorerPanel< ?, ? >) panel ).getSavedFilteringAndGrouping() == null );
+					if ( isSavedFaG )
 					{
 						FilteredAndGroupedExplorerPanel< AbstractSpimData< ? >, ? > panelFG = (FilteredAndGroupedExplorerPanel< AbstractSpimData< ? >, ? >) panel;
 						filteringAndGrouping = new SpimDataFilteringAndGrouping< AbstractSpimData< ? > >(
@@ -279,6 +280,12 @@ public class OptimizeGloballyPopupExpertBatch extends JMenuItem
 
 					}
 
+					if (isSavedFaG)
+					{
+						// remove saved filtering and grouping once we are done here
+						( (StitchingExplorerPanel< ?, ? >) panel ).setSavedFilteringAndGrouping( null );
+					}
+
 					panel.bdvPopup().updateBDV();
 
 				}
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
