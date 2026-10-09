This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 6e9ec7a38c9ffc87ce881fbe679f5a7e65b7eb2c
- Commit message: Fix org.getMembers() to 'wrap' returned users for post-populating

This fixes an issue in which users returned by `getMembers()` were not
populated with a full set of values.

This commit just applies 'wrapping' to all users returned, so that methods
like `user.getCreatedAt()` can be called on returned users without throwing
a NullPointerException - the reference to 'root' allows the user objects to
populate themselves.
- Diff:
```
commit 6e9ec7a38c9ffc87ce881fbe679f5a7e65b7eb2c
Author: Roberto Tyley <roberto.tyley@gmail.com>
Date:   Fri Mar 14 09:22:15 2014 +0000

    Fix org.getMembers() to 'wrap' returned users for post-populating
    
    This fixes an issue in which users returned by `getMembers()` were not
    populated with a full set of values.
    
    This commit just applies 'wrapping' to all users returned, so that methods
    like `user.getCreatedAt()` can be called on returned users without throwing
    a NullPointerException - the reference to 'root' allows the user objects to
    populate themselves.
---
 src/main/java/org/kohsuke/github/GHOrganization.java | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)

diff --git a/src/main/java/org/kohsuke/github/GHOrganization.java b/src/main/java/org/kohsuke/github/GHOrganization.java
index dedc9e2..f040518 100644
--- a/src/main/java/org/kohsuke/github/GHOrganization.java
+++ b/src/main/java/org/kohsuke/github/GHOrganization.java
@@ -105,7 +105,8 @@ public class GHOrganization extends GHPerson {
                 String filterParams = (filter == null) ? "" : ("?filter=" + filter);
                 return new PagedIterator<GHUser>(root.retrieve().asIterator(String.format("/orgs/%s/%s%s", login, suffix, filterParams), GHUser[].class)) {
                     @Override
-                    protected void wrapUp(GHUser[] page) {
+                    protected void wrapUp(GHUser[] users) {
+                        GHUser.wrap(users, root);
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
