This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 757580a52ff4357da96d21b9ed5d0382191b2f0c
- Commit message: fix build error
- Diff:
```
commit 757580a52ff4357da96d21b9ed5d0382191b2f0c
Author: Thomas Swift <tswift@u.rochester.edu>
Date:   Sat Jan 17 21:59:07 2015 -0500

    fix build error
---
 src/main/java/com/tswift242/tetris/TetrisPanel.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/src/main/java/com/tswift242/tetris/TetrisPanel.java b/src/main/java/com/tswift242/tetris/TetrisPanel.java
index a621c44..9b36adc 100755
--- a/src/main/java/com/tswift242/tetris/TetrisPanel.java
+++ b/src/main/java/com/tswift242/tetris/TetrisPanel.java
@@ -44,7 +44,7 @@ public class TetrisPanel extends JPanel
 	private static final int INIT_DELAY = 400; //timer delay
 	// TODO: make this value formulaic instead of fixed in the future
 	private static final int SCORE_INCREMENT_VALUE = 100;
-	private static final int HIGH_SCORES_FILENAME = "TetrisHighScores.txt";
+	private static final String HIGH_SCORES_FILENAME = "TetrisHighScores.txt";
 	// maximum number of high scores to save
 	private static final int MAX_HIGH_SCORES = 10;
 	private static final String MUSIC_FILE = "/12-hans_zimmer-time.wav";
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
