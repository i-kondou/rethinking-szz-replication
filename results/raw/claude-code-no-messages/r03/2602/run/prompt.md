This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: ea146d3bbb9b6eb582e9f5c1e6969f9382c703c3
- Commit message: 
- Diff:
```
commit ea146d3bbb9b6eb582e9f5c1e6969f9382c703c3
Author: crykn <crykn@users.noreply.github.com>
Date:   Wed Aug 15 14:58:31 2018 +0100
---
 core/src/de/gg/event/AllPlayersReadyEvent.java     | 21 +++++
 core/src/de/gg/event/NextRoundEvent.java           |  9 ---
 .../src/de/gg/event/RoundEndDataReceivedEvent.java | 20 -----
 core/src/de/gg/event/ServerReadyEvent.java         | 12 +++
 core/src/de/gg/game/AuthoritativeSession.java      | 12 +--
 core/src/de/gg/game/GameSession.java               | 89 +++++++++++-----------
 core/src/de/gg/game/SlaveSession.java              | 18 ++---
 core/src/de/gg/game/data/RoundEndData.java         | 34 ---------
 core/src/de/gg/game/system/smp/RoundEndSystem.java |  1 +
 core/src/de/gg/network/GameServer.java             | 10 +++
 core/src/de/gg/network/NetworkRegisterer.java      |  4 -
 .../network/rmi/AuthoritativeResultListener.java   | 10 +--
 .../rmi/ServerAuthoritativResultListenerStub.java  |  5 +-
 core/src/de/gg/screen/BaseGameScreen.java          |  7 +-
 core/src/de/gg/screen/GameLoadingScreen.java       | 11 ++-
 core/src/de/gg/screen/GameRoundendScreen.java      | 64 ++++++++--------
 core/src/de/gg/screen/SettingsScreen.java          |  7 +-
 core/src/de/gg/util/TickCounter.java               |  5 +-
 18 files changed, 151 insertions(+), 188 deletions(-)

diff --git a/core/src/de/gg/event/AllPlayersReadyEvent.java b/core/src/de/gg/event/AllPlayersReadyEvent.java
new file mode 100644
index 0000000..e5923d6
--- /dev/null
+++ b/core/src/de/gg/event/AllPlayersReadyEvent.java
@@ -0,0 +1,21 @@
+package de.gg.event;
+
+/**
+ * Posted when all players readied up and the screen should change.
+ */
+public class AllPlayersReadyEvent {
+
+	private boolean nextRound;
+
+	public AllPlayersReadyEvent(boolean nextRound) {
+		this.nextRound = nextRound;
+	}
+
+	/**
+	 * @return whether this event also marks the beginning of a new round.
+	 */
+	public boolean isNextRound() {
+		return nextRound;
+	}
+
+}
diff --git a/core/src/de/gg/event/NextRoundEvent.java b/core/src/de/gg/event/NextRoundEvent.java
deleted file mode 100644
index 54b9437..0000000
--- a/core/src/de/gg/event/NextRoundEvent.java
+++ /dev/null
@@ -1,9 +0,0 @@
-package de.gg.event;
-
-/**
- * Posted when the next round starts (because all other players readied up) and
- * the screen should change.
- */
-public class NextRoundEvent {
-
-}
diff --git a/core/src/de/gg/event/RoundEndDataReceivedEvent.java b/core/src/de/gg/event/RoundEndDataReceivedEvent.java
deleted file mode 100644
index 1321f4a..0000000
--- a/core/src/de/gg/event/RoundEndDataReceivedEvent.java
+++ /dev/null
@@ -1,20 +0,0 @@
-package de.gg.event;
-
-import de.gg.game.data.RoundEndData;
-
-/**
- * Posted after a the client received the round end data by the server.
- */
-public class RoundEndDataReceivedEvent {
-
-	private RoundEndData data;
-
-	public RoundEndDataReceivedEvent(RoundEndData data) {
-		this.data = data;
-	}
-
-	public RoundEndData getData() {
-		return data;
-	}
-
-}
diff --git a/core/src/de/gg/event/ServerReadyEvent.java b/core/src/de/gg/event/ServerReadyEvent.java
new file mode 100644
index 0000000..9829560
--- /dev/null
+++ b/core/src/de/gg/event/ServerReadyEvent.java
@@ -0,0 +1,12 @@
+package de.gg.event;
+
+import de.gg.network.rmi.AuthoritativeResultListener;
+
+/**
+ * Posted after a the client is informed that the server is ready.
+ * 
+ * @see AuthoritativeResultListener#onServerReady()
+ */
+public class ServerReadyEvent {
+
+}
diff --git a/core/src/de/gg/game/AuthoritativeSession.java b/core/src/de/gg/game/AuthoritativeSession.java
index f58ca24..6d4e676 100644
--- a/core/src/de/gg/game/AuthoritativeSession.java
+++ b/core/src/de/gg/game/AuthoritativeSession.java
@@ -17,7 +17,6 @@ import com.google.gson.JsonSyntaxException;
 
 import de.gg.game.data.GameSessionSetup;
 import de.gg.game.data.GameSpeed;
-import de.gg.game.data.RoundEndData;
 import de.gg.game.data.vote.VoteResults;
 import de.gg.game.entity.Character;
 import de.gg.game.entity.Player;
@@ -42,7 +41,6 @@ import de.gg.network.rmi.SlaveActionListener;
 import de.gg.util.CollectionUtils;
 import de.gg.util.Log;
 import de.gg.util.PlayerUtils;
-import de.gg.util.RandomUtils;
 import de.gg.util.json.SaveGameParser;
 
 /**
@@ -153,17 +151,10 @@ public class AuthoritativeSession extends GameSession
 	}
 
 	public void onRoundEnd() {
-		// RoundEndData generieren
-		RoundEndData data = new RoundEndData();
-		data.setOpeningHourNextDay(RandomUtils.getRandomNumber(6, 9));
-
 		Log.debug("Server", "Runde zu Ende");
 
 		// Inform the clients
-		resultListenerStub.onRoundEnd(data);
-
-		// Process the last round
-		super.processRoundEnd(data);
+		resultListenerStub.onServerReady();
 
 		// Save automatically on the round end
 		// saveGame();
@@ -284,7 +275,6 @@ public class AuthoritativeSession extends GameSession
 
 		// Save the systems states
 		for (ProcessingSystem<Character> c : characterSystems) {
-
 			save.processingSystemStates.put(c.getClass().getSimpleName(),
 					((ServerProcessingSystem<Character>) c).getSaveState());
 		}
diff --git a/core/src/de/gg/game/GameSession.java b/core/src/de/gg/game/GameSession.java
index 801c266..5fe0c81 100644
--- a/core/src/de/gg/game/GameSession.java
+++ b/core/src/de/gg/game/GameSession.java
@@ -9,7 +9,6 @@ import com.google.common.base.Stopwatch;
 import de.gg.game.data.GameDifficulty;
 import de.gg.game.data.GameSessionSetup;
 import de.gg.game.data.GameSpeed;
-import de.gg.game.data.RoundEndData;
 import de.gg.game.data.vote.VoteResults;
 import de.gg.game.entity.Character;
 import de.gg.game.entity.Player;
@@ -32,15 +31,13 @@ import de.gg.util.TickCounter.TickHandler;
  * <p>
  * Following are the different phases a game session can be in:
  * <ul>
- * <li>{@link #init(SavedGame))}: Initializes the game session, has to get
- * called before the first {@link #update()}-call</li>
+ * <li>{@link #init(SavedGame)}: Initializes the game session, has to get called
+ * before the first {@link #update()}-call</li>
  * <li>{@link #update()}: Processes the current round; has to get called
  * continually; returns <code>true</code> <i>once</i> when the current round is
  * over</li>
- * <li>{@link #processRoundEnd(RoundEndData)}: Has to get called by the child
- * classes to set up the next round after a round ended</li>
- * <li>{@link #startNextRound()}: Has to get called (internally) after
- * {@link #processRoundEnd(RoundEndData)} to start the next round</li>
+ * <li>{@link #startNextRound()}: Has to get called (internally) to start the
+ * next round</li>
  * <li>{@link #finishCurrentVote(VoteResults)}: If there are any votes to hold
  * after {@link #startNextRound()} has been called, this method has to get
  * called to inform the session about its results</li>
@@ -52,7 +49,7 @@ public abstract class GameSession {
 	static final int ROUND_DURATION_IN_SECONDS = 35; // 8*60
 	protected static final int TICKS_PER_SECOND = 10;
 
-	private static final int TICKS_PER_ROUND = ROUND_DURATION_IN_SECONDS
+	protected static final int TICKS_PER_ROUND = ROUND_DURATION_IN_SECONDS
 			* TICKS_PER_SECOND;
 	private static final int TICK_DURATION = 1000
 			* GameSpeed.NORMAL.getDeltaTimeMultiplied() / TICKS_PER_SECOND;
@@ -167,7 +164,11 @@ public abstract class GameSession {
 
 		if (!holdVote) {
 			// NORMAL UPDATE CYCLE
-			return tickCounter.update();
+			if (tickCounter.update()) {
+				processRoundEnd();
+				return true;
+			}
+			return false;
 		} else {
 			// PROCESS VOTES
 			if (matterToVoteOn == null) {
@@ -192,6 +193,28 @@ public abstract class GameSession {
 		}
 	}
 
+	private void processRoundEnd() {
+		logTimer.reset().start();
+		// Character
+		for (Entry<Short, Character> e : city.getCharacters().entrySet()) {
+			roundEndSystem.processCharacter(e.getKey(), e.getValue());
+		}
+
+		// Player
+		for (Entry<Short, Player> e : city.getPlayers().entrySet()) {
+			roundEndSystem.processPlayer(e.getKey(), e.getValue());
+		}
+
+		// Position
+		for (Entry<PositionType, Position> e : city.getPositions().entrySet()) {
+			roundEndSystem.processPosition(e.getKey(), e.getValue());
+		}
+
+		Log.info(localNetworkId == -1 ? "Server" : "Client",
+				"RoundEndSystem in %d ms verarbeitet",
+				logTimer.elapsed(Log.DEFAULT_TIME_UNIT));
+	}
+
 	/**
 	 * This is used to process the game. It is called ten times per second if
 	 * the game is running on {@linkplain GameSpeed#NORMAL normal speed}.
@@ -213,7 +236,6 @@ public abstract class GameSession {
 								sys.getClass().getSimpleName(),
 								logTimer.elapsed(Log.DEFAULT_TIME_UNIT));
 
-						// if (!sys.isProcessedContinuously())
 						sys.setAsProcessed(true);
 					}
 				}
@@ -232,7 +254,6 @@ public abstract class GameSession {
 								sys.getClass().getSimpleName(),
 								logTimer.elapsed(Log.DEFAULT_TIME_UNIT));
 
-						// (!sys.isProcessedContinuously())
 						sys.setAsProcessed(true);
 					}
 				}
@@ -240,45 +261,18 @@ public abstract class GameSession {
 		}
 	}
 
-	/**
-	 * Called after a round ended to setup the next round.
-	 * 
-	 * @param data
-	 *            The relevant round end data.
-	 */
-	protected void processRoundEnd(RoundEndData data) {
-		logTimer.reset().start();
-		// Character
-		for (Entry<Short, Character> e : city.getCharacters().entrySet()) {
-			roundEndSystem.processCharacter(e.getKey(), e.getValue());
-		}
-
-		// Player
-		for (Entry<Short, Player> e : city.getPlayers().entrySet()) {
-			roundEndSystem.processPlayer(e.getKey(), e.getValue());
-		}
-
-		// Position
-		for (Entry<PositionType, Position> e : city.getPositions().entrySet()) {
-			roundEndSystem.processPosition(e.getKey(), e.getValue());
-		}
-
-		Log.info(localNetworkId == -1 ? "Server" : "Client",
-				"RoundEndSystem in %d ms verarbeitet",
-				logTimer.elapsed(Log.DEFAULT_TIME_UNIT));
-	}
-
 	/**
 	 * Called after a round ended to start the next round. If there are any
 	 * {@linkplain City#getMattersToHoldVoteOn() matters to hold a vote on}
 	 * those are done first.
 	 */
 	protected synchronized void startNextRound() {
-		Log.debug(localNetworkId == -1 ? "Server" : "Client",
-				"Runde %s zuende; %s Ticks verarbeitet", currentRound,
-				tickCounter.getTickCount());
 		currentRound++;
 
+		Log.debug(localNetworkId == -1 ? "Server" : "Client",
+				"Runde %s gestartet; Letzte Runde wurden %s Ticks gezählt",
+				currentRound, tickCounter.getTickCount());
+
 		// Reset the tick counter
 		tickCounter.reset();
 
@@ -293,7 +287,8 @@ public abstract class GameSession {
 		}
 
 		// Take care of votes
-		Log.info("Client", "Es stehen %d Tagesordnunspunkte an",
+		Log.info(localNetworkId == -1 ? "Server" : "Client",
+				"Es stehen %d Tagesordnunspunkte an",
 				city.getMattersToHoldVoteOn().size());
 		holdVote = !city.getMattersToHoldVoteOn().isEmpty();
 	}
@@ -332,6 +327,14 @@ public abstract class GameSession {
 		return tickCounter.getTickCount() % tickInterval == 0;
 	}
 
+	/**
+	 * @return the current tick count. <code>-1</code> if the session didn't get
+	 *         {@linkplain #init(SavedGame) initialized}.
+	 */
+	protected int getTickCount() {
+		return tickCounter == null ? -1 : tickCounter.getTickCount();
+	}
+
 	protected void setGameSpeed(GameSpeed gameSpeed) {
 		this.gameSpeed = gameSpeed;
 	}
diff --git a/core/src/de/gg/game/SlaveSession.java b/core/src/de/gg/game/SlaveSession.java
index bc74916..e21ebd7 100644
--- a/core/src/de/gg/game/SlaveSession.java
+++ b/core/src/de/gg/game/SlaveSession.java
@@ -4,14 +4,13 @@ import java.util.HashMap;
 
 import com.google.common.eventbus.EventBus;
 
+import de.gg.event.AllPlayersReadyEvent;
 import de.gg.event.ChangedGameSpeedEvent;
 import de.gg.event.NewVoteEvent;
-import de.gg.event.NextRoundEvent;
-import de.gg.event.RoundEndDataReceivedEvent;
+import de.gg.event.ServerReadyEvent;
 import de.gg.event.VoteFinishedEvent;
 import de.gg.game.data.GameSessionSetup;
 import de.gg.game.data.GameSpeed;
-import de.gg.game.data.RoundEndData;
 import de.gg.game.data.vote.VoteResults;
 import de.gg.game.entity.Player;
 import de.gg.game.system.ProcessingSystem;
@@ -99,16 +98,15 @@ public class SlaveSession extends GameSession
 		Log.debug("Client", "Alle Spieler sind bereit! Nächste Runde startet");
 
 		this.startNextRound();
-		eventBus.post(new NextRoundEvent());
+		eventBus.post(new AllPlayersReadyEvent(true));
 	}
 
 	@Override
-	public void onRoundEnd(RoundEndData data) { // Inherited from
-												// AuthoritativeResultListener
-		eventBus.post(new RoundEndDataReceivedEvent(data));
-
-		// Process the last round
-		super.processRoundEnd(data); // Inherited from GameSession
+	public void onServerReady() {
+		Log.info("Client", "Der Server is bereit");
+		Log.debug("Client", "%d Ticks hinter der Server-Simulation",
+				TICKS_PER_ROUND - getTickCount());
+		eventBus.post(new ServerReadyEvent());
 	}
 
 	@Override
diff --git a/core/src/de/gg/game/data/RoundEndData.java b/core/src/de/gg/game/data/RoundEndData.java
deleted file mode 100644
index c36bf33..0000000
--- a/core/src/de/gg/game/data/RoundEndData.java
+++ /dev/null
@@ -1,34 +0,0 @@
-package de.gg.game.data;
-
-/**
- * This data is sent after a round ends to setup the next round. It contains all
- * the needed (random) data for next round i.e. the next opening hours.
- */
-public class RoundEndData {
-
-	private int openingHourNextDay;
-	private int closingHourNextDay;
-
-	/**
-	 * @return the hour the market work begins on the next day.
-	 */
-	public int getOpeningHourNextDay() {
-		return openingHourNextDay;
-	}
-
-	public void setOpeningHourNextDay(int openingHourNextDay) {
-		this.openingHourNextDay = openingHourNextDay;
-	}
-
-	/**
-	 * @return the hour the market work ends on the next day.
-	 */
-	public int getClosingHourNextDay() {
-		return closingHourNextDay;
-	}
-
-	public void setClosingHourNextDay(int closingHourNextDay) {
-		this.closingHourNextDay = closingHourNextDay;
-	}
-
-}
diff --git a/core/src/de/gg/game/system/smp/RoundEndSystem.java b/core/src/de/gg/game/system/smp/RoundEndSystem.java
index 4c7e659..512ffe8 100644
--- a/core/src/de/gg/game/system/smp/RoundEndSystem.java
+++ b/core/src/de/gg/game/system/smp/RoundEndSystem.java
@@ -51,6 +51,7 @@ public class RoundEndSystem {
 		}
 
 		// SALARY
+		// TODO statt am Rundenende am Rundenstart berechnen
 		PositionType position = c.getPosition();
 		if (position != null) {
 			c.setGold(c.getGold() + position.getSalary());
diff --git a/core/src/de/gg/network/GameServer.java b/core/src/de/gg/network/GameServer.java
index 2efd270..147fd60 100644
--- a/core/src/de/gg/network/GameServer.java
+++ b/core/src/de/gg/network/GameServer.java
@@ -182,6 +182,16 @@ public class GameServer {
 		Log.info("Server", "Spiel gestartet");
 	}
 
+	/**
+	 * Starts the actual game. Has to get called after the session is
+	 * {@linkplain #initGameSession() initialized}.
+	 * 
+	 * @see AuthoritativeResultListener#onServerReady()
+	 */
+	public void startGame() {
+		session.getResultListenerStub().onServerReady();
+	}
+
 	/**
 	 * Stops the server. Also takes care of saving the game.
 	 */
diff --git a/core/src/de/gg/network/NetworkRegisterer.java b/core/src/de/gg/network/NetworkRegisterer.java
index 20a1ec5..2038a93 100644
--- a/core/src/de/gg/network/NetworkRegisterer.java
+++ b/core/src/de/gg/network/NetworkRegisterer.java
@@ -8,7 +8,6 @@ import com.esotericsoftware.kryo.Kryo;
 import de.gg.game.data.GameDifficulty;
 import de.gg.game.data.GameSessionSetup;
 import de.gg.game.data.GameSpeed;
-import de.gg.game.data.RoundEndData;
 import de.gg.game.data.vote.VoteResults;
 import de.gg.game.type.PlayerIcon;
 import de.gg.game.type.PositionTypes.PositionType;
@@ -57,9 +56,6 @@ public class NetworkRegisterer {
 		kryo.register(GameDifficulty.class);
 		kryo.register(GameSessionSetup.class);
 
-		// Round End Stuff
-		kryo.register(RoundEndData.class);
-
 		// Messages
 		kryo.register(ChatMessageSentMessage.class);
 		kryo.register(GameSetupMessage.class);
diff --git a/core/src/de/gg/network/rmi/AuthoritativeResultListener.java b/core/src/de/gg/network/rmi/AuthoritativeResultListener.java
index d10558b..ae6ffa0 100644
--- a/core/src/de/gg/network/rmi/AuthoritativeResultListener.java
+++ b/core/src/de/gg/network/rmi/AuthoritativeResultListener.java
@@ -1,6 +1,5 @@
 package de.gg.network.rmi;
 
-import de.gg.game.data.RoundEndData;
 import de.gg.game.data.vote.VoteResults;
 import de.gg.game.type.PositionTypes.PositionType;
 
@@ -19,13 +18,10 @@ public interface AuthoritativeResultListener {
 	public void onAllPlayersReadied();
 
 	/**
-	 * Called after a round ended to inform about the changes.
-	 * 
-	 * @param data
-	 *            this data contains all server-side calculations done after a
-	 *            round.
+	 * Called when the server is ready to continue the game session's
+	 * processing. Is normally called when a round is over.
 	 */
-	public void onRoundEnd(RoundEndData data);
+	public void onServerReady();
 
 	public void onCharacterDeath(short characterId);
 
diff --git a/core/src/de/gg/network/rmi/ServerAuthoritativResultListenerStub.java b/core/src/de/gg/network/rmi/ServerAuthoritativResultListenerStub.java
index 1aeade3..8e436ed 100644
--- a/core/src/de/gg/network/rmi/ServerAuthoritativResultListenerStub.java
+++ b/core/src/de/gg/network/rmi/ServerAuthoritativResultListenerStub.java
@@ -4,7 +4,6 @@ import java.util.concurrent.ExecutorService;
 import java.util.concurrent.Executors;
 
 import de.gg.game.AuthoritativeSession;
-import de.gg.game.data.RoundEndData;
 import de.gg.game.data.vote.VoteResults;
 import de.gg.game.type.PositionTypes.PositionType;
 
@@ -43,12 +42,12 @@ public class ServerAuthoritativResultListenerStub
 	}
 
 	@Override
-	public void onRoundEnd(RoundEndData data) {
+	public void onServerReady() {
 		informClients(new ResultTask() {
 			@Override
 			protected void informClient(
 					AuthoritativeResultListener resultListener) {
-				resultListener.onRoundEnd(data);
+				resultListener.onServerReady();
 			}
 		});
 	}
diff --git a/core/src/de/gg/screen/BaseGameScreen.java b/core/src/de/gg/screen/BaseGameScreen.java
index c6691a9..7916feb 100644
--- a/core/src/de/gg/screen/BaseGameScreen.java
+++ b/core/src/de/gg/screen/BaseGameScreen.java
@@ -7,8 +7,8 @@ import com.google.common.eventbus.Subscribe;
 
 import de.gg.event.NewChatMessagEvent;
 import de.gg.event.PlayerDisconnectedEvent;
-import de.gg.event.RoundEndDataReceivedEvent;
 import de.gg.event.RoundEndEvent;
+import de.gg.event.ServerReadyEvent;
 
 public abstract class BaseGameScreen extends BaseUIScreen {
 
@@ -45,9 +45,8 @@ public abstract class BaseGameScreen extends BaseUIScreen {
 	}
 
 	@Subscribe
-	public void onRoundEndDataArrived(RoundEndDataReceivedEvent event) {
-		((GameRoundendScreen) game.getScreen("roundEnd"))
-				.setData(event.getData());
+	public void onServerReady(ServerReadyEvent event) {
+		((GameRoundendScreen) game.getScreen("roundEnd")).setServerReady();
 	}
 
 	@Subscribe
diff --git a/core/src/de/gg/screen/GameLoadingScreen.java b/core/src/de/gg/screen/GameLoadingScreen.java
index 39687a0..d59714b 100644
--- a/core/src/de/gg/screen/GameLoadingScreen.java
+++ b/core/src/de/gg/screen/GameLoadingScreen.java
@@ -5,7 +5,7 @@ import com.badlogic.gdx.graphics.g3d.ModelInstance;
 import com.badlogic.gdx.math.Vector3;
 import com.google.common.eventbus.Subscribe;
 
-import de.gg.event.RoundEndDataReceivedEvent;
+import de.gg.event.ServerReadyEvent;
 import de.gg.game.entity.BuildingSlot;
 import de.gg.game.factory.CharacterFactory;
 import de.gg.game.type.BuildingTypes;
@@ -97,13 +97,16 @@ public class GameLoadingScreen extends BaseLoadingScreen {
 
 		// Change the screen
 		Log.info("Client", "Spiel geladen & gestartet");
+
+		if (game.isHost())
+			game.getServer().startGame();
+
 		game.pushScreen("roundEnd");
 	}
 
 	@Subscribe
-	public void onRoundEndDataArrived(RoundEndDataReceivedEvent event) {
-		((GameRoundendScreen) game.getScreen("roundEnd"))
-				.setData(event.getData());
+	public void onRoundEndDataArrived(ServerReadyEvent event) {
+		((GameRoundendScreen) game.getScreen("roundEnd")).setServerReady();
 	}
 
 }
diff --git a/core/src/de/gg/screen/GameRoundendScreen.java b/core/src/de/gg/screen/GameRoundendScreen.java
index d7899ff..999b72b 100644
--- a/core/src/de/gg/screen/GameRoundendScreen.java
+++ b/core/src/de/gg/screen/GameRoundendScreen.java
@@ -12,14 +12,16 @@ import com.badlogic.gdx.scenes.scene2d.ui.Table;
 import com.badlogic.gdx.utils.Align;
 import com.google.common.eventbus.Subscribe;
 
-import de.gg.event.NextRoundEvent;
-import de.gg.event.RoundEndDataReceivedEvent;
-import de.gg.game.data.RoundEndData;
+import de.gg.event.AllPlayersReadyEvent;
+import de.gg.event.ServerReadyEvent;
 import de.gg.util.Log;
 import net.dermetfan.gdx.assets.AnnotationAssetManager.Asset;
 
 /**
- * This screen is rendered after a round ends.
+ * This screen is rendered after a round ends. When the server is
+ * {@linkplain #serverReady ready} all clients can
+ * {@linkplain #onAllPlayersReady(AllPlayersReadyEvent) ready up} and after that
+ * this screen switches either to the voting or the map screen.
  */
 public class GameRoundendScreen extends BaseGameScreen {
 
@@ -29,7 +31,12 @@ public class GameRoundendScreen extends BaseGameScreen {
 	private final String FLIP_SOUND = "audio/flip-page.mp3";
 	private Sound flipSound;
 
-	private volatile RoundEndData data = null;
+	/**
+	 * Whether the server is ready to process the next round.
+	 * 
+	 * @see ServerReadyEvent
+	 */
+	private volatile boolean serverReady = false;
 
 	private ImageTextButton nextButton;
 	private Label lastYearTitle, comingYearTitle, lastYearData, comingYearData;
@@ -100,56 +107,51 @@ public class GameRoundendScreen extends BaseGameScreen {
 	}
 
 	private synchronized void updateUI() {
-		// Data anzeigen
-		if (data != null) {
+		// Informationen zu Rundenende anzeigen
+		if (serverReady) {
 			lastYearTitle.setText("Das vergangene Jahr");
 			comingYearTitle.setText("Kommendes Jahr");
 
 			lastYearData.setText("-3 Gold für XYZ");
-			comingYearData.setText(String.format(
-					"-15 Gold für XYZ \n+3 AP\n Die Geschäfte öffnen um %d",
-					data.getOpeningHourNextDay()));
+			comingYearData.setText(String.format("-15 Gold für XYZ \n+3 AP"));
 		}
 
 		nextButton.setText("Weiter");
-		nextButton.setDisabled(data == null);
+		nextButton.setDisabled(!serverReady);
 		nextButton.setTouchable(
-				data == null ? Touchable.disabled : Touchable.enabled);
+				!serverReady ? Touchable.disabled : Touchable.enabled);
 	}
 
 	@Override
 	public void renderGame(float delta) {
 		game.getClient().updatePing(delta);
 
-		if (game.isHost())
-			game.getServer().update();
+		// if (game.isHost())
+		// game.getServer().update();
 	}
 
 	@Subscribe
 	@Override
-	public synchronized void onRoundEndDataArrived(
-			RoundEndDataReceivedEvent event) {
-		this.setData(event.getData());
+	public synchronized void onServerReady(ServerReadyEvent event) {
+		this.serverReady = true;
 
 		updateUI();
 	}
 
-	@Subscribe
-	public void onNextRound(NextRoundEvent event) {
-		setData(null);
-		if (!game.getClient().getCity().getMattersToHoldVoteOn().isEmpty())
-			game.pushScreen("vote");
-		else
-			game.pushScreen("map");
+	public void setServerReady() {
+		this.serverReady = true;
 	}
 
-	/**
-	 * Set the round end data that should get applied.
-	 * 
-	 * @param data
-	 */
-	public void setData(RoundEndData data) {
-		this.data = data;
+	@Subscribe
+	public void onAllPlayersReady(AllPlayersReadyEvent event) {
+		this.serverReady = false;
+
+		if (event.isNextRound()) {
+			if (!game.getClient().getCity().getMattersToHoldVoteOn().isEmpty())
+				game.pushScreen("vote");
+			else
+				game.pushScreen("map");
+		}
 	}
 
 	@Override
diff --git a/core/src/de/gg/screen/SettingsScreen.java b/core/src/de/gg/screen/SettingsScreen.java
index 7a44231..672d359 100644
--- a/core/src/de/gg/screen/SettingsScreen.java
+++ b/core/src/de/gg/screen/SettingsScreen.java
@@ -10,8 +10,8 @@ import com.badlogic.gdx.scenes.scene2d.ui.Slider;
 import com.badlogic.gdx.scenes.scene2d.ui.Table;
 import com.google.common.eventbus.Subscribe;
 
-import de.gg.event.RoundEndDataReceivedEvent;
 import de.gg.event.RoundEndEvent;
+import de.gg.event.ServerReadyEvent;
 import de.gg.input.ButtonClickListener;
 import de.gg.ui.KeySelectionInputField;
 import de.gg.ui.KeySelectionInputField.KeySelectionEventListener;
@@ -221,9 +221,8 @@ public class SettingsScreen extends BaseUIScreen {
 	}
 
 	@Subscribe
-	public void onRoundEndDataArrived(RoundEndDataReceivedEvent event) {
-		((GameRoundendScreen) game.getScreen("roundEnd"))
-				.setData(event.getData());
+	public void onRoundEndDataArrived(ServerReadyEvent event) {
+		((GameRoundendScreen) game.getScreen("roundEnd")).setServerReady();
 	}
 
 	public BaseScreen getCaller() {
diff --git a/core/src/de/gg/util/TickCounter.java b/core/src/de/gg/util/TickCounter.java
index 60e648f..8752c8e 100644
--- a/core/src/de/gg/util/TickCounter.java
+++ b/core/src/de/gg/util/TickCounter.java
@@ -12,8 +12,7 @@ public class TickCounter {
 	private int tickCount = 0;
 
 	/**
-	 * Creates a tick counter. Has to be {@linkplain #reset() reset} first to
-	 * get used.
+	 * Creates a tick counter.
 	 * 
 	 * @param tickHandler
 	 * @param maxTicks
@@ -28,8 +27,6 @@ public class TickCounter {
 		this.tickHandler = tickHandler;
 		this.maxTicks = maxTicks;
 		this.tickDuration = tickDuration;
-
-		tickCount = maxTicks;
 	}
 
 	/**
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
