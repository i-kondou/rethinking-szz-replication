This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: d33e5278b211753ac3d46acb7d6213f3ae75e087
- Commit message: kvm: Fix double-escape issue while creating rbd disk options

This fixes issue
in which the rados host/monitor port was double escaped.

Signed-off-by: Rohit Yadav <rohit.yadav@shapeblue.com>
- Diff:
```
commit d33e5278b211753ac3d46acb7d6213f3ae75e087
Author: Rohit Yadav <rohit.yadav@shapeblue.com>
Date:   Tue Jan 5 15:23:38 2021 +0530

    kvm: Fix double-escape issue while creating rbd disk options
    
    This fixes issue
    in which the rados host/monitor port was double escaped.
    
    Signed-off-by: Rohit Yadav <rohit.yadav@shapeblue.com>
---
 .../src/main/java/com/cloud/hypervisor/kvm/storage/KVMPhysicalDisk.java | 2 +-
 .../test/java/com/cloud/hypervisor/kvm/storage/KVMPhysicalDiskTest.java | 2 +-
 2 files changed, 2 insertions(+), 2 deletions(-)

diff --git a/plugins/hypervisors/kvm/src/main/java/com/cloud/hypervisor/kvm/storage/KVMPhysicalDisk.java b/plugins/hypervisors/kvm/src/main/java/com/cloud/hypervisor/kvm/storage/KVMPhysicalDisk.java
index 221a3d7c18..5b4a61058d 100644
--- a/plugins/hypervisors/kvm/src/main/java/com/cloud/hypervisor/kvm/storage/KVMPhysicalDisk.java
+++ b/plugins/hypervisors/kvm/src/main/java/com/cloud/hypervisor/kvm/storage/KVMPhysicalDisk.java
@@ -29,7 +29,7 @@ public class KVMPhysicalDisk {
         rbdOpts = "rbd:" + image;
         rbdOpts += ":mon_host=" + monHost;
         if (monPort > 0) {
-            rbdOpts += "\\\\:" + monPort;
+            rbdOpts += "\\:" + monPort;
         }
 
         if (authUserName == null) {
diff --git a/plugins/hypervisors/kvm/src/test/java/com/cloud/hypervisor/kvm/storage/KVMPhysicalDiskTest.java b/plugins/hypervisors/kvm/src/test/java/com/cloud/hypervisor/kvm/storage/KVMPhysicalDiskTest.java
index bd644c85cd..cf39dceb1a 100644
--- a/plugins/hypervisors/kvm/src/test/java/com/cloud/hypervisor/kvm/storage/KVMPhysicalDiskTest.java
+++ b/plugins/hypervisors/kvm/src/test/java/com/cloud/hypervisor/kvm/storage/KVMPhysicalDiskTest.java
@@ -25,7 +25,7 @@ public class KVMPhysicalDiskTest extends TestCase {
 
     public void testRBDStringBuilder() {
         assertEquals(KVMPhysicalDisk.RBDStringBuilder("ceph-monitor", 8000, "admin", "supersecret", "volume1"),
-                     "rbd:volume1:mon_host=ceph-monitor\\\\:8000:auth_supported=cephx:id=admin:key=supersecret:rbd_default_format=2:client_mount_timeout=30");
+                     "rbd:volume1:mon_host=ceph-monitor\\:8000:auth_supported=cephx:id=admin:key=supersecret:rbd_default_format=2:client_mount_timeout=30");
     }
 
     public void testAttributes() {
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
