This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: e475aeddbc3516f80272f6095477debc6c0129d2
- Commit message: 
- Diff:
```
commit e475aeddbc3516f80272f6095477debc6c0129d2
Author: Phillip Webb <pwebb@pivotal.io>
Date:   Sat Sep 21 12:29:46 2019 -0700
---
 .../servlet/ApplicationContextRequestMatcher.java  | 14 +++--
 .../ApplicationContextRequestMatcherTests.java     | 73 ++++++++++++++++++++++
 2 files changed, 83 insertions(+), 4 deletions(-)

diff --git a/spring-boot-project/spring-boot/src/main/java/org/springframework/boot/security/servlet/ApplicationContextRequestMatcher.java b/spring-boot-project/spring-boot/src/main/java/org/springframework/boot/security/servlet/ApplicationContextRequestMatcher.java
index ff1bc115cf..a56626e873 100644
--- a/spring-boot-project/spring-boot/src/main/java/org/springframework/boot/security/servlet/ApplicationContextRequestMatcher.java
+++ b/spring-boot-project/spring-boot/src/main/java/org/springframework/boot/security/servlet/ApplicationContextRequestMatcher.java
@@ -16,7 +16,6 @@
 
 package org.springframework.boot.security.servlet;
 
-import java.util.concurrent.atomic.AtomicBoolean;
 import java.util.function.Supplier;
 
 import javax.servlet.http.HttpServletRequest;
@@ -44,7 +43,9 @@ public abstract class ApplicationContextRequestMatcher<C> implements RequestMatc
 
 	private final Class<? extends C> contextClass;
 
-	private final AtomicBoolean initialized = new AtomicBoolean(false);
+	private volatile boolean initialized;
+
+	private final Object initializeLock = new Object();
 
 	public ApplicationContextRequestMatcher(Class<? extends C> contextClass) {
 		Assert.notNull(contextClass, "Context class must not be null");
@@ -59,8 +60,13 @@ public abstract class ApplicationContextRequestMatcher<C> implements RequestMatc
 			return false;
 		}
 		Supplier<C> context = () -> getContext(webApplicationContext);
-		if (this.initialized.compareAndSet(false, true)) {
-			initialized(context);
+		if (!this.initialized) {
+			synchronized (this.initializeLock) {
+				if (!this.initialized) {
+					initialized(context);
+					this.initialized = true;
+				}
+			}
 		}
 		return matches(request, context);
 	}
diff --git a/spring-boot-project/spring-boot/src/test/java/org/springframework/boot/security/servlet/ApplicationContextRequestMatcherTests.java b/spring-boot-project/spring-boot/src/test/java/org/springframework/boot/security/servlet/ApplicationContextRequestMatcherTests.java
index c08bc5681f..8ddce424da 100644
--- a/spring-boot-project/spring-boot/src/test/java/org/springframework/boot/security/servlet/ApplicationContextRequestMatcherTests.java
+++ b/spring-boot-project/spring-boot/src/test/java/org/springframework/boot/security/servlet/ApplicationContextRequestMatcherTests.java
@@ -16,6 +16,10 @@
 
 package org.springframework.boot.security.servlet;
 
+import java.lang.Thread.UncaughtExceptionHandler;
+import java.util.ArrayList;
+import java.util.List;
+import java.util.concurrent.atomic.AtomicBoolean;
 import java.util.function.Supplier;
 
 import javax.servlet.http.HttpServletRequest;
@@ -26,6 +30,7 @@ import org.springframework.beans.factory.NoSuchBeanDefinitionException;
 import org.springframework.context.ApplicationContext;
 import org.springframework.mock.web.MockHttpServletRequest;
 import org.springframework.mock.web.MockServletContext;
+import org.springframework.util.ReflectionUtils;
 import org.springframework.web.context.WebApplicationContext;
 import org.springframework.web.context.support.StaticWebApplicationContext;
 
@@ -105,6 +110,31 @@ public class ApplicationContextRequestMatcherTests {
 		assertThat(matcher.matches(request)).isFalse();
 	}
 
+	@Test // gh-18211
+	public void matchesWhenConcurrentlyCalledWaitsForInitialize() {
+		ConcurrentApplicationContextRequestMatcher matcher = new ConcurrentApplicationContextRequestMatcher();
+		StaticWebApplicationContext context = createWebApplicationContext();
+		Runnable target = () -> matcher.matches(new MockHttpServletRequest(context.getServletContext()));
+		List<Thread> threads = new ArrayList<>();
+		AssertingUncaughtExceptionHandler exceptionHandler = new AssertingUncaughtExceptionHandler();
+		for (int i = 0; i < 2; i++) {
+			Thread thread = new Thread(target);
+			thread.setUncaughtExceptionHandler(exceptionHandler);
+			threads.add(thread);
+		}
+		threads.forEach(Thread::start);
+		threads.forEach(this::join);
+		exceptionHandler.assertNoExceptions();
+	}
+
+	private void join(Thread thread) {
+		try {
+			thread.join(1000);
+		}
+		catch (InterruptedException ex) {
+		}
+	}
+
 	private StaticWebApplicationContext createWebApplicationContext() {
 		StaticWebApplicationContext context = new StaticWebApplicationContext();
 		MockServletContext servletContext = new MockServletContext();
@@ -160,4 +190,47 @@ public class ApplicationContextRequestMatcherTests {
 
 	}
 
+	static class ConcurrentApplicationContextRequestMatcher extends ApplicationContextRequestMatcher<Object> {
+
+		ConcurrentApplicationContextRequestMatcher() {
+			super(Object.class);
+		}
+
+		private AtomicBoolean initialized = new AtomicBoolean();
+
+		@Override
+		protected void initialized(Supplier<Object> context) {
+			try {
+				Thread.sleep(200);
+			}
+			catch (InterruptedException ex) {
+			}
+			this.initialized.set(true);
+		}
+
+		@Override
+		protected boolean matches(HttpServletRequest request, Supplier<Object> context) {
+			assertThat(this.initialized.get()).isTrue();
+			return true;
+		}
+
+	}
+
+	private static class AssertingUncaughtExceptionHandler implements UncaughtExceptionHandler {
+
+		private volatile Throwable ex;
+
+		@Override
+		public void uncaughtException(Thread thead, Throwable ex) {
+			this.ex = ex;
+		}
+
+		public void assertNoExceptions() {
+			if (this.ex != null) {
+				ReflectionUtils.rethrowRuntimeException(this.ex);
+			}
+		}
+
+	}
+
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
