This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: dc4ddf091e7a1f33d10d820ef70714f23a9c6d39
- Commit message: 
- Diff:
```
commit dc4ddf091e7a1f33d10d820ef70714f23a9c6d39
Author: RayMin <rmin@thoughtworks.com>
Date:   Wed Feb 28 19:51:06 2018 +0800
---
 .../com/github/wuxudong/rncharts/charts/CustomPieChart.java  | 12 ++++++------
 1 file changed, 6 insertions(+), 6 deletions(-)

diff --git a/android/src/main/java/com/github/wuxudong/rncharts/charts/CustomPieChart.java b/android/src/main/java/com/github/wuxudong/rncharts/charts/CustomPieChart.java
index 6110ef6..53cdf76 100644
--- a/android/src/main/java/com/github/wuxudong/rncharts/charts/CustomPieChart.java
+++ b/android/src/main/java/com/github/wuxudong/rncharts/charts/CustomPieChart.java
@@ -3,12 +3,9 @@ package com.github.wuxudong.rncharts.charts;
 import android.content.Context;
 import android.util.AttributeSet;
 import android.view.MotionEvent;
-import android.view.View;
 
 import com.github.mikephil.charting.charts.PieChart;
 import com.github.mikephil.charting.highlight.Highlight;
-import com.github.mikephil.charting.listener.ChartTouchListener;
-import com.github.mikephil.charting.listener.OnChartGestureListener;
 import com.github.mikephil.charting.listener.PieRadarChartTouchListener;
 
 /**
@@ -34,9 +31,12 @@ public class CustomPieChart extends PieChart {
 
         mChartTouchListener = new PieRadarChartTouchListener(this){
 
-            if (h != null && !h.equalTo(mLastHighlighted)) {
-                mChart.highlightValue(h, true);
-                mLastHighlighted = h;
+            protected void performHighlight(Highlight h, MotionEvent e) {
+
+                if (h != null && !h.equalTo(mLastHighlighted)) {
+                    mChart.highlightValue(h, true);
+                    mLastHighlighted = h;
+                }
             }
         };
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
