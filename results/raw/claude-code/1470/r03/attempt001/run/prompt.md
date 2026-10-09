This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: ddd19d8307447856b7823d91a2e7b3141f0c9f0d
- Commit message: MINOR: Remove unused variable to fix spotBugs failure

Fixed spotBugs error:

>Dead store to isFreshAssignment in org.apache.kafka.clients.consumer.internals.AbstractStickyAssignor.generalAssign(Map, Map)

Reviewers: Ismael Juma <ismael@juma.me.uk>
- Diff:
```
commit ddd19d8307447856b7823d91a2e7b3141f0c9f0d
Author: Nikolay <nizhikov@apache.org>
Date:   Tue Jun 2 18:59:56 2020 +0300

    MINOR: Remove unused variable to fix spotBugs failure
    
    Fixed spotBugs error:
    
    >Dead store to isFreshAssignment in org.apache.kafka.clients.consumer.internals.AbstractStickyAssignor.generalAssign(Map, Map)
    
    Reviewers: Ismael Juma <ismael@juma.me.uk>
---
 .../apache/kafka/clients/consumer/internals/AbstractStickyAssignor.java  | 1 -
 1 file changed, 1 deletion(-)

diff --git a/clients/src/main/java/org/apache/kafka/clients/consumer/internals/AbstractStickyAssignor.java b/clients/src/main/java/org/apache/kafka/clients/consumer/internals/AbstractStickyAssignor.java
index d4e023cc0..353a225c8 100644
--- a/clients/src/main/java/org/apache/kafka/clients/consumer/internals/AbstractStickyAssignor.java
+++ b/clients/src/main/java/org/apache/kafka/clients/consumer/internals/AbstractStickyAssignor.java
@@ -274,7 +274,6 @@ public abstract class AbstractStickyAssignor extends AbstractPartitionAssignor {
         Map<TopicPartition, ConsumerGenerationPair> prevAssignment = new HashMap<>();
 
         prepopulateCurrentAssignments(subscriptions, currentAssignment, prevAssignment);
-        boolean isFreshAssignment = currentAssignment.isEmpty();
 
         // a mapping of all topic partitions to all consumers that can be assigned to them
         final Map<TopicPartition, List<String>> partition2AllPotentialConsumers = new HashMap<>();
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
