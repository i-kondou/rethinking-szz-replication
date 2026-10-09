This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 5187cc1ae803708e1875f1e419c97883cce85657
- Commit message: 
- Diff:
```
commit 5187cc1ae803708e1875f1e419c97883cce85657
Author: Armin Schrenk <armin.schrenk@zoho.eu>
Date:   Mon May 25 12:30:03 2020 +0200
---
 src/main/java/com/dokany/java/DokanyDriver.java | 33 +++++++++++++++++++++----
 1 file changed, 28 insertions(+), 5 deletions(-)

diff --git a/src/main/java/com/dokany/java/DokanyDriver.java b/src/main/java/com/dokany/java/DokanyDriver.java
index 7c8d008..7e30677 100644
--- a/src/main/java/com/dokany/java/DokanyDriver.java
+++ b/src/main/java/com/dokany/java/DokanyDriver.java
@@ -5,6 +5,10 @@ import com.dokany.java.structure.DeviceOptions;
 import org.slf4j.Logger;
 import org.slf4j.LoggerFactory;
 
+import java.util.concurrent.CompletableFuture;
+import java.util.concurrent.ExecutionException;
+import java.util.concurrent.TimeUnit;
+import java.util.concurrent.TimeoutException;
 import java.util.concurrent.atomic.AtomicBoolean;
 
 /**
@@ -70,12 +74,29 @@ public final class DokanyDriver {
 					}
 				});
 
-				int mountStatus = NativeMethods.DokanMain(deviceOptions, new DokanyOperationsProxy(fileSystem));
+				int mountStatus = 0;
+
+
+				try {
+					mountStatus = CompletableFuture
+							.supplyAsync(() -> NativeMethods.DokanMain(deviceOptions, new DokanyOperationsProxy(fileSystem)))
+							.get(2900, TimeUnit.MILLISECONDS);
+				} catch (TimeoutException e) {
+					// ok
+					mountStatus = 0;
+				} catch (ExecutionException e) {
+					mountStatus = -1;
+				} catch (InterruptedException e) {
+					Thread.currentThread().interrupt();
+				}
+
 
 				if (mountStatus < 0) {
 					throw new IllegalStateException(MountError.fromInt(mountStatus).getDescription());
+				} else {
+					isMounted.set(true);
 				}
-				isMounted.set(true);
+
 
 			} catch (UnsatisfiedLinkError err) {
 				LOG.error("Unable to load dokan driver.", err);
@@ -95,12 +116,14 @@ public final class DokanyDriver {
 	public synchronized void shutdown() {
 		LOG.info("Unmounting Dokan device at {}", deviceOptions.MountPoint);
 		if (isMounted.get()) {
-			isMounted.set(NativeMethods.DokanRemoveMountPoint(deviceOptions.MountPoint)); //TODO: check if the volume is already unmounted
-			if (isMounted.get()) {
+			boolean unmounted = NativeMethods.DokanRemoveMountPoint(deviceOptions.MountPoint);
+			if (unmounted) {
+				isMounted.set(false);
+			} else {
 				LOG.error("Unable to unmount Dokan device at {}.", deviceOptions.MountPoint);
 			}
 		} else {
-			LOG.info("Dokan Device {} already unmounted.", deviceOptions.MountPoint);
+			LOG.info("Dokan Device not mounted at {}.", deviceOptions.MountPoint);
 		}
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
