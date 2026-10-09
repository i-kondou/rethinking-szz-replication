This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: e3a09244c0309b814ff0b6ce85908a0d3ba82840
- Commit message: generated table code fixes

fixed problems

fixed generated table factory method argument ordering

added static access to a table's raw (unnamespaced) table name

uniformed style for generated table code

updated auto generated tables

removed wildcard imports
- Diff:
```
commit e3a09244c0309b814ff0b6ce85908a0d3ba82840
Author: Bobby Ullman <bullman@palantir.com>
Date:   Wed Oct 7 13:49:54 2015 -0700

    generated table code fixes
    
    fixed problems
    
    fixed generated table factory method argument ordering
    
    added static access to a table's raw (unnamespaced) table name
    
    uniformed style for generated table code
    
    updated auto generated tables
    
    removed wildcard imports
---
 .../schema/generated/SweepPriorityTable.java       | 12 +++--
 .../schema/generated/SweepProgressTable.java       | 12 +++--
 .../schema/generated/UpgTaskMetadataTable.java     | 10 +++-
 .../schema/generated/UpgradeMetadataTable.java     | 12 +++--
 .../render/RowOrDynamicColumnRenderer.java         | 61 ++++++++++++++++------
 .../description/render/TableFactoryRenderer.java   |  2 +-
 .../table/description/render/TableRenderer.java    | 14 +++++
 .../schema/indexing/generated/DataTable.java       | 48 ++++++++++++-----
 .../schema/indexing/generated/TwoColumnsTable.java | 32 ++++++++----
 .../generated/StreamTest2StreamHashAidxTable.java  | 16 ++++--
 .../generated/StreamTest2StreamIdxTable.java       | 16 ++++--
 .../generated/StreamTest2StreamMetadataTable.java  | 12 +++--
 .../generated/StreamTest2StreamValueTable.java     | 10 +++-
 .../generated/StreamTestStreamHashAidxTable.java   | 16 ++++--
 .../stream/generated/StreamTestStreamIdxTable.java | 16 ++++--
 .../generated/StreamTestStreamMetadataTable.java   | 12 +++--
 .../generated/StreamTestStreamValueTable.java      | 10 +++-
 .../generated/UserPhotosStreamHashAidxTable.java   | 16 ++++--
 .../schema/generated/UserPhotosStreamIdxTable.java | 16 ++++--
 .../generated/UserPhotosStreamMetadataTable.java   | 12 +++--
 .../generated/UserPhotosStreamValueTable.java      | 10 +++-
 .../profile/schema/generated/UserProfileTable.java | 42 ++++++++++-----
 22 files changed, 301 insertions(+), 106 deletions(-)

diff --git a/atlasdb-client/src/main/java/com/palantir/atlasdb/schema/generated/SweepPriorityTable.java b/atlasdb-client/src/main/java/com/palantir/atlasdb/schema/generated/SweepPriorityTable.java
index 5318e84..05c89c8 100644
--- a/atlasdb-client/src/main/java/com/palantir/atlasdb/schema/generated/SweepPriorityTable.java
+++ b/atlasdb-client/src/main/java/com/palantir/atlasdb/schema/generated/SweepPriorityTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -112,6 +114,10 @@ public final class SweepPriorityTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -155,7 +161,7 @@ public final class SweepPriorityTable implements
             return new Function<String, SweepPriorityRow>() {
                 @Override
                 public SweepPriorityRow apply(String row) {
-                    return new SweepPriorityRow(row);
+                    return SweepPriorityRow.of(row);
                 }
             };
         }
@@ -172,7 +178,7 @@ public final class SweepPriorityTable implements
                 int __index = 0;
                 String fullTableName = PtBytes.toString(__input, __index, __input.length-__index);
                 __index += 0;
-                return of(fullTableName);
+                return SweepPriorityRow.of(fullTableName);
             }
         };
 
@@ -1012,5 +1018,5 @@ public final class SweepPriorityTable implements
         return ImmutableList.of();
     }
 
-    static String __CLASS_HASH = "m27lLOYfbvklYVrYxtoKog==";
+    static String __CLASS_HASH = "VH+ZkEOsv/yPU+lzUUD6HA==";
 }
diff --git a/atlasdb-client/src/main/java/com/palantir/atlasdb/schema/generated/SweepProgressTable.java b/atlasdb-client/src/main/java/com/palantir/atlasdb/schema/generated/SweepProgressTable.java
index 71f083d..71e0555 100644
--- a/atlasdb-client/src/main/java/com/palantir/atlasdb/schema/generated/SweepProgressTable.java
+++ b/atlasdb-client/src/main/java/com/palantir/atlasdb/schema/generated/SweepProgressTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -112,6 +114,10 @@ public final class SweepProgressTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -155,7 +161,7 @@ public final class SweepProgressTable implements
             return new Function<Long, SweepProgressRow>() {
                 @Override
                 public SweepProgressRow apply(Long row) {
-                    return new SweepProgressRow(row);
+                    return SweepProgressRow.of(row);
                 }
             };
         }
@@ -172,7 +178,7 @@ public final class SweepProgressTable implements
                 int __index = 0;
                 Long dummy = EncodingUtils.decodeUnsignedVarLong(__input, __index);
                 __index += EncodingUtils.sizeOfUnsignedVarLong(dummy);
-                return of(dummy);
+                return SweepProgressRow.of(dummy);
             }
         };
 
@@ -1012,5 +1018,5 @@ public final class SweepProgressTable implements
         return ImmutableList.of();
     }
 
-    static String __CLASS_HASH = "l2w+15AbTF4UGWo+c8hxUw==";
+    static String __CLASS_HASH = "ehL5vm/72YkdZNZNA33rQQ==";
 }
diff --git a/atlasdb-client/src/main/java/com/palantir/atlasdb/schema/generated/UpgTaskMetadataTable.java b/atlasdb-client/src/main/java/com/palantir/atlasdb/schema/generated/UpgTaskMetadataTable.java
index c09563e..ce7be4d 100644
--- a/atlasdb-client/src/main/java/com/palantir/atlasdb/schema/generated/UpgTaskMetadataTable.java
+++ b/atlasdb-client/src/main/java/com/palantir/atlasdb/schema/generated/UpgTaskMetadataTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -112,6 +114,10 @@ public final class UpgTaskMetadataTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -258,7 +264,7 @@ public final class UpgTaskMetadataTable implements
                 __index += EncodingUtils.sizeOfVarString(extraId);
                 Long rangeId = EncodingUtils.decodeUnsignedVarLong(__input, __index);
                 __index += EncodingUtils.sizeOfUnsignedVarLong(rangeId);
-                return of(namespace, version, hotfixVersion, hotfixHotfix, extraId, rangeId);
+                return UpgTaskMetadataRow.of(namespace, version, hotfixVersion, hotfixHotfix, extraId, rangeId);
             }
         };
 
@@ -791,5 +797,5 @@ public final class UpgTaskMetadataTable implements
         return ImmutableList.of();
     }
 
-    static String __CLASS_HASH = "oRyDIlHgjaReJ+rMdhgadw==";
+    static String __CLASS_HASH = "fljatuiBsr6K9BUXbTDoWQ==";
 }
diff --git a/atlasdb-client/src/main/java/com/palantir/atlasdb/schema/generated/UpgradeMetadataTable.java b/atlasdb-client/src/main/java/com/palantir/atlasdb/schema/generated/UpgradeMetadataTable.java
index 6f9cc13..e6f087b 100644
--- a/atlasdb-client/src/main/java/com/palantir/atlasdb/schema/generated/UpgradeMetadataTable.java
+++ b/atlasdb-client/src/main/java/com/palantir/atlasdb/schema/generated/UpgradeMetadataTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -112,6 +114,10 @@ public final class UpgradeMetadataTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -155,7 +161,7 @@ public final class UpgradeMetadataTable implements
             return new Function<String, UpgradeMetadataRow>() {
                 @Override
                 public UpgradeMetadataRow apply(String row) {
-                    return new UpgradeMetadataRow(row);
+                    return UpgradeMetadataRow.of(row);
                 }
             };
         }
@@ -172,7 +178,7 @@ public final class UpgradeMetadataTable implements
                 int __index = 0;
                 String namespace = PtBytes.toString(__input, __index, __input.length-__index);
                 __index += 0;
-                return of(namespace);
+                return UpgradeMetadataRow.of(namespace);
             }
         };
 
@@ -1059,5 +1065,5 @@ public final class UpgradeMetadataTable implements
         return ImmutableList.of();
     }
 
-    static String __CLASS_HASH = "LpWO30b9kH5IhcrqzJ9auQ==";
+    static String __CLASS_HASH = "h03MSdcbTez7kajqIeeSaA==";
 }
diff --git a/atlasdb-client/src/main/java/com/palantir/atlasdb/table/description/render/RowOrDynamicColumnRenderer.java b/atlasdb-client/src/main/java/com/palantir/atlasdb/table/description/render/RowOrDynamicColumnRenderer.java
index a8a921c..4cae92f 100644
--- a/atlasdb-client/src/main/java/com/palantir/atlasdb/table/description/render/RowOrDynamicColumnRenderer.java
+++ b/atlasdb-client/src/main/java/com/palantir/atlasdb/table/description/render/RowOrDynamicColumnRenderer.java
@@ -52,15 +52,15 @@ class RowOrDynamicColumnRenderer extends Renderer {
             line();
             constructor();
             line();
-            for (NameComponentDescription comp : desc.getRowParts()) {
+            for (NameComponentDescription comp : getRowPartsWithoutHash()) {
                 getVarName(comp);
                 line();
             }
-            for (NameComponentDescription comp : desc.getRowParts()) {
+            for (NameComponentDescription comp : getRowPartsWithoutHash()) {
                 getVarNameFun(comp);
                 line();
             }
-            if (desc.getRowParts().size() == 1) {
+            if (getRowPartsWithoutHash().size() == 1) {
                 fromVarNameFun();
                 line();
             }
@@ -112,7 +112,10 @@ class RowOrDynamicColumnRenderer extends Renderer {
     }
 
     private void staticFactory() {
-        line("public static ", Name, " of"); renderParameterList(); lineEnd(" {"); {
+        line("public static ", Name, " of"); renderParameterList(getRowPartsWithoutHash()); lineEnd(" {"); {
+            if (desc.hasFirstComponentHash()) {
+                renderComputeFirstComponentHash();
+            }
             line("return new ", Name); renderArgumentList(); lineEnd(";");
         } line("}");
     }
@@ -143,12 +146,12 @@ class RowOrDynamicColumnRenderer extends Renderer {
     }
 
     private void fromVarNameFun() {
-        NameComponentDescription comp = Iterables.getOnlyElement(desc.getRowParts());
+        NameComponentDescription comp = Iterables.getOnlyElement(getRowPartsWithoutHash());
         line("public static Function<", TypeName(comp), ", ", Name, "> from", VarName(comp), "Fun() {"); {
             line("return new Function<", TypeName(comp), ", ", Name, ">() {"); {
                 line("@Override");
                 line("public ", Name, " apply(", TypeName(comp), " row) {"); {
-                    line("return new ", Name, "(row);");
+                    line("return ", Name, ".of(row);");
                 } line("}");
             } line("};");
         } line("}");
@@ -186,15 +189,22 @@ class RowOrDynamicColumnRenderer extends Renderer {
                     }
                     line("__index += ", comp.getType().getHydrateSizeCode(var), ";");
                 }
-                line("return of(", Joiner.on(", ").join(vars), ");");
+                line("return ", Name, ".of(", Joiner.on(", ").join(vars), ");");
             } line("}");
         } line("};");
     }
 
     private void createPrefixRange(int i, boolean isSorted) {
-        line("public static RangeRequest.Builder createPrefixRange", isSorted ? "" : "Unsorted"); renderParameterList(i); lineEnd(" {"); {
+        List<NameComponentDescription> components = getRowPartsWithoutHash().subList(0, i);
+        line("public static RangeRequest.Builder createPrefixRange", isSorted ? "" : "Unsorted"); renderParameterList(components); lineEnd(" {"); {
             List<String> vars = Lists.newArrayList();
-            for (NameComponentDescription comp : desc.getRowParts().subList(0, i)) {
+            if (desc.hasFirstComponentHash()) {
+                renderComputeFirstComponentHash();
+                String var = NameMetadataDescription.HASH_ROW_COMPONENT_NAME + "Bytes";
+                vars.add(var);
+                line("byte[] ", var, " = ", ValueType.FIXED_LONG.getPersistCode(NameMetadataDescription.HASH_ROW_COMPONENT_NAME), ";");
+            }
+            for (NameComponentDescription comp : components) {
                 String var = varName(comp) + "Bytes";
                 vars.add(var);
                 line("byte[] ", var, " = ", comp.getType().getPersistCode(varName(comp)), ";");
@@ -207,9 +217,16 @@ class RowOrDynamicColumnRenderer extends Renderer {
     }
 
     private void prefix(int i, boolean isSorted) {
-        line("public static Prefix prefix", isSorted ? "" : "Unsorted"); renderParameterList(i); lineEnd(" {"); {
+        List<NameComponentDescription> components = getRowPartsWithoutHash().subList(0, i);
+        line("public static Prefix prefix", isSorted ? "" : "Unsorted"); renderParameterList(components); lineEnd(" {"); {
             List<String> vars = Lists.newArrayList();
-            for (NameComponentDescription comp : desc.getRowParts().subList(0, i)) {
+            if (desc.hasFirstComponentHash()) {
+                renderComputeFirstComponentHash();
+                String var = NameMetadataDescription.HASH_ROW_COMPONENT_NAME + "Bytes";
+                vars.add(var);
+                line("byte[] ", var, " = ", ValueType.FIXED_LONG.getPersistCode(NameMetadataDescription.HASH_ROW_COMPONENT_NAME), ";");
+            }
+            for (NameComponentDescription comp : components) {
                 String var = varName(comp) + "Bytes";
                 vars.add(var);
                 line("byte[] ", var, " = ", comp.getType().getPersistCode(varName(comp)), ";");
@@ -221,6 +238,11 @@ class RowOrDynamicColumnRenderer extends Renderer {
         } line("}");
     }
 
+    private void renderComputeFirstComponentHash() {
+        NameComponentDescription firstRowPart = getRowPartsWithoutHash().get(0);
+        line("long ", NameMetadataDescription.HASH_ROW_COMPONENT_NAME, " = Hashing.murmur3_128().hashBytes(ValueType.", firstRowPart.getType().name(), ".convertFromJava(", varName(firstRowPart), ")).asLong();");
+    }
+
     private void renderToString() {
         line("@Override");
         line("public String toString() {"); {
@@ -270,7 +292,8 @@ class RowOrDynamicColumnRenderer extends Renderer {
 
     private void renderCompareTo() {
         line("@Override");
-        line("public int compareTo(", Name, " o) {"); {
+        line("public int compareTo(", Name, " o) {");
+        {
             line("return ComparisonChain.start()");
             for (NameComponentDescription comp : desc.getRowParts()) {
                 String comparator = TypeName(comp).equals("byte[]") ? ", UnsignedBytes.lexicographicalComparator()" : "";
@@ -281,12 +304,12 @@ class RowOrDynamicColumnRenderer extends Renderer {
     }
 
     private void renderParameterList() {
-        renderParameterList(desc.getRowParts().size());
+        renderParameterList(desc.getRowParts());
     }
 
-    private void renderParameterList(int i) {
+    private void renderParameterList(List<NameComponentDescription> components) {
         lineEnd("(");
-        for (NameComponentDescription comp : desc.getRowParts().subList(0, i)) {
+        for (NameComponentDescription comp : components.subList(0, components.size())) {
             lineEnd(typeName(comp), " ", varName(comp), ", ");
         }
         replace(", ", ")");
@@ -303,4 +326,12 @@ class RowOrDynamicColumnRenderer extends Renderer {
         }
         replace(", ", ")");
     }
+
+    private List<NameComponentDescription> getRowPartsWithoutHash() {
+        if (!desc.hasFirstComponentHash()) {
+            return desc.getRowParts();
+        } else {
+            return desc.getRowParts().subList(1, desc.getRowParts().size());
+        }
+    }
 }
diff --git a/atlasdb-client/src/main/java/com/palantir/atlasdb/table/description/render/TableFactoryRenderer.java b/atlasdb-client/src/main/java/com/palantir/atlasdb/table/description/render/TableFactoryRenderer.java
index 558a262..eaecb53 100644
--- a/atlasdb-client/src/main/java/com/palantir/atlasdb/table/description/render/TableFactoryRenderer.java
+++ b/atlasdb-client/src/main/java/com/palantir/atlasdb/table/description/render/TableFactoryRenderer.java
@@ -116,7 +116,7 @@ public class TableFactoryRenderer {
                 String Trigger = Table + "." + name + "Trigger";
                 if (table.getGenericTableName() != null) {
                     line("public ", Table, " get", Table, "(Transaction t, String name, ", Trigger, "... triggers) {"); {
-                        line("return ", Table, ".of(t, name, namespace, Triggers.getAllTriggers(t, sharedTriggers, triggers));");
+                        line("return ", Table, ".of(t, namespace, name, Triggers.getAllTriggers(t, sharedTriggers, triggers));");
                     } line("}");
                 } else {
                     line("public ", Table, " get", Table, "(Transaction t, ", Trigger, "... triggers) {"); {
diff --git a/atlasdb-client/src/main/java/com/palantir/atlasdb/table/description/render/TableRenderer.java b/atlasdb-client/src/main/java/com/palantir/atlasdb/table/description/render/TableRenderer.java
index 6f01edb..2a0310c 100644
--- a/atlasdb-client/src/main/java/com/palantir/atlasdb/table/description/render/TableRenderer.java
+++ b/atlasdb-client/src/main/java/com/palantir/atlasdb/table/description/render/TableRenderer.java
@@ -54,6 +54,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.io.BaseEncoding;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
@@ -87,6 +88,7 @@ import com.palantir.atlasdb.table.description.NamedColumnDescription;
 import com.palantir.atlasdb.table.description.Schemas;
 import com.palantir.atlasdb.table.description.TableDefinition;
 import com.palantir.atlasdb.table.description.TableMetadata;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -229,6 +231,10 @@ public class TableRenderer {
                 staticFactories();
                 line();
                 constructors();
+                if (!isGeneric) {
+                    line();
+                    renderGetRawTableName();
+                }
                 line();
                 renderGetTableName();
                 line();
@@ -407,6 +413,12 @@ public class TableRenderer {
             } line("}");
         }
 
+        private void renderGetRawTableName() {
+            line("public static String getRawTableName() {"); {
+                line("return rawTableName;");
+            } line("}");
+        }
+
         private void renderGetTableName() {
             line("public String getTableName() {"); {
                 line("return tableName;");
@@ -1302,5 +1314,7 @@ public class TableRenderer {
         CompressionUtils.class,
         Compression.class,
         Namespace.class,
+        Hashing.class,
+        ValueType.class
     };
 }
diff --git a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/indexing/generated/DataTable.java b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/indexing/generated/DataTable.java
index 8c14ef6..b50ada4 100644
--- a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/indexing/generated/DataTable.java
+++ b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/indexing/generated/DataTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -112,6 +114,10 @@ public final class DataTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -155,7 +161,7 @@ public final class DataTable implements
             return new Function<Long, DataRow>() {
                 @Override
                 public DataRow apply(Long row) {
-                    return new DataRow(row);
+                    return DataRow.of(row);
                 }
             };
         }
@@ -172,7 +178,7 @@ public final class DataTable implements
                 int __index = 0;
                 Long id = Long.MIN_VALUE ^ PtBytes.toLong(__input, __index);
                 __index += 8;
-                return of(id);
+                return DataRow.of(id);
             }
         };
 
@@ -854,6 +860,10 @@ public final class DataTable implements
             this.namespace = namespace;
         }
 
+        public static String getRawTableName() {
+            return rawTableName;
+        }
+
         public String getTableName() {
             return tableName;
         }
@@ -897,7 +907,7 @@ public final class DataTable implements
                 return new Function<Long, Index1IdxRow>() {
                     @Override
                     public Index1IdxRow apply(Long row) {
-                        return new Index1IdxRow(row);
+                        return Index1IdxRow.of(row);
                     }
                 };
             }
@@ -914,7 +924,7 @@ public final class DataTable implements
                     int __index = 0;
                     Long value = Long.MIN_VALUE ^ PtBytes.toLong(__input, __index);
                     __index += 8;
-                    return of(value);
+                    return Index1IdxRow.of(value);
                 }
             };
 
@@ -1034,7 +1044,7 @@ public final class DataTable implements
                     __index += EncodingUtils.sizeOfSizedBytes(columnName);
                     Long id = Long.MIN_VALUE ^ PtBytes.toLong(__input, __index);
                     __index += 8;
-                    return of(rowName, columnName, id);
+                    return Index1IdxColumn.of(rowName, columnName, id);
                 }
             };
 
@@ -1483,6 +1493,10 @@ public final class DataTable implements
             this.namespace = namespace;
         }
 
+        public static String getRawTableName() {
+            return rawTableName;
+        }
+
         public String getTableName() {
             return tableName;
         }
@@ -1553,7 +1567,7 @@ public final class DataTable implements
                     __index += 8;
                     Long id = Long.MIN_VALUE ^ PtBytes.toLong(__input, __index);
                     __index += 8;
-                    return of(value, id);
+                    return Index2IdxRow.of(value, id);
                 }
             };
 
@@ -1666,7 +1680,7 @@ public final class DataTable implements
                     __index += EncodingUtils.sizeOfSizedBytes(rowName);
                     byte[] columnName = EncodingUtils.decodeSizedBytes(__input, __index);
                     __index += EncodingUtils.sizeOfSizedBytes(columnName);
-                    return of(rowName, columnName);
+                    return Index2IdxColumn.of(rowName, columnName);
                 }
             };
 
@@ -2112,6 +2126,10 @@ public final class DataTable implements
             this.namespace = namespace;
         }
 
+        public static String getRawTableName() {
+            return rawTableName;
+        }
+
         public String getTableName() {
             return tableName;
         }
@@ -2155,7 +2173,7 @@ public final class DataTable implements
                 return new Function<Long, Index3IdxRow>() {
                     @Override
                     public Index3IdxRow apply(Long row) {
-                        return new Index3IdxRow(row);
+                        return Index3IdxRow.of(row);
                     }
                 };
             }
@@ -2172,7 +2190,7 @@ public final class DataTable implements
                     int __index = 0;
                     Long value = Long.MIN_VALUE ^ PtBytes.toLong(__input, __index);
                     __index += 8;
-                    return of(value);
+                    return Index3IdxRow.of(value);
                 }
             };
 
@@ -2273,7 +2291,7 @@ public final class DataTable implements
                     __index += EncodingUtils.sizeOfSizedBytes(rowName);
                     byte[] columnName = EncodingUtils.decodeSizedBytes(__input, __index);
                     __index += EncodingUtils.sizeOfSizedBytes(columnName);
-                    return of(rowName, columnName);
+                    return Index3IdxColumn.of(rowName, columnName);
                 }
             };
 
@@ -2719,6 +2737,10 @@ public final class DataTable implements
             this.namespace = namespace;
         }
 
+        public static String getRawTableName() {
+            return rawTableName;
+        }
+
         public String getTableName() {
             return tableName;
         }
@@ -2789,7 +2811,7 @@ public final class DataTable implements
                     __index += 8;
                     Long value2 = Long.MIN_VALUE ^ PtBytes.toLong(__input, __index);
                     __index += 8;
-                    return of(value1, value2);
+                    return Index4IdxRow.of(value1, value2);
                 }
             };
 
@@ -2902,7 +2924,7 @@ public final class DataTable implements
                     __index += EncodingUtils.sizeOfSizedBytes(rowName);
                     byte[] columnName = EncodingUtils.decodeSizedBytes(__input, __index);
                     __index += EncodingUtils.sizeOfSizedBytes(columnName);
-                    return of(rowName, columnName);
+                    return Index4IdxColumn.of(rowName, columnName);
                 }
             };
 
@@ -3318,5 +3340,5 @@ public final class DataTable implements
     }
 
 
-    static String __CLASS_HASH = "ViVjKvmt8daAep18q7KtJQ==";
+    static String __CLASS_HASH = "4tqSV0ccERqprZI28T6I0w==";
 }
diff --git a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/indexing/generated/TwoColumnsTable.java b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/indexing/generated/TwoColumnsTable.java
index b77878b..a558e38 100644
--- a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/indexing/generated/TwoColumnsTable.java
+++ b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/indexing/generated/TwoColumnsTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -112,6 +114,10 @@ public final class TwoColumnsTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -155,7 +161,7 @@ public final class TwoColumnsTable implements
             return new Function<Long, TwoColumnsRow>() {
                 @Override
                 public TwoColumnsRow apply(Long row) {
-                    return new TwoColumnsRow(row);
+                    return TwoColumnsRow.of(row);
                 }
             };
         }
@@ -172,7 +178,7 @@ public final class TwoColumnsTable implements
                 int __index = 0;
                 Long id = Long.MIN_VALUE ^ PtBytes.toLong(__input, __index);
                 __index += 8;
-                return of(id);
+                return TwoColumnsRow.of(id);
             }
         };
 
@@ -884,6 +890,10 @@ public final class TwoColumnsTable implements
             this.namespace = namespace;
         }
 
+        public static String getRawTableName() {
+            return rawTableName;
+        }
+
         public String getTableName() {
             return tableName;
         }
@@ -927,7 +937,7 @@ public final class TwoColumnsTable implements
                 return new Function<Long, FooToIdCondIdxRow>() {
                     @Override
                     public FooToIdCondIdxRow apply(Long row) {
-                        return new FooToIdCondIdxRow(row);
+                        return FooToIdCondIdxRow.of(row);
                     }
                 };
             }
@@ -944,7 +954,7 @@ public final class TwoColumnsTable implements
                     int __index = 0;
                     Long foo = Long.MIN_VALUE ^ PtBytes.toLong(__input, __index);
                     __index += 8;
-                    return of(foo);
+                    return FooToIdCondIdxRow.of(foo);
                 }
             };
 
@@ -1064,7 +1074,7 @@ public final class TwoColumnsTable implements
                     __index += EncodingUtils.sizeOfSizedBytes(columnName);
                     Long id = Long.MIN_VALUE ^ PtBytes.toLong(__input, __index);
                     __index += 8;
-                    return of(rowName, columnName, id);
+                    return FooToIdCondIdxColumn.of(rowName, columnName, id);
                 }
             };
 
@@ -1479,6 +1489,10 @@ public final class TwoColumnsTable implements
             this.namespace = namespace;
         }
 
+        public static String getRawTableName() {
+            return rawTableName;
+        }
+
         public String getTableName() {
             return tableName;
         }
@@ -1522,7 +1536,7 @@ public final class TwoColumnsTable implements
                 return new Function<Long, FooToIdIdxRow>() {
                     @Override
                     public FooToIdIdxRow apply(Long row) {
-                        return new FooToIdIdxRow(row);
+                        return FooToIdIdxRow.of(row);
                     }
                 };
             }
@@ -1539,7 +1553,7 @@ public final class TwoColumnsTable implements
                     int __index = 0;
                     Long foo = Long.MIN_VALUE ^ PtBytes.toLong(__input, __index);
                     __index += 8;
-                    return of(foo);
+                    return FooToIdIdxRow.of(foo);
                 }
             };
 
@@ -1659,7 +1673,7 @@ public final class TwoColumnsTable implements
                     __index += EncodingUtils.sizeOfSizedBytes(columnName);
                     Long id = Long.MIN_VALUE ^ PtBytes.toLong(__input, __index);
                     __index += 8;
-                    return of(rowName, columnName, id);
+                    return FooToIdIdxColumn.of(rowName, columnName, id);
                 }
             };
 
@@ -2044,5 +2058,5 @@ public final class TwoColumnsTable implements
     }
 
 
-    static String __CLASS_HASH = "kMLWwWC3cSKEaC03d7jn8g==";
+    static String __CLASS_HASH = "mGHb1bQ4clRh4woUn89ZUw==";
 }
diff --git a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTest2StreamHashAidxTable.java b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTest2StreamHashAidxTable.java
index 53eafcb..ba1b11f 100644
--- a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTest2StreamHashAidxTable.java
+++ b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTest2StreamHashAidxTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -110,6 +112,10 @@ public final class StreamTest2StreamHashAidxTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -153,7 +159,7 @@ public final class StreamTest2StreamHashAidxTable implements
             return new Function<Sha256Hash, StreamTest2StreamHashAidxRow>() {
                 @Override
                 public StreamTest2StreamHashAidxRow apply(Sha256Hash row) {
-                    return new StreamTest2StreamHashAidxRow(row);
+                    return StreamTest2StreamHashAidxRow.of(row);
                 }
             };
         }
@@ -170,7 +176,7 @@ public final class StreamTest2StreamHashAidxTable implements
                 int __index = 0;
                 Sha256Hash hash = new Sha256Hash(EncodingUtils.get32Bytes(__input, __index));
                 __index += 32;
-                return of(hash);
+                return StreamTest2StreamHashAidxRow.of(hash);
             }
         };
 
@@ -244,7 +250,7 @@ public final class StreamTest2StreamHashAidxTable implements
             return new Function<Long, StreamTest2StreamHashAidxColumn>() {
                 @Override
                 public StreamTest2StreamHashAidxColumn apply(Long row) {
-                    return new StreamTest2StreamHashAidxColumn(row);
+                    return StreamTest2StreamHashAidxColumn.of(row);
                 }
             };
         }
@@ -261,7 +267,7 @@ public final class StreamTest2StreamHashAidxTable implements
                 int __index = 0;
                 Long streamId = EncodingUtils.decodeUnsignedVarLong(__input, __index);
                 __index += EncodingUtils.sizeOfUnsignedVarLong(streamId);
-                return of(streamId);
+                return StreamTest2StreamHashAidxColumn.of(streamId);
             }
         };
 
@@ -627,5 +633,5 @@ public final class StreamTest2StreamHashAidxTable implements
         return ImmutableList.of();
     }
 
-    static String __CLASS_HASH = "0OgTnSLpmih4DnPo8ghp/Q==";
+    static String __CLASS_HASH = "W121mr5e+JMpHnnQg6bu2g==";
 }
diff --git a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTest2StreamIdxTable.java b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTest2StreamIdxTable.java
index a153696..6dfdd63 100644
--- a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTest2StreamIdxTable.java
+++ b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTest2StreamIdxTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -110,6 +112,10 @@ public final class StreamTest2StreamIdxTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -153,7 +159,7 @@ public final class StreamTest2StreamIdxTable implements
             return new Function<Long, StreamTest2StreamIdxRow>() {
                 @Override
                 public StreamTest2StreamIdxRow apply(Long row) {
-                    return new StreamTest2StreamIdxRow(row);
+                    return StreamTest2StreamIdxRow.of(row);
                 }
             };
         }
@@ -170,7 +176,7 @@ public final class StreamTest2StreamIdxTable implements
                 int __index = 0;
                 Long id = EncodingUtils.decodeUnsignedVarLong(__input, __index);
                 __index += EncodingUtils.sizeOfUnsignedVarLong(id);
-                return of(id);
+                return StreamTest2StreamIdxRow.of(id);
             }
         };
 
@@ -244,7 +250,7 @@ public final class StreamTest2StreamIdxTable implements
             return new Function<byte[], StreamTest2StreamIdxColumn>() {
                 @Override
                 public StreamTest2StreamIdxColumn apply(byte[] row) {
-                    return new StreamTest2StreamIdxColumn(row);
+                    return StreamTest2StreamIdxColumn.of(row);
                 }
             };
         }
@@ -261,7 +267,7 @@ public final class StreamTest2StreamIdxTable implements
                 int __index = 0;
                 byte[] reference = EncodingUtils.decodeSizedBytes(__input, __index);
                 __index += EncodingUtils.sizeOfSizedBytes(reference);
-                return of(reference);
+                return StreamTest2StreamIdxColumn.of(reference);
             }
         };
 
@@ -627,5 +633,5 @@ public final class StreamTest2StreamIdxTable implements
         return ImmutableList.of();
     }
 
-    static String __CLASS_HASH = "r3tF3jEKRR9S5Xq5PhdvqQ==";
+    static String __CLASS_HASH = "Ck2Qs2dX6qUs5zoGiBS1hg==";
 }
diff --git a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTest2StreamMetadataTable.java b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTest2StreamMetadataTable.java
index e32ede4..5e6f805 100644
--- a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTest2StreamMetadataTable.java
+++ b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTest2StreamMetadataTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -112,6 +114,10 @@ public final class StreamTest2StreamMetadataTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -155,7 +161,7 @@ public final class StreamTest2StreamMetadataTable implements
             return new Function<Long, StreamTest2StreamMetadataRow>() {
                 @Override
                 public StreamTest2StreamMetadataRow apply(Long row) {
-                    return new StreamTest2StreamMetadataRow(row);
+                    return StreamTest2StreamMetadataRow.of(row);
                 }
             };
         }
@@ -172,7 +178,7 @@ public final class StreamTest2StreamMetadataTable implements
                 int __index = 0;
                 Long id = EncodingUtils.decodeUnsignedVarLong(__input, __index);
                 __index += EncodingUtils.sizeOfUnsignedVarLong(id);
-                return of(id);
+                return StreamTest2StreamMetadataRow.of(id);
             }
         };
 
@@ -619,5 +625,5 @@ public final class StreamTest2StreamMetadataTable implements
         return ImmutableList.of();
     }
 
-    static String __CLASS_HASH = "fJBmiJ2sxoo1v7Ly5ln0Mw==";
+    static String __CLASS_HASH = "TUNZE4ZSNvSNzD06D+jmQw==";
 }
diff --git a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTest2StreamValueTable.java b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTest2StreamValueTable.java
index 47fb8cb..7e36c53 100644
--- a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTest2StreamValueTable.java
+++ b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTest2StreamValueTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -112,6 +114,10 @@ public final class StreamTest2StreamValueTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -182,7 +188,7 @@ public final class StreamTest2StreamValueTable implements
                 __index += EncodingUtils.sizeOfUnsignedVarLong(id);
                 Long blockId = EncodingUtils.decodeUnsignedVarLong(__input, __index);
                 __index += EncodingUtils.sizeOfUnsignedVarLong(blockId);
-                return of(id, blockId);
+                return StreamTest2StreamValueRow.of(id, blockId);
             }
         };
 
@@ -607,5 +613,5 @@ public final class StreamTest2StreamValueTable implements
         return ImmutableList.of();
     }
 
-    static String __CLASS_HASH = "Pk68Ul1AOtPwEWK2UUMRfQ==";
+    static String __CLASS_HASH = "SKdt7KcvFY6cvVwEHKlhHg==";
 }
diff --git a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTestStreamHashAidxTable.java b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTestStreamHashAidxTable.java
index aabb3cf..57d7943 100644
--- a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTestStreamHashAidxTable.java
+++ b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTestStreamHashAidxTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -110,6 +112,10 @@ public final class StreamTestStreamHashAidxTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -153,7 +159,7 @@ public final class StreamTestStreamHashAidxTable implements
             return new Function<Sha256Hash, StreamTestStreamHashAidxRow>() {
                 @Override
                 public StreamTestStreamHashAidxRow apply(Sha256Hash row) {
-                    return new StreamTestStreamHashAidxRow(row);
+                    return StreamTestStreamHashAidxRow.of(row);
                 }
             };
         }
@@ -170,7 +176,7 @@ public final class StreamTestStreamHashAidxTable implements
                 int __index = 0;
                 Sha256Hash hash = new Sha256Hash(EncodingUtils.get32Bytes(__input, __index));
                 __index += 32;
-                return of(hash);
+                return StreamTestStreamHashAidxRow.of(hash);
             }
         };
 
@@ -244,7 +250,7 @@ public final class StreamTestStreamHashAidxTable implements
             return new Function<Long, StreamTestStreamHashAidxColumn>() {
                 @Override
                 public StreamTestStreamHashAidxColumn apply(Long row) {
-                    return new StreamTestStreamHashAidxColumn(row);
+                    return StreamTestStreamHashAidxColumn.of(row);
                 }
             };
         }
@@ -261,7 +267,7 @@ public final class StreamTestStreamHashAidxTable implements
                 int __index = 0;
                 Long streamId = EncodingUtils.decodeUnsignedVarLong(__input, __index);
                 __index += EncodingUtils.sizeOfUnsignedVarLong(streamId);
-                return of(streamId);
+                return StreamTestStreamHashAidxColumn.of(streamId);
             }
         };
 
@@ -638,5 +644,5 @@ public final class StreamTestStreamHashAidxTable implements
         return ImmutableList.of();
     }
 
-    static String __CLASS_HASH = "00Nxg4Alo0a4ZK8htn6eBg==";
+    static String __CLASS_HASH = "7FANJ9if509kjpmioCtNeA==";
 }
diff --git a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTestStreamIdxTable.java b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTestStreamIdxTable.java
index 552a21f..0f6edc1 100644
--- a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTestStreamIdxTable.java
+++ b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTestStreamIdxTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -110,6 +112,10 @@ public final class StreamTestStreamIdxTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -153,7 +159,7 @@ public final class StreamTestStreamIdxTable implements
             return new Function<Long, StreamTestStreamIdxRow>() {
                 @Override
                 public StreamTestStreamIdxRow apply(Long row) {
-                    return new StreamTestStreamIdxRow(row);
+                    return StreamTestStreamIdxRow.of(row);
                 }
             };
         }
@@ -170,7 +176,7 @@ public final class StreamTestStreamIdxTable implements
                 int __index = 0;
                 Long id = EncodingUtils.decodeUnsignedVarLong(__input, __index);
                 __index += EncodingUtils.sizeOfUnsignedVarLong(id);
-                return of(id);
+                return StreamTestStreamIdxRow.of(id);
             }
         };
 
@@ -244,7 +250,7 @@ public final class StreamTestStreamIdxTable implements
             return new Function<byte[], StreamTestStreamIdxColumn>() {
                 @Override
                 public StreamTestStreamIdxColumn apply(byte[] row) {
-                    return new StreamTestStreamIdxColumn(row);
+                    return StreamTestStreamIdxColumn.of(row);
                 }
             };
         }
@@ -261,7 +267,7 @@ public final class StreamTestStreamIdxTable implements
                 int __index = 0;
                 byte[] reference = EncodingUtils.decodeSizedBytes(__input, __index);
                 __index += EncodingUtils.sizeOfSizedBytes(reference);
-                return of(reference);
+                return StreamTestStreamIdxColumn.of(reference);
             }
         };
 
@@ -638,5 +644,5 @@ public final class StreamTestStreamIdxTable implements
         return ImmutableList.of();
     }
 
-    static String __CLASS_HASH = "pzI7oPDyV1s0sBcm+7W/VA==";
+    static String __CLASS_HASH = "SYRz5JOcrd4Z1XvNIKuHuQ==";
 }
diff --git a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTestStreamMetadataTable.java b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTestStreamMetadataTable.java
index 830e870..afbeeb5 100644
--- a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTestStreamMetadataTable.java
+++ b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTestStreamMetadataTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -112,6 +114,10 @@ public final class StreamTestStreamMetadataTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -155,7 +161,7 @@ public final class StreamTestStreamMetadataTable implements
             return new Function<Long, StreamTestStreamMetadataRow>() {
                 @Override
                 public StreamTestStreamMetadataRow apply(Long row) {
-                    return new StreamTestStreamMetadataRow(row);
+                    return StreamTestStreamMetadataRow.of(row);
                 }
             };
         }
@@ -172,7 +178,7 @@ public final class StreamTestStreamMetadataTable implements
                 int __index = 0;
                 Long id = EncodingUtils.decodeUnsignedVarLong(__input, __index);
                 __index += EncodingUtils.sizeOfUnsignedVarLong(id);
-                return of(id);
+                return StreamTestStreamMetadataRow.of(id);
             }
         };
 
@@ -619,5 +625,5 @@ public final class StreamTestStreamMetadataTable implements
         return ImmutableList.of();
     }
 
-    static String __CLASS_HASH = "C45Plyjt0dfiIQ4C3UQR3Q==";
+    static String __CLASS_HASH = "MWCZ4YhPfWqKZdI9aFHFgQ==";
 }
diff --git a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTestStreamValueTable.java b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTestStreamValueTable.java
index c658070..497f912 100644
--- a/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTestStreamValueTable.java
+++ b/atlasdb-tests-shared/src/test/java/com/palantir/atlasdb/schema/stream/generated/StreamTestStreamValueTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -112,6 +114,10 @@ public final class StreamTestStreamValueTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -182,7 +188,7 @@ public final class StreamTestStreamValueTable implements
                 __index += EncodingUtils.sizeOfUnsignedVarLong(id);
                 Long blockId = EncodingUtils.decodeUnsignedVarLong(__input, __index);
                 __index += EncodingUtils.sizeOfUnsignedVarLong(blockId);
-                return of(id, blockId);
+                return StreamTestStreamValueRow.of(id, blockId);
             }
         };
 
@@ -607,5 +613,5 @@ public final class StreamTestStreamValueTable implements
         return ImmutableList.of();
     }
 
-    static String __CLASS_HASH = "O6Gqoqzbkbu03BQAR6rQtg==";
+    static String __CLASS_HASH = "XLLQ4TtXJ3NMYlSjBRx6uA==";
 }
diff --git a/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserPhotosStreamHashAidxTable.java b/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserPhotosStreamHashAidxTable.java
index d198b23..f7a64e9 100644
--- a/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserPhotosStreamHashAidxTable.java
+++ b/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserPhotosStreamHashAidxTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -110,6 +112,10 @@ public final class UserPhotosStreamHashAidxTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -153,7 +159,7 @@ public final class UserPhotosStreamHashAidxTable implements
             return new Function<Sha256Hash, UserPhotosStreamHashAidxRow>() {
                 @Override
                 public UserPhotosStreamHashAidxRow apply(Sha256Hash row) {
-                    return new UserPhotosStreamHashAidxRow(row);
+                    return UserPhotosStreamHashAidxRow.of(row);
                 }
             };
         }
@@ -170,7 +176,7 @@ public final class UserPhotosStreamHashAidxTable implements
                 int __index = 0;
                 Sha256Hash hash = new Sha256Hash(EncodingUtils.get32Bytes(__input, __index));
                 __index += 32;
-                return of(hash);
+                return UserPhotosStreamHashAidxRow.of(hash);
             }
         };
 
@@ -244,7 +250,7 @@ public final class UserPhotosStreamHashAidxTable implements
             return new Function<Long, UserPhotosStreamHashAidxColumn>() {
                 @Override
                 public UserPhotosStreamHashAidxColumn apply(Long row) {
-                    return new UserPhotosStreamHashAidxColumn(row);
+                    return UserPhotosStreamHashAidxColumn.of(row);
                 }
             };
         }
@@ -261,7 +267,7 @@ public final class UserPhotosStreamHashAidxTable implements
                 int __index = 0;
                 Long streamId = EncodingUtils.decodeUnsignedVarLong(__input, __index);
                 __index += EncodingUtils.sizeOfUnsignedVarLong(streamId);
-                return of(streamId);
+                return UserPhotosStreamHashAidxColumn.of(streamId);
             }
         };
 
@@ -638,5 +644,5 @@ public final class UserPhotosStreamHashAidxTable implements
         return ImmutableList.of();
     }
 
-    static String __CLASS_HASH = "jpT91S5GgRnuP8RoxhYGrQ==";
+    static String __CLASS_HASH = "NgWHlfSo6uZHx13edyG/qA==";
 }
diff --git a/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserPhotosStreamIdxTable.java b/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserPhotosStreamIdxTable.java
index 9d20120..34705ba 100644
--- a/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserPhotosStreamIdxTable.java
+++ b/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserPhotosStreamIdxTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -110,6 +112,10 @@ public final class UserPhotosStreamIdxTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -153,7 +159,7 @@ public final class UserPhotosStreamIdxTable implements
             return new Function<Long, UserPhotosStreamIdxRow>() {
                 @Override
                 public UserPhotosStreamIdxRow apply(Long row) {
-                    return new UserPhotosStreamIdxRow(row);
+                    return UserPhotosStreamIdxRow.of(row);
                 }
             };
         }
@@ -170,7 +176,7 @@ public final class UserPhotosStreamIdxTable implements
                 int __index = 0;
                 Long id = EncodingUtils.decodeUnsignedVarLong(__input, __index);
                 __index += EncodingUtils.sizeOfUnsignedVarLong(id);
-                return of(id);
+                return UserPhotosStreamIdxRow.of(id);
             }
         };
 
@@ -244,7 +250,7 @@ public final class UserPhotosStreamIdxTable implements
             return new Function<byte[], UserPhotosStreamIdxColumn>() {
                 @Override
                 public UserPhotosStreamIdxColumn apply(byte[] row) {
-                    return new UserPhotosStreamIdxColumn(row);
+                    return UserPhotosStreamIdxColumn.of(row);
                 }
             };
         }
@@ -261,7 +267,7 @@ public final class UserPhotosStreamIdxTable implements
                 int __index = 0;
                 byte[] reference = EncodingUtils.decodeSizedBytes(__input, __index);
                 __index += EncodingUtils.sizeOfSizedBytes(reference);
-                return of(reference);
+                return UserPhotosStreamIdxColumn.of(reference);
             }
         };
 
@@ -638,5 +644,5 @@ public final class UserPhotosStreamIdxTable implements
         return ImmutableList.of();
     }
 
-    static String __CLASS_HASH = "dsSxmLixkLYzQk/QvMaHwA==";
+    static String __CLASS_HASH = "Rn+HjDJ8Yr2SxCYp4J7IlQ==";
 }
diff --git a/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserPhotosStreamMetadataTable.java b/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserPhotosStreamMetadataTable.java
index 9463249..9c30e3e 100644
--- a/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserPhotosStreamMetadataTable.java
+++ b/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserPhotosStreamMetadataTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -112,6 +114,10 @@ public final class UserPhotosStreamMetadataTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -155,7 +161,7 @@ public final class UserPhotosStreamMetadataTable implements
             return new Function<Long, UserPhotosStreamMetadataRow>() {
                 @Override
                 public UserPhotosStreamMetadataRow apply(Long row) {
-                    return new UserPhotosStreamMetadataRow(row);
+                    return UserPhotosStreamMetadataRow.of(row);
                 }
             };
         }
@@ -172,7 +178,7 @@ public final class UserPhotosStreamMetadataTable implements
                 int __index = 0;
                 Long id = EncodingUtils.decodeUnsignedVarLong(__input, __index);
                 __index += EncodingUtils.sizeOfUnsignedVarLong(id);
-                return of(id);
+                return UserPhotosStreamMetadataRow.of(id);
             }
         };
 
@@ -619,5 +625,5 @@ public final class UserPhotosStreamMetadataTable implements
         return ImmutableList.of();
     }
 
-    static String __CLASS_HASH = "HlzM3MtaHjSyifYRNyv++A==";
+    static String __CLASS_HASH = "zNcjeszwItlnjkDopW5cBg==";
 }
diff --git a/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserPhotosStreamValueTable.java b/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserPhotosStreamValueTable.java
index d08f72b..484f0a6 100644
--- a/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserPhotosStreamValueTable.java
+++ b/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserPhotosStreamValueTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -112,6 +114,10 @@ public final class UserPhotosStreamValueTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -182,7 +188,7 @@ public final class UserPhotosStreamValueTable implements
                 __index += EncodingUtils.sizeOfUnsignedVarLong(id);
                 Long blockId = EncodingUtils.decodeUnsignedVarLong(__input, __index);
                 __index += EncodingUtils.sizeOfUnsignedVarLong(blockId);
-                return of(id, blockId);
+                return UserPhotosStreamValueRow.of(id, blockId);
             }
         };
 
@@ -607,5 +613,5 @@ public final class UserPhotosStreamValueTable implements
         return ImmutableList.of();
     }
 
-    static String __CLASS_HASH = "gg5sLq8r9HzlW4HkOJ2YyQ==";
+    static String __CLASS_HASH = "tjlODO2U7RJ1t2OB2ZGLvw==";
 }
diff --git a/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserProfileTable.java b/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserProfileTable.java
index b17b7ed..0ae12d0 100644
--- a/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserProfileTable.java
+++ b/examples/profile-client/src/main/java/com/palantir/example/profile/schema/generated/UserProfileTable.java
@@ -36,6 +36,7 @@ import com.google.common.collect.Maps;
 import com.google.common.collect.Multimap;
 import com.google.common.collect.Multimaps;
 import com.google.common.collect.Sets;
+import com.google.common.hash.Hashing;
 import com.google.common.primitives.Bytes;
 import com.google.common.primitives.UnsignedBytes;
 import com.google.protobuf.InvalidProtocolBufferException;
@@ -59,6 +60,7 @@ import com.palantir.atlasdb.table.api.AtlasDbNamedPersistentSet;
 import com.palantir.atlasdb.table.api.ColumnValue;
 import com.palantir.atlasdb.table.api.TypedRowResult;
 import com.palantir.atlasdb.table.description.ColumnValueDescription.Compression;
+import com.palantir.atlasdb.table.description.ValueType;
 import com.palantir.atlasdb.table.generation.ColumnValues;
 import com.palantir.atlasdb.table.generation.Descending;
 import com.palantir.atlasdb.table.generation.NamedColumnValue;
@@ -112,6 +114,10 @@ public final class UserProfileTable implements
         this.namespace = namespace;
     }
 
+    public static String getRawTableName() {
+        return rawTableName;
+    }
+
     public String getTableName() {
         return tableName;
     }
@@ -155,7 +161,7 @@ public final class UserProfileTable implements
             return new Function<Long, UserProfileRow>() {
                 @Override
                 public UserProfileRow apply(Long row) {
-                    return new UserProfileRow(row);
+                    return UserProfileRow.of(row);
                 }
             };
         }
@@ -172,7 +178,7 @@ public final class UserProfileTable implements
                 int __index = 0;
                 Long id = Long.MIN_VALUE ^ PtBytes.toLong(__input, __index);
                 __index += 8;
-                return of(id);
+                return UserProfileRow.of(id);
             }
         };
 
@@ -1233,6 +1239,10 @@ public final class UserProfileTable implements
             this.namespace = namespace;
         }
 
+        public static String getRawTableName() {
+            return rawTableName;
+        }
+
         public String getTableName() {
             return tableName;
         }
@@ -1276,7 +1286,7 @@ public final class UserProfileTable implements
                 return new Function<String, CookiesIdxRow>() {
                     @Override
                     public CookiesIdxRow apply(String row) {
-                        return new CookiesIdxRow(row);
+                        return CookiesIdxRow.of(row);
                     }
                 };
             }
@@ -1293,7 +1303,7 @@ public final class UserProfileTable implements
                     int __index = 0;
                     String cookie = PtBytes.toString(__input, __index, __input.length-__index);
                     __index += 0;
-                    return of(cookie);
+                    return CookiesIdxRow.of(cookie);
                 }
             };
 
@@ -1413,7 +1423,7 @@ public final class UserProfileTable implements
                     __index += EncodingUtils.sizeOfSizedBytes(columnName);
                     Long id = Long.MIN_VALUE ^ PtBytes.toLong(__input, __index);
                     __index += 8;
-                    return of(rowName, columnName, id);
+                    return CookiesIdxColumn.of(rowName, columnName, id);
                 }
             };
 
@@ -1862,6 +1872,10 @@ public final class UserProfileTable implements
             this.namespace = namespace;
         }
 
+        public static String getRawTableName() {
+            return rawTableName;
+        }
+
         public String getTableName() {
             return tableName;
         }
@@ -1905,7 +1919,7 @@ public final class UserProfileTable implements
                 return new Function<Long, CreatedIdxRow>() {
                     @Override
                     public CreatedIdxRow apply(Long row) {
-                        return new CreatedIdxRow(row);
+                        return CreatedIdxRow.of(row);
                     }
                 };
             }
@@ -1922,7 +1936,7 @@ public final class UserProfileTable implements
                     int __index = 0;
                     Long time = EncodingUtils.decodeUnsignedVarLong(__input, __index);
                     __index += EncodingUtils.sizeOfUnsignedVarLong(time);
-                    return of(time);
+                    return CreatedIdxRow.of(time);
                 }
             };
 
@@ -2042,7 +2056,7 @@ public final class UserProfileTable implements
                     __index += EncodingUtils.sizeOfSizedBytes(columnName);
                     Long id = Long.MIN_VALUE ^ PtBytes.toLong(__input, __index);
                     __index += 8;
-                    return of(rowName, columnName, id);
+                    return CreatedIdxColumn.of(rowName, columnName, id);
                 }
             };
 
@@ -2491,6 +2505,10 @@ public final class UserProfileTable implements
             this.namespace = namespace;
         }
 
+        public static String getRawTableName() {
+            return rawTableName;
+        }
+
         public String getTableName() {
             return tableName;
         }
@@ -2534,7 +2552,7 @@ public final class UserProfileTable implements
                 return new Function<Long, UserBirthdaysIdxRow>() {
                     @Override
                     public UserBirthdaysIdxRow apply(Long row) {
-                        return new UserBirthdaysIdxRow(row);
+                        return UserBirthdaysIdxRow.of(row);
                     }
                 };
             }
@@ -2551,7 +2569,7 @@ public final class UserProfileTable implements
                     int __index = 0;
                     Long birthday = EncodingUtils.decodeSignedVarLong(__input, __index);
                     __index += EncodingUtils.sizeOfSignedVarLong(birthday);
-                    return of(birthday);
+                    return UserBirthdaysIdxRow.of(birthday);
                 }
             };
 
@@ -2671,7 +2689,7 @@ public final class UserProfileTable implements
                     __index += EncodingUtils.sizeOfSizedBytes(columnName);
                     Long id = Long.MIN_VALUE ^ PtBytes.toLong(__input, __index);
                     __index += 8;
-                    return of(rowName, columnName, id);
+                    return UserBirthdaysIdxColumn.of(rowName, columnName, id);
                 }
             };
 
@@ -3090,5 +3108,5 @@ public final class UserProfileTable implements
     }
 
 
-    static String __CLASS_HASH = "sEC6/UzxLgVG3xSPImRzNQ==";
+    static String __CLASS_HASH = "/oKfTLHzGrnOXiqT9ItdbA==";
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
