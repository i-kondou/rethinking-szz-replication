This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: b1c9edc398212a441cbee9a4bbb047a88f7fa8be
- Commit message: Add mp3 support - fix bug.
- Diff:
```
commit b1c9edc398212a441cbee9a4bbb047a88f7fa8be
Author: DanVanAtta <dhvatta@gmail.com>
Date:   Fri Jan 1 15:21:18 2016 -0800

    Add mp3 support - fix bug.
---
 src/games/strategy/triplea/TripleAPlayer.java | 12 +++++++++---
 1 file changed, 9 insertions(+), 3 deletions(-)

diff --git a/src/games/strategy/triplea/TripleAPlayer.java b/src/games/strategy/triplea/TripleAPlayer.java
index 01443c98b..bceb3ed93 100644
--- a/src/games/strategy/triplea/TripleAPlayer.java
+++ b/src/games/strategy/triplea/TripleAPlayer.java
@@ -25,7 +25,6 @@ import games.strategy.engine.data.Unit;
 import games.strategy.engine.gamePlayer.IGamePlayer;
 import games.strategy.net.GUID;
 import games.strategy.sound.ClipPlayer;
-import games.strategy.sound.DefaultSoundChannel;
 import games.strategy.sound.SoundPath;
 import games.strategy.triplea.attatchments.PlayerAttachment;
 import games.strategy.triplea.attatchments.PoliticalActionAttachment;
@@ -66,7 +65,7 @@ import games.strategy.util.Tuple;
  * It should be using a Change done in a delegate, and done through an IDelegate, which we get through
  * getPlayerBridge().getRemote()
  */
-public class TripleAPlayer extends AbstractHumanPlayer<TripleAFrame>implements IGamePlayer, ITripleaPlayer {
+public class TripleAPlayer extends AbstractHumanPlayer<TripleAFrame> implements IGamePlayer, ITripleaPlayer {
   private boolean m_soundPlayedAlreadyCombatMove = false;
   private boolean m_soundPlayedAlreadyNonCombatMove = false;
   private boolean m_soundPlayedAlreadyPurchase = false;
@@ -307,10 +306,17 @@ public class TripleAPlayer extends AbstractHumanPlayer<TripleAFrame>implements I
     }
 
     final PlayerID id = getPlayerID();
-    if ((nonCombat && !m_soundPlayedAlreadyNonCombatMove) || (!nonCombat && !m_soundPlayedAlreadyCombatMove)) {
+
+    if (nonCombat && !m_soundPlayedAlreadyNonCombatMove) {
       ClipPlayer.play(SoundPath.CLIP_PHASE_MOVE_NONCOMBAT, id);
       m_soundPlayedAlreadyNonCombatMove = true;
     }
+
+    if (!nonCombat && !m_soundPlayedAlreadyCombatMove) {
+      ClipPlayer.play(SoundPath.CLIP_PHASE_MOVE_NONCOMBAT, id);
+      m_soundPlayedAlreadyCombatMove = true;
+    }
+
     final MoveDescription moveDescription = m_ui.getMove(id, getPlayerBridge(), nonCombat, stepName);
     if (moveDescription == null) {
       if (GameStepPropertiesHelper.isRemoveAirThatCanNotLand(getGameData())) {
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
