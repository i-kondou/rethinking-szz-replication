This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 90690d5428fc3db1dbac73e4c30b302a93bad087
- Commit message: 
- Diff:
```
commit 90690d5428fc3db1dbac73e4c30b302a93bad087
Author: fertrist <fertrist@rambler.ru>
Date:   Mon May 2 13:34:44 2016 +0300
---
 src/main/java/org/mishpaha/project/config/SecurityConfig.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/src/main/java/org/mishpaha/project/config/SecurityConfig.java b/src/main/java/org/mishpaha/project/config/SecurityConfig.java
index a581a92..62e20fc 100644
--- a/src/main/java/org/mishpaha/project/config/SecurityConfig.java
+++ b/src/main/java/org/mishpaha/project/config/SecurityConfig.java
@@ -14,7 +14,7 @@ import org.springframework.security.web.csrf.HttpSessionCsrfTokenRepository;
 
 import javax.sql.DataSource;
 
-@EnableWebSecurity
+@Configuration
 @Order(SecurityProperties.ACCESS_OVERRIDE_ORDER)
 public class SecurityConfig extends WebSecurityConfigurerAdapter {
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
