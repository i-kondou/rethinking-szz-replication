This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 550830f34aceec69a708921c7c262a42090ed162
- Commit message: fixed a bug
- Diff:
```
commit 550830f34aceec69a708921c7c262a42090ed162
Author: aviaryan <avi.aryan123@gmail.com>
Date:   Thu Feb 11 13:09:31 2016 +0530

    fixed a bug
---
 app/src/main/java/in/aviaryan/popularmovies/MainActivityFragment.java | 1 +
 1 file changed, 1 insertion(+)

diff --git a/app/src/main/java/in/aviaryan/popularmovies/MainActivityFragment.java b/app/src/main/java/in/aviaryan/popularmovies/MainActivityFragment.java
index 72bd0be..cd46c06 100644
--- a/app/src/main/java/in/aviaryan/popularmovies/MainActivityFragment.java
+++ b/app/src/main/java/in/aviaryan/popularmovies/MainActivityFragment.java
@@ -49,6 +49,7 @@ public class MainActivityFragment extends Fragment {
 
         updateUI();
         gridview = (GridView) mainFragmentView.findViewById(R.id.gridView);
+        gridview.setAdapter(imageAdapter);
 
         gridview.setOnItemClickListener(new AdapterView.OnItemClickListener() {
             @Override
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
