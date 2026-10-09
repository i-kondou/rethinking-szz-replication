This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: be39b286273f3ce14a6e3b4ad6d6401aaa3f5fa6
- Commit message: 
- Diff:
```
commit be39b286273f3ce14a6e3b4ad6d6401aaa3f5fa6
Author: 123DMWM <shmo1joe2@gmail.com>
Date:   Wed Aug 12 16:41:30 2015 -0400
---
 src/main/java/com/mojang/minecraft/Minecraft.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/src/main/java/com/mojang/minecraft/Minecraft.java b/src/main/java/com/mojang/minecraft/Minecraft.java
index 75edcf1..bd57e68 100644
--- a/src/main/java/com/mojang/minecraft/Minecraft.java
+++ b/src/main/java/com/mojang/minecraft/Minecraft.java
@@ -1926,7 +1926,7 @@ public final class Minecraft implements Runnable {
                     }
                     if (currentScreen == null) {
                         if (Keyboard.getEventKey() == Keyboard.KEY_ESCAPE) {
-                            if (!packetHandler.isLoadingLevel){
+                            if (!packetHandler.isLoadingLevel || !isOnline()){
                                 pause();
                             } else {
                                 Mouse.setGrabbed(false);
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
