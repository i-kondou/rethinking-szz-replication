This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 9caec2863ab6430eab50d86bb39bf89423056160
- Commit message: 
- Diff:
```
commit 9caec2863ab6430eab50d86bb39bf89423056160
Author: gid15@web.de <gid15@web.de>
Date:   Thu Dec 20 19:23:02 2018 +0100
---
 src/jpcsp/HLE/modules/sceAtrac3plus.java | 26 +++++++++++++++++++++++---
 1 file changed, 23 insertions(+), 3 deletions(-)

diff --git a/src/jpcsp/HLE/modules/sceAtrac3plus.java b/src/jpcsp/HLE/modules/sceAtrac3plus.java
index 292ed7b8..23e55e09 100644
--- a/src/jpcsp/HLE/modules/sceAtrac3plus.java
+++ b/src/jpcsp/HLE/modules/sceAtrac3plus.java
@@ -209,9 +209,19 @@ public class sceAtrac3plus extends HLEModule {
         public int setHalfwayBuffer(int addr, int readSize, int bufferSize, boolean isMonoOutput, AtracFileInfo info) {
         	this.info = info;
         	channels = info.atracChannels;
-        	int maxSizeBeforeFirstWrap = bufferSize - ((bufferSize - info.inputFileDataOffset) % info.atracBytesPerFrame);
-        	int maxSizeAfterFirstWrap = bufferSize - (bufferSize % info.atracBytesPerFrame);
-    		inputBuffer = new pspFileBuffer(addr, maxSizeBeforeFirstWrap, maxSizeAfterFirstWrap, readSize, readSize);
+        	int maxSizeBeforeFirstWrap = bufferSize;
+        	int maxSizeAfterFirstWrap = bufferSize;
+
+        	// If the buffer is not already full, try to align it on multiple of atracBytesPerFrame
+        	if (readSize < bufferSize) {
+        		int maxSizeAligned = bufferSize - ((bufferSize - info.inputFileDataOffset) % info.atracBytesPerFrame);
+        		if (maxSizeAligned >= readSize) {
+        			maxSizeBeforeFirstWrap = maxSizeAligned;
+        			maxSizeAfterFirstWrap = bufferSize - (bufferSize % info.atracBytesPerFrame);
+        		}
+        	}
+
+        	inputBuffer = new pspFileBuffer(addr, maxSizeBeforeFirstWrap, maxSizeAfterFirstWrap, readSize, readSize);
         	inputBuffer.notifyRead(info.inputFileDataOffset);
     		inputBuffer.setFileMaxSize(info.inputFileSize);
         	currentReadPosition = info.inputFileDataOffset;
@@ -308,6 +318,9 @@ public class sceAtrac3plus extends HLEModule {
 
         	if (log.isDebugEnabled()) {
         		log.debug(String.format("decodeData from 0x%08X(0x%X) to 0x%08X(0x%X), skippedSamples=0x%X, currentSample=0x%X, outputChannels=%d", readAddr, info.atracBytesPerFrame, decodedSamplesAddr, maxSamples, skippedSamples, currentSample, outputChannels));
+        		if (log.isTraceEnabled()) {
+        			log.trace(String.format("decodeData from:%s", Utilities.getMemoryDump(readAddr, info.atracBytesPerFrame)));
+        		}
         	}
 
         	int result = codec.decode(mem, readAddr, info.atracBytesPerFrame, mem, decodedSamplesAddr);
@@ -399,6 +412,9 @@ public class sceAtrac3plus extends HLEModule {
         				log.debug(String.format("addStreamData ignored as the atrac has looped inbetween: sample 0x%X -> 0x%X", getStreamDataInfoCurrentSample, getAtracCurrentSample()));
         			}
         		} else {
+        			if (log.isTraceEnabled()) {
+        				log.trace(String.format("addStreamData length=0x%X: %s", length, Utilities.getMemoryDump(inputBuffer.getWriteAddr(), length)));
+        			}
         			inputBuffer.notifyWrite(length);
         		}
         	}
@@ -1028,6 +1044,10 @@ public class sceAtrac3plus extends HLEModule {
         // Allow negative values.
         // "Tales of VS - ULJS00209" is even passing an uninitialized value bufferSize=0xDEADBEEF
 
+        if (log.isTraceEnabled()) {
+        	log.trace(String.format("hleSetHalfwayBufferAndGetID buffer=%s", Utilities.getMemoryDump(buffer, readSize)));
+        }
+
         AtracFileInfo info = new AtracFileInfo();
         int codecType = analyzeRiffFile(buffer.getMemory(), buffer.getAddress(), readSize, info);
         if (codecType < 0) {
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
