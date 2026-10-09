This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: bcc6b84868516881e8b8f24eb7668ce242ec0ce8
- Commit message: 
- Diff:
```
commit bcc6b84868516881e8b8f24eb7668ce242ec0ce8
Author: Roger Baumgartner <rogermarcbaumgartner@hotmail.com>
Date:   Sat Nov 18 00:37:44 2017 +0100
---
 .../github/theholywaffle/teamspeak3/TS3Query.java  | 54 +++++++++++++++-------
 1 file changed, 38 insertions(+), 16 deletions(-)

diff --git a/src/main/java/com/github/theholywaffle/teamspeak3/TS3Query.java b/src/main/java/com/github/theholywaffle/teamspeak3/TS3Query.java
index 57ef52d..f5d5cec 100644
--- a/src/main/java/com/github/theholywaffle/teamspeak3/TS3Query.java
+++ b/src/main/java/com/github/theholywaffle/teamspeak3/TS3Query.java
@@ -35,6 +35,7 @@ import org.slf4j.LoggerFactory;
 
 import java.util.concurrent.ExecutorService;
 import java.util.concurrent.Executors;
+import java.util.concurrent.atomic.AtomicBoolean;
 
 public class TS3Query {
 
@@ -69,9 +70,10 @@ public class TS3Query {
 	private final TS3ApiAsync asyncApi;
 	private final TS3Config config;
 
-	private QueryIO io;
+	private final AtomicBoolean connected = new AtomicBoolean(false);
+	private final AtomicBoolean shuttingDown = new AtomicBoolean(false);
 
-	private volatile boolean connected;
+	private QueryIO io;
 
 	/**
 	 * Creates a TS3Query that connects to a TS3 server at
@@ -92,7 +94,6 @@ public class TS3Query {
 		this.config = config;
 		this.fileTransferHelper = new FileTransferHelper(config.getHost());
 		this.connectionHandler = config.getReconnectStrategy().create(config.getConnectionHandler());
-		this.connected = false;
 
 		this.asyncApi = new TS3ApiAsync(this);
 		this.api = new TS3Api(asyncApi);
@@ -111,7 +112,7 @@ public class TS3Query {
 		}
 
 		io = new QueryIO(this, config);
-		connected = true;
+		connected.set(true);
 
 		try {
 			connectionHandler.onConnect(this);
@@ -124,22 +125,39 @@ public class TS3Query {
 	/**
 	 * Removes and closes all used resources to the TeamSpeak server.
 	 */
-	public synchronized void exit() {
-		if (connected) {
+	public void exit() {
+		if (shuttingDown.compareAndSet(false, true)) {
 			// Sending this command will guarantee that all previously sent commands have been processed
 			try {
 				api.quit();
 			} catch (TS3Exception e) {
 				log.warn("Could not send a quit command to terminate the connection", e);
+			} finally {
+				shutDown();
+			}
+		} else {
+			// Only 1 thread shall ever send quit, the rest of the threads wait for the first thread to finish
+			try {
+				synchronized (this) {
+					while (connected.get()) {
+						wait();
+					}
+				}
+			} catch (InterruptedException e) {
+				// Restore interrupt, then bail out
+				Thread.currentThread().interrupt();
 			}
 		}
+	}
 
+	private synchronized void shutDown() {
 		if (io != null) {
 			io.disconnect();
 		}
 
-		connected = false;
 		userThreadPool.shutdown();
+		connected.set(false);
+		notifyAll();
 	}
 
 	/**
@@ -161,7 +179,7 @@ public class TS3Query {
 	 * @see TS3Config#setConnectionHandler(ConnectionHandler)
 	 */
 	public boolean isConnected() {
-		return connected;
+		return connected.get();
 	}
 
 	public TS3Api getApi() {
@@ -200,19 +218,23 @@ public class TS3Query {
 	}
 
 	void fireDisconnect() {
-		connected = false;
+		connected.set(false);
 
 		submitUserTask("ConnectionHandler disconnect task", new Runnable() {
 			@Override
 			public void run() {
-				try {
-					connectionHandler.onDisconnect(TS3Query.this);
-				} finally {
-					if (!connected) {
-						exit();
-					}
-				}
+				handleDisconnect();
 			}
 		});
 	}
+
+	private synchronized void handleDisconnect() {
+		try {
+			connectionHandler.onDisconnect(this);
+		} finally {
+			if (!connected.get()) {
+				shutDown();
+			}
+		}
+	}
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
