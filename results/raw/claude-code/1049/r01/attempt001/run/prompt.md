This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 7c5e119134c20141b7af1322d08cca0d047d1e34
- Commit message: MINOR: fix a bug in removing elements from an ImplicitLinkedHashColle…

Fix a bug that resulted in incorrect behavior when
deleting through an iterator.

The bug is that the hash table relies on a denseness invariant... if you remove something,
you might have to move some other things. Calling removeElementAtSlot will do this.
Calling removeFromList is not enough.

Reviewers: Jason Gustafson <jason@confluent.io>
- Diff:
```
commit 7c5e119134c20141b7af1322d08cca0d047d1e34
Author: Colin Patrick McCabe <cmccabe@confluent.io>
Date:   Wed Oct 14 14:53:30 2020 -0700

    MINOR: fix a bug in removing elements from an ImplicitLinkedHashColle…
    
    Fix a bug that resulted in incorrect behavior when
    deleting through an iterator.
    
    The bug is that the hash table relies on a denseness invariant... if you remove something,
    you might have to move some other things. Calling removeElementAtSlot will do this.
    Calling removeFromList is not enough.
    
    Reviewers: Jason Gustafson <jason@confluent.io>
---
 .../common/utils/ImplicitLinkedHashCollection.java |  3 +--
 .../utils/ImplicitLinkedHashCollectionTest.java    | 24 +++++++++++++++++++++-
 2 files changed, 24 insertions(+), 3 deletions(-)

diff --git a/clients/src/main/java/org/apache/kafka/common/utils/ImplicitLinkedHashCollection.java b/clients/src/main/java/org/apache/kafka/common/utils/ImplicitLinkedHashCollection.java
index decabe886..3e1bccc47 100644
--- a/clients/src/main/java/org/apache/kafka/common/utils/ImplicitLinkedHashCollection.java
+++ b/clients/src/main/java/org/apache/kafka/common/utils/ImplicitLinkedHashCollection.java
@@ -208,8 +208,7 @@ public class ImplicitLinkedHashCollection<E extends ImplicitLinkedHashCollection
                 throw new IllegalStateException();
             }
             Element nextElement = indexToElement(head, elements, lastReturned.next());
-            removeFromList(head, elements, nextElement.prev());
-            size--;
+            ImplicitLinkedHashCollection.this.removeElementAtSlot(nextElement.prev());
             if (lastReturned == cur) {
                 // If the element we are removing was cur, set cur to cur->next.
                 cur = nextElement;
diff --git a/clients/src/test/java/org/apache/kafka/common/utils/ImplicitLinkedHashCollectionTest.java b/clients/src/test/java/org/apache/kafka/common/utils/ImplicitLinkedHashCollectionTest.java
index 01be3a6fd..152d5be7f 100644
--- a/clients/src/test/java/org/apache/kafka/common/utils/ImplicitLinkedHashCollectionTest.java
+++ b/clients/src/test/java/org/apache/kafka/common/utils/ImplicitLinkedHashCollectionTest.java
@@ -103,7 +103,8 @@ public class ImplicitLinkedHashCollectionTest {
 
         @Override
         public int hashCode() {
-            return key;
+            long hashCode = 2654435761L * key;
+            return (int) (hashCode >> 32);
         }
     }
 
@@ -596,4 +597,25 @@ public class ImplicitLinkedHashCollectionTest {
         Assert.assertThrows(RuntimeException.class, () ->
             coll.moveToEnd(new TestElement(4, 4)));
     }
+
+    @Test
+    public void testRemovals() {
+        ImplicitLinkedHashCollection<TestElement> coll = new ImplicitLinkedHashCollection<>();
+        List<TestElement> elements  = new ArrayList<>();
+        for (int i = 0; i < 100; i++) {
+            TestElement element  = new TestElement(i, i);
+            elements.add(element);
+            coll.add(element);
+        }
+        assertEquals(100, coll.size());
+        Iterator<TestElement> iter = coll.iterator();
+        for (int i = 0; i < 50; i++) {
+            iter.next();
+            iter.remove();
+        }
+        assertEquals(50, coll.size());
+        for (int i = 50; i < 100; i++) {
+            assertEquals(new TestElement(i, i), coll.find(elements.get(i)));
+        }
+    }
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
