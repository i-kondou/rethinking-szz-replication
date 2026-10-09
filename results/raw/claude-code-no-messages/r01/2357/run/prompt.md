This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 0cc556efc448ec980d988b6e276df8b19f851aa2
- Commit message: 
- Diff:
```
commit 0cc556efc448ec980d988b6e276df8b19f851aa2
Author: Mohamed EL Habib <mohamed.el-habib@digitaslbi.fr>
Date:   Mon Dec 18 03:32:40 2017 +0100
---
 .../org/jenkinsci/plugins/GitLabLogoutAction.java  |  7 +++---
 .../org/jenkinsci/plugins/GitLabSecurityRealm.java | 27 ++++++++++++----------
 2 files changed, 18 insertions(+), 16 deletions(-)

diff --git a/src/main/java/org/jenkinsci/plugins/GitLabLogoutAction.java b/src/main/java/org/jenkinsci/plugins/GitLabLogoutAction.java
index 38ea10f..7f152b6 100644
--- a/src/main/java/org/jenkinsci/plugins/GitLabLogoutAction.java
+++ b/src/main/java/org/jenkinsci/plugins/GitLabLogoutAction.java
@@ -71,11 +71,10 @@ public class GitLabLogoutAction implements UnprotectedRootAction {
 
     @Restricted(NoExternalUse.class) // jelly only
     public String getGitLabText() {
-        Jenkins j = Jenkins.getInstance();
-        assert j != null;
-        SecurityRealm r = j.getSecurityRealm();
+        Jenkins jenkins = Jenkins.getInstance();
+        assert jenkins != null;
+        SecurityRealm r = jenkins.getSecurityRealm();
         if (r instanceof GitLabSecurityRealm) {
-            GitLabSecurityRealm glsr = (GitLabSecurityRealm) r;
             return "GitLab";
         }
         // only called from the Jelly if the GitLabSecurityRealm is set...
diff --git a/src/main/java/org/jenkinsci/plugins/GitLabSecurityRealm.java b/src/main/java/org/jenkinsci/plugins/GitLabSecurityRealm.java
index 0a93f91..b56564e 100644
--- a/src/main/java/org/jenkinsci/plugins/GitLabSecurityRealm.java
+++ b/src/main/java/org/jenkinsci/plugins/GitLabSecurityRealm.java
@@ -223,16 +223,21 @@ public class GitLabSecurityRealm extends SecurityRealm implements UserDetailsSer
 		}
 
 		private void setValue(GitLabSecurityRealm realm, String node, String value) {
-			if (node.toLowerCase().equals("clientid")) {
-				realm.setClientID(value);
-			} else if (node.toLowerCase().equals("clientsecret")) {
-				realm.setClientSecret(value);
-			} else if (node.toLowerCase().equals("gitlabweburi")) {
-				realm.setGitlabWebUri(value);
-			} else if (node.toLowerCase().equals("gitlabapiuri")) {
-				realm.setGitlabApiUri(value);
-			} else {
-				throw new ConversionException("Invalid node value = " + node);
+			switch (node.toLowerCase()) {
+                case "clientid":
+                    realm.setClientID(value);
+                    break;
+                case "clientsecret":
+                    realm.setClientSecret(value);
+                    break;
+                case "gitlabweburi":
+                    realm.setGitlabWebUri(value);
+                    break;
+                case "gitlabapiuri":
+                    realm.setGitlabApiUri(value);
+                    break;
+                default:
+				    throw new ConversionException("Invalid node value = " + node);
 			}
 		}
 
@@ -383,8 +388,6 @@ public class GitLabSecurityRealm extends SecurityRealm implements UserDetailsSer
 			if (node != null) {
 				return node.asText();
 			}
-		} catch (JsonProcessingException e) {
-			Log.error(e.getMessage(), e);
 		} catch (IOException e) {
 			Log.error(e.getMessage(), e);
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
