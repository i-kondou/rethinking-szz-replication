This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 5534be1bc60d3bfc884f70077ef94780e866f255
- Commit message: 
- Diff:
```
commit 5534be1bc60d3bfc884f70077ef94780e866f255
Author: Gabriel Roldan <gabriel.roldan@gmail.com>
Date:   Wed Oct 2 22:06:33 2019 -0300
---
 .../console/ws/newaccount/NewAccountFormControllerTest.java    | 10 ++++++++--
 1 file changed, 8 insertions(+), 2 deletions(-)

diff --git a/console/src/test/java/org/georchestra/console/ws/newaccount/NewAccountFormControllerTest.java b/console/src/test/java/org/georchestra/console/ws/newaccount/NewAccountFormControllerTest.java
index d7b39020b..fb3877a44 100644
--- a/console/src/test/java/org/georchestra/console/ws/newaccount/NewAccountFormControllerTest.java
+++ b/console/src/test/java/org/georchestra/console/ws/newaccount/NewAccountFormControllerTest.java
@@ -50,7 +50,7 @@ import java.util.Arrays;
 import java.util.HashMap;
 import java.util.List;
 
-import static junit.framework.Assert.assertEquals;
+import static org.junit.Assert.assertEquals;
 import static org.junit.Assert.assertFalse;
 import static org.junit.Assert.assertTrue;
 import static org.mockito.Matchers.any;
@@ -80,6 +80,8 @@ public class NewAccountFormControllerTest {
     private BindingResult mockedValidationReports = mock(BindingResult.class);
     private SessionStatus status = mock(SessionStatus.class);
 
+    private final String orgName = "geOrchestra testing team";
+
     @Before
     public void setUp() {
 
@@ -96,14 +98,18 @@ public class NewAccountFormControllerTest {
         Account adminAccount = AccountFactory.createBrief("testadmin", "monkey123", "Test", "ADmin",
                 "postmastrer@localhost", "+33123456789", "admin", "");
         request.addHeader("sec-username", "testadmin"); // Set user connected through http header
+        Org mockOrg = new Org();
+        mockOrg.setName(orgName);
         try {
             when(mockAccountDao.findByUID(eq("testadmin"))).thenReturn(adminAccount);
+            when(mockOrgDao.findByCommonName(eq(orgName))).thenReturn(mockOrg);
         } catch (DataServiceException | NameNotFoundException e) {
             assertTrue(false);
         }
 
         String[] orgTypes = { "Association", "Company", "Non-governmental organization" };
         when(mockOrgDao.getOrgTypeValues()).thenReturn(orgTypes);
+
     }
 
     @Test
@@ -406,7 +412,7 @@ public class NewAccountFormControllerTest {
         when(formBean.getRecaptcha_response_field()).thenReturn("abc1234");
         when(formBean.getPhone()).thenReturn("+331234567890");
         when(formBean.getTitle()).thenReturn("+331234567890");
-        when(formBean.getOrg()).thenReturn("geOrchestra testing team");
+        when(formBean.getOrg()).thenReturn(orgName);
         when(formBean.getDescription()).thenReturn("Bot Unit Testing");
         when(formBean.getPrivacyPolicyAgreed()).thenReturn(true);
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
