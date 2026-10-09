This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: fdab258bd9d24deb072ecd0f4c2522027dae52b1
- Commit message: 
- Diff:
```
commit fdab258bd9d24deb072ecd0f4c2522027dae52b1
Author: Piotr Rusin <piotr.rusin88@gmail.com>
Date:   Wed Mar 29 19:14:49 2017 +0200
---
 .../github/{piotr/rusin => piotr_rusin}/yule/YuleApplicationTests.java  | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/src/test/java/com/github/piotr/rusin/yule/YuleApplicationTests.java b/src/test/java/com/github/piotr_rusin/yule/YuleApplicationTests.java
similarity index 97%
rename from src/test/java/com/github/piotr/rusin/yule/YuleApplicationTests.java
rename to src/test/java/com/github/piotr_rusin/yule/YuleApplicationTests.java
index 6cc5d0d..dc0e64b 100644
--- a/src/test/java/com/github/piotr/rusin/yule/YuleApplicationTests.java
+++ b/src/test/java/com/github/piotr_rusin/yule/YuleApplicationTests.java
@@ -21,7 +21,7 @@
  * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  * SOFTWARE.
  *******************************************************************************/
-package com.github.piotr.rusin.yule;
+package com.github.piotr_rusin.yule;
 
 import org.junit.Test;
 import org.junit.runner.RunWith;
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
