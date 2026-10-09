This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: adae741e66f8236bcd7e7b933f2451c8f94ce86b
- Commit message: 
- Diff:
```
commit adae741e66f8236bcd7e7b933f2451c8f94ce86b
Author: Eden33 <eduard.gopp@gmail.com>
Date:   Sat Jan 18 09:39:39 2014 +0100
---
 .../src/at/fhv/audioracer/simulator/gui/StartUpView.java               | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)

diff --git a/AudioRacer-PlayerSimulator/src/at/fhv/audioracer/simulator/gui/StartUpView.java b/AudioRacer-PlayerSimulator/src/at/fhv/audioracer/simulator/gui/StartUpView.java
index 7026249..c2479a8 100644
--- a/AudioRacer-PlayerSimulator/src/at/fhv/audioracer/simulator/gui/StartUpView.java
+++ b/AudioRacer-PlayerSimulator/src/at/fhv/audioracer/simulator/gui/StartUpView.java
@@ -18,6 +18,7 @@ import javax.swing.event.ListSelectionListener;
 import at.fhv.audioracer.client.player.IPlayerClientListener;
 import at.fhv.audioracer.client.player.PlayerClient;
 import at.fhv.audioracer.core.model.Player;
+import at.fhv.audioracer.core.util.Position;
 
 @SuppressWarnings("serial")
 public class StartUpView extends JFrame {
@@ -101,7 +102,7 @@ public class StartUpView extends JFrame {
 			}
 			
 			@Override
-			public void onUpdateCheckpointDirection() {
+			public void onUpdateCheckpointDirection(Position pos) {
 				// TODO Auto-generated method stub
 				
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
