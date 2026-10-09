This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 333cd0d114de5bee2bdbfc3be91c7a373174dfe1
- Commit message: Fixed unused imports, and fixed a bug.
- Diff:
```
commit 333cd0d114de5bee2bdbfc3be91c7a373174dfe1
Author: Ned Twigg <ned.twigg@diffplug.com>
Date:   Thu Dec 1 18:11:25 2016 -0800

    Fixed unused imports, and fixed a bug.
---
 src/main/java/com/diffplug/gradle/oomph/ConventionJdt.java | 4 +---
 1 file changed, 1 insertion(+), 3 deletions(-)

diff --git a/src/main/java/com/diffplug/gradle/oomph/ConventionJdt.java b/src/main/java/com/diffplug/gradle/oomph/ConventionJdt.java
index 9cf914d..b1502b8 100644
--- a/src/main/java/com/diffplug/gradle/oomph/ConventionJdt.java
+++ b/src/main/java/com/diffplug/gradle/oomph/ConventionJdt.java
@@ -16,9 +16,7 @@
 package com.diffplug.gradle.oomph;
 
 import java.util.HashSet;
-import java.util.LinkedHashMap;
 import java.util.List;
-import java.util.Map;
 import java.util.Set;
 
 import org.gradle.api.Action;
@@ -77,7 +75,7 @@ public class ConventionJdt extends OomphConvention {
 				"org.eclipse.jdt.core.compiler.compliance",
 				"org.eclipse.jdt.core.compiler.source");
 		extension.workspaceProp(JDT_CORE_PREFS, props -> {
-			JDT_COMPLIANCE_PROPS.forEach(p -> props.put(p, compilerComplianceLevel.toString()));
+			JDT_COMPLIANCE_PROPS.forEach(p -> props.put(p, JavaVersion.toVersion(compilerComplianceLevel).toString()));
 			//Use default compliance settings.
 			props.put("org.eclipse.jdt.core.compiler.codegen.inlineJsrBytecode", "enabled");
 			props.put("org.eclipse.jdt.core.compiler.problem.assertIdentifier", "error");
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
