This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: f09c02aa839edd46ba7e3f76271871fe24c090bb
- Commit message: Add block/position convention to all distinct from operators

This commit adds a second implementation to distinct from operator of all
types. This 2nd implementation uses block/position convention. As a
result, for certain types, it's no longer necessary to extract the value
out of the Block in order to invoke "distinct from" operator. This is
expected to resolve performance issue.
- Diff:
```
commit f09c02aa839edd46ba7e3f76271871fe24c090bb
Author: Gerlou Shyy <gerloushyy@gmail.com>
Date:   Mon Aug 13 15:47:02 2018 -0700

    Add block/position convention to all distinct from operators
    
    This commit adds a second implementation to distinct from operator of all
    types. This 2nd implementation uses block/position convention. As a
    result, for certain types, it's no longer necessary to extract the value
    out of the Block in order to invoke "distinct from" operator. This is
    expected to resolve performance issue.
---
 .../facebook/presto/metadata/FunctionRegistry.java | 21 ++++++++
 .../operator/scalar/ArrayDistinctFromOperator.java | 53 ++++++++++++--------
 .../presto/operator/scalar/JsonOperators.java      | 41 +++++++++++++---
 .../operator/scalar/MapDistinctFromOperator.java   | 52 ++++++++++++--------
 .../operator/scalar/RowDistinctFromOperator.java   | 30 ++++++++++--
 .../com/facebook/presto/type/BigintOperators.java  | 45 ++++++++++++-----
 .../com/facebook/presto/type/BooleanOperators.java | 47 +++++++++++++-----
 .../com/facebook/presto/type/CharOperators.java    | 53 +++++++++++++++-----
 .../com/facebook/presto/type/ColorOperators.java   | 45 ++++++++++++-----
 .../com/facebook/presto/type/DateOperators.java    | 47 +++++++++++++-----
 .../com/facebook/presto/type/DoubleOperators.java  | 56 ++++++++++++++++------
 .../com/facebook/presto/type/IntegerOperators.java | 45 ++++++++++++-----
 .../presto/type/IntervalDayTimeOperators.java      | 47 +++++++++++++-----
 .../presto/type/IntervalYearMonthOperators.java    | 47 +++++++++++++-----
 .../facebook/presto/type/IpAddressOperators.java   | 47 +++++++++++++-----
 .../com/facebook/presto/type/RealOperators.java    | 55 ++++++++++++++-------
 .../facebook/presto/type/SmallintOperators.java    | 45 ++++++++++++-----
 .../com/facebook/presto/type/TimeOperators.java    | 47 +++++++++++++-----
 .../presto/type/TimeWithTimeZoneOperators.java     | 47 +++++++++++++-----
 .../facebook/presto/type/TimestampOperators.java   | 45 ++++++++++++-----
 .../type/TimestampWithTimeZoneOperators.java       | 47 +++++++++++++-----
 .../com/facebook/presto/type/TinyintOperators.java | 45 ++++++++++++-----
 .../com/facebook/presto/type/UnknownOperators.java | 30 +++++++++---
 .../facebook/presto/type/VarbinaryOperators.java   | 50 ++++++++++++++-----
 .../com/facebook/presto/type/VarcharOperators.java | 53 +++++++++++++++-----
 .../facebook/presto/type/TestArrayOperators.java   |  6 +++
 .../facebook/presto/type/TestDecimalOperators.java |  8 ++++
 27 files changed, 867 insertions(+), 287 deletions(-)

diff --git a/presto-main/src/main/java/com/facebook/presto/metadata/FunctionRegistry.java b/presto-main/src/main/java/com/facebook/presto/metadata/FunctionRegistry.java
index 1d35efed3a..4a64595293 100644
--- a/presto-main/src/main/java/com/facebook/presto/metadata/FunctionRegistry.java
+++ b/presto-main/src/main/java/com/facebook/presto/metadata/FunctionRegistry.java
@@ -490,29 +490,48 @@ public class FunctionRegistry
                 .scalars(JsonFunctions.class)
                 .scalars(ColorFunctions.class)
                 .scalars(ColorOperators.class)
+                .scalar(ColorOperators.ColorDistinctFromOperator.class)
                 .scalars(HyperLogLogFunctions.class)
                 .scalars(QuantileDigestFunctions.class)
                 .scalars(UnknownOperators.class)
+                .scalar(UnknownOperators.UnknownDistinctFromOperator.class)
                 .scalars(BooleanOperators.class)
+                .scalar(BooleanOperators.BooleanDistinctFromOperator.class)
                 .scalars(BigintOperators.class)
+                .scalar(BigintOperators.BigintDistinctFromOperator.class)
                 .scalars(IntegerOperators.class)
+                .scalar(IntegerOperators.IntegerDistinctFromOperator.class)
                 .scalars(SmallintOperators.class)
+                .scalar(SmallintOperators.SmallintDistinctFromOperator.class)
                 .scalars(TinyintOperators.class)
+                .scalar(TinyintOperators.TinyintDistinctFromOperator.class)
                 .scalars(DoubleOperators.class)
+                .scalar(DoubleOperators.DoubleDistinctFromOperator.class)
                 .scalars(RealOperators.class)
+                .scalar(RealOperators.RealDistinctFromOperator.class)
                 .scalars(VarcharOperators.class)
+                .scalar(VarcharOperators.VarcharDistinctFromOperator.class)
                 .scalars(VarbinaryOperators.class)
+                .scalar(VarbinaryOperators.VarbinaryDistinctFromOperator.class)
                 .scalars(DateOperators.class)
+                .scalar(DateOperators.DateDistinctFromOperator.class)
                 .scalars(TimeOperators.class)
+                .scalar(TimeOperators.TimeDistinctFromOperator.class)
                 .scalars(TimestampOperators.class)
+                .scalar(TimestampOperators.TimestampDistinctFromOperator.class)
                 .scalars(IntervalDayTimeOperators.class)
+                .scalar(IntervalDayTimeOperators.IntervalDayTimeDistinctFromOperator.class)
                 .scalars(IntervalYearMonthOperators.class)
+                .scalar(IntervalYearMonthOperators.IntervalYearMonthDistinctFromOperator.class)
                 .scalars(TimeWithTimeZoneOperators.class)
+                .scalar(TimeWithTimeZoneOperators.TimeWithTimeZoneDistinctFromOperator.class)
                 .scalars(TimestampWithTimeZoneOperators.class)
+                .scalar(TimestampWithTimeZoneOperators.TimestampWithTimeZoneDistinctFromOperator.class)
                 .scalars(DateTimeOperators.class)
                 .scalars(HyperLogLogOperators.class)
                 .scalars(QuantileDigestOperators.class)
                 .scalars(IpAddressOperators.class)
+                .scalar(IpAddressOperators.IpAddressDistinctFromOperator.class)
                 .scalars(LikeFunctions.class)
                 .scalars(ArrayFunctions.class)
                 .scalars(HmacFunctions.class)
@@ -523,10 +542,12 @@ public class FunctionRegistry
                 .scalar(ArrayPositionFunction.class)
                 .scalars(CombineHashFunction.class)
                 .scalars(JsonOperators.class)
+                .scalar(JsonOperators.JsonDistinctFromOperator.class)
                 .scalars(FailureFunction.class)
                 .scalars(JoniRegexpCasts.class)
                 .scalars(CharacterStringCasts.class)
                 .scalars(CharOperators.class)
+                .scalar(CharOperators.CharDistinctFromOperator.class)
                 .scalar(DecimalOperators.Negation.class)
                 .scalar(DecimalOperators.HashCode.class)
                 .scalar(DecimalOperators.Indeterminate.class)
diff --git a/presto-main/src/main/java/com/facebook/presto/operator/scalar/ArrayDistinctFromOperator.java b/presto-main/src/main/java/com/facebook/presto/operator/scalar/ArrayDistinctFromOperator.java
index e7bae8619e..99ae365bfa 100644
--- a/presto-main/src/main/java/com/facebook/presto/operator/scalar/ArrayDistinctFromOperator.java
+++ b/presto-main/src/main/java/com/facebook/presto/operator/scalar/ArrayDistinctFromOperator.java
@@ -14,6 +14,8 @@ package com.facebook.presto.operator.scalar;
  */
 
 import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.Convention;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.OperatorDependency;
@@ -25,12 +27,10 @@ import com.facebook.presto.spi.type.Type;
 
 import java.lang.invoke.MethodHandle;
 
-import static com.facebook.presto.spi.function.InvocationConvention.InvocationArgumentConvention.NULL_FLAG;
+import static com.facebook.presto.spi.function.InvocationConvention.InvocationArgumentConvention.BLOCK_POSITION;
 import static com.facebook.presto.spi.function.InvocationConvention.InvocationReturnConvention.FAIL_ON_NULL;
 import static com.facebook.presto.spi.function.OperatorType.IS_DISTINCT_FROM;
-import static com.facebook.presto.spi.type.TypeUtils.readNativeValue;
 import static com.facebook.presto.util.Failures.internalError;
-import static com.google.common.base.Defaults.defaultValue;
 
 @ScalarOperator(IS_DISTINCT_FROM)
 public final class ArrayDistinctFromOperator
@@ -44,8 +44,8 @@ public final class ArrayDistinctFromOperator
                     operator = IS_DISTINCT_FROM,
                     returnType = StandardTypes.BOOLEAN,
                     argumentTypes = {"E", "E"},
-                    convention = @Convention(arguments = {NULL_FLAG, NULL_FLAG}, result = FAIL_ON_NULL)) MethodHandle function,
-            @TypeParameter("E") Type type,
+                    convention = @Convention(arguments = {BLOCK_POSITION, BLOCK_POSITION}, result = FAIL_ON_NULL)) MethodHandle function,
+            @TypeParameter("array(E)") Type type,
             @SqlType("array(E)") Block left,
             @IsNull boolean leftNull,
             @SqlType("array(E)") Block right,
@@ -61,22 +61,12 @@ public final class ArrayDistinctFromOperator
             return true;
         }
         for (int i = 0; i < left.getPositionCount(); i++) {
-            Object leftValue = readNativeValue(type, left, i);
-            boolean leftValueNull = leftValue == null;
-            if (leftValueNull) {
-                leftValue = defaultValue(type.getJavaType());
-            }
-            Object rightValue = readNativeValue(type, right, i);
-            boolean rightValueNull = rightValue == null;
-            if (rightValueNull) {
-                rightValue = defaultValue(type.getJavaType());
-            }
             try {
-                if ((boolean) function.invoke(
-                        leftValue,
-                        leftValueNull,
-                        rightValue,
-                        rightValueNull)) {
+                if ((boolean) function.invokeExact(
+                        left,
+                        i,
+                        right,
+                        i)) {
                     return true;
                 }
             }
@@ -86,4 +76,27 @@ public final class ArrayDistinctFromOperator
         }
         return false;
     }
+
+    @TypeParameter("E")
+    @SqlType(StandardTypes.BOOLEAN)
+    public static boolean isDistinctFrom(
+            @OperatorDependency(
+                    operator = IS_DISTINCT_FROM,
+                    returnType = StandardTypes.BOOLEAN,
+                    argumentTypes = {"E", "E"},
+                    convention = @Convention(arguments = {BLOCK_POSITION, BLOCK_POSITION}, result = FAIL_ON_NULL)) MethodHandle elementIsDistinctFrom,
+            @TypeParameter("array(E)") Type type,
+            @BlockPosition @SqlType(value = "array(E)", nativeContainerType = Block.class) Block left,
+            @BlockIndex int leftPosition,
+            @BlockPosition @SqlType(value = "array(E)", nativeContainerType = Block.class) Block right,
+            @BlockIndex int rightPosition)
+    {
+        return isDistinctFrom(
+                elementIsDistinctFrom,
+                type,
+                (Block) type.getObject(left, leftPosition),
+                left.isNull(leftPosition),
+                (Block) type.getObject(right, rightPosition),
+                right.isNull(rightPosition));
+    }
 }
diff --git a/presto-main/src/main/java/com/facebook/presto/operator/scalar/JsonOperators.java b/presto-main/src/main/java/com/facebook/presto/operator/scalar/JsonOperators.java
index a1c15a34ea..0d41b08af3 100644
--- a/presto-main/src/main/java/com/facebook/presto/operator/scalar/JsonOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/operator/scalar/JsonOperators.java
@@ -15,6 +15,9 @@ package com.facebook.presto.operator.scalar;
 
 import com.facebook.presto.spi.ConnectorSession;
 import com.facebook.presto.spi.PrestoException;
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarOperator;
@@ -391,15 +394,39 @@ public final class JsonOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(BOOLEAN)
-    public static boolean isDistinctFrom(@SqlType(JSON) Slice leftJson, @IsNull boolean leftNull, @SqlType(JSON) Slice rightJson, @IsNull boolean rightNull)
+    public static class JsonDistinctFromOperator
     {
-        if (leftNull != rightNull) {
-            return true;
+        @SqlType(BOOLEAN)
+        public static boolean isDistinctFrom(@SqlType(JSON) Slice leftJson, @IsNull boolean leftNull, @SqlType(JSON) Slice rightJson, @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(leftJson, rightJson);
         }
-        if (leftNull) {
-            return false;
+
+        @SqlType(BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = JSON, nativeContainerType = Slice.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = JSON, nativeContainerType = Slice.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+            int leftLength = left.getSliceLength(leftPosition);
+            int rightLength = right.getSliceLength(rightPosition);
+            if (leftLength != rightLength) {
+                return true;
+            }
+            return !left.equals(leftPosition, 0, right, rightPosition, 0, leftLength);
         }
-        return notEqual(leftJson, rightJson);
     }
 }
diff --git a/presto-main/src/main/java/com/facebook/presto/operator/scalar/MapDistinctFromOperator.java b/presto-main/src/main/java/com/facebook/presto/operator/scalar/MapDistinctFromOperator.java
index 1174446d33..85da781a7d 100644
--- a/presto-main/src/main/java/com/facebook/presto/operator/scalar/MapDistinctFromOperator.java
+++ b/presto-main/src/main/java/com/facebook/presto/operator/scalar/MapDistinctFromOperator.java
@@ -14,20 +14,23 @@ package com.facebook.presto.operator.scalar;
  */
 
 import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
+import com.facebook.presto.spi.function.Convention;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.OperatorDependency;
 import com.facebook.presto.spi.function.ScalarOperator;
 import com.facebook.presto.spi.function.SqlType;
 import com.facebook.presto.spi.function.TypeParameter;
+import com.facebook.presto.spi.type.MapType;
 import com.facebook.presto.spi.type.StandardTypes;
 import com.facebook.presto.spi.type.Type;
 
 import java.lang.invoke.MethodHandle;
 
-import static com.facebook.presto.spi.function.OperatorType.EQUAL;
-import static com.facebook.presto.spi.function.OperatorType.HASH_CODE;
+import static com.facebook.presto.spi.function.InvocationConvention.InvocationArgumentConvention.BLOCK_POSITION;
+import static com.facebook.presto.spi.function.InvocationConvention.InvocationReturnConvention.FAIL_ON_NULL;
 import static com.facebook.presto.spi.function.OperatorType.IS_DISTINCT_FROM;
-import static com.facebook.presto.spi.type.TypeUtils.readNativeValue;
 
 @ScalarOperator(IS_DISTINCT_FROM)
 public final class MapDistinctFromOperator
@@ -38,14 +41,9 @@ public final class MapDistinctFromOperator
     @TypeParameter("V")
     @SqlType(StandardTypes.BOOLEAN)
     public static boolean isDistinctFrom(
-            @OperatorDependency(operator = EQUAL, returnType = StandardTypes.BOOLEAN, argumentTypes = {"K", "K"})
-                    MethodHandle keyEqualsFunction,
-            @OperatorDependency(operator = HASH_CODE, returnType = StandardTypes.BIGINT, argumentTypes = {"K"})
-                    MethodHandle keyHashcodeFunction,
-            @OperatorDependency(operator = IS_DISTINCT_FROM, returnType = StandardTypes.BOOLEAN, argumentTypes = {"V", "V"})
+            @OperatorDependency(operator = IS_DISTINCT_FROM, returnType = StandardTypes.BOOLEAN, argumentTypes = {"V", "V"}, convention = @Convention(arguments = {BLOCK_POSITION, BLOCK_POSITION}, result = FAIL_ON_NULL))
                     MethodHandle valueDistinctFromFunction,
-            @TypeParameter("K") Type keyType,
-            @TypeParameter("V") Type valueType,
+            @TypeParameter("map(K, V)") Type mapType,
             @SqlType("map(K,V)") Block leftMapBlock,
             @IsNull boolean leftMapNull,
             @SqlType("map(K,V)") Block rightMapBlock,
@@ -59,18 +57,30 @@ public final class MapDistinctFromOperator
         }
         // Note that we compare to NOT distinct here and so negate the result.
         return !MapGenericEquality.genericEqual(
-                keyType,
+                ((MapType) mapType).getKeyType(),
                 leftMapBlock,
                 rightMapBlock,
-                (leftMapIndex, rightMapIndex) -> {
-                    Object leftValue = readNativeValue(valueType, leftMapBlock, leftMapIndex);
-                    Object rightValue = readNativeValue(valueType, rightMapBlock, rightMapIndex);
-                    boolean leftNull = leftValue == null;
-                    boolean rightNull = rightValue == null;
-                    if (leftNull || rightNull) {
-                        return leftNull == rightNull;
-                    }
-                    return !(boolean) valueDistinctFromFunction.invoke(leftValue, leftNull, rightValue, rightNull);
-                });
+                (leftMapIndex, rightMapIndex) -> !(boolean) valueDistinctFromFunction.invokeExact(leftMapBlock, leftMapIndex, rightMapBlock, rightMapIndex));
+    }
+
+    @TypeParameter("K")
+    @TypeParameter("V")
+    @SqlType(StandardTypes.BOOLEAN)
+    public static boolean isDistinctFrom(
+            @OperatorDependency(operator = IS_DISTINCT_FROM, returnType = StandardTypes.BOOLEAN, argumentTypes = {"V", "V"}, convention = @Convention(arguments = {BLOCK_POSITION, BLOCK_POSITION}, result = FAIL_ON_NULL))
+                    MethodHandle valueDistinctFromFunction,
+            @TypeParameter("map(K, V)") Type mapType,
+            @BlockPosition @SqlType(value = "map(K,V)", nativeContainerType = Block.class) Block left,
+            @BlockIndex int leftPosition,
+            @BlockPosition @SqlType(value = "map(K,V)", nativeContainerType = Block.class) Block right,
+            @BlockIndex int rightPosition)
+    {
+        return isDistinctFrom(
+                valueDistinctFromFunction,
+                mapType,
+                (Block) mapType.getObject(left, leftPosition),
+                left.isNull(leftPosition),
+                (Block) mapType.getObject(right, rightPosition),
+                right.isNull(rightPosition));
     }
 }
diff --git a/presto-main/src/main/java/com/facebook/presto/operator/scalar/RowDistinctFromOperator.java b/presto-main/src/main/java/com/facebook/presto/operator/scalar/RowDistinctFromOperator.java
index 7306079f77..26b473829d 100644
--- a/presto-main/src/main/java/com/facebook/presto/operator/scalar/RowDistinctFromOperator.java
+++ b/presto-main/src/main/java/com/facebook/presto/operator/scalar/RowDistinctFromOperator.java
@@ -18,6 +18,7 @@ import com.facebook.presto.metadata.FunctionInvoker;
 import com.facebook.presto.metadata.FunctionRegistry;
 import com.facebook.presto.metadata.Signature;
 import com.facebook.presto.metadata.SqlOperator;
+import com.facebook.presto.operator.scalar.ScalarFunctionImplementation.ScalarImplementationChoice;
 import com.facebook.presto.spi.block.Block;
 import com.facebook.presto.spi.function.InvocationConvention;
 import com.facebook.presto.spi.type.StandardTypes;
@@ -31,6 +32,7 @@ import java.util.Optional;
 
 import static com.facebook.presto.metadata.Signature.comparableWithVariadicBound;
 import static com.facebook.presto.operator.scalar.ScalarFunctionImplementation.ArgumentProperty.valueTypeArgumentProperty;
+import static com.facebook.presto.operator.scalar.ScalarFunctionImplementation.NullConvention.BLOCK_AND_POSITION;
 import static com.facebook.presto.operator.scalar.ScalarFunctionImplementation.NullConvention.USE_NULL_FLAG;
 import static com.facebook.presto.spi.function.InvocationConvention.InvocationArgumentConvention.NULL_FLAG;
 import static com.facebook.presto.spi.function.OperatorType.IS_DISTINCT_FROM;
@@ -44,7 +46,8 @@ public class RowDistinctFromOperator
         extends SqlOperator
 {
     public static final RowDistinctFromOperator ROW_DISTINCT_FROM = new RowDistinctFromOperator();
-    private static final MethodHandle METHOD_HANDLE = methodHandle(RowDistinctFromOperator.class, "isDistinctFrom", Type.class, List.class, Block.class, boolean.class, Block.class, boolean.class);
+    private static final MethodHandle METHOD_HANDLE_NULL_FLAG = methodHandle(RowDistinctFromOperator.class, "isDistinctFrom", Type.class, List.class, Block.class, boolean.class, Block.class, boolean.class);
+    private static final MethodHandle METHOD_HANDLE_BLOCK_POSITION = methodHandle(RowDistinctFromOperator.class, "isDistinctFrom", Type.class, List.class, Block.class, int.class, Block.class, int.class);
 
     private RowDistinctFromOperator()
     {
@@ -71,11 +74,17 @@ public class RowDistinctFromOperator
             argumentMethods.add(functionInvoker.methodHandle());
         }
         return new ScalarFunctionImplementation(
-                false,
                 ImmutableList.of(
-                        valueTypeArgumentProperty(USE_NULL_FLAG),
-                        valueTypeArgumentProperty(USE_NULL_FLAG)),
-                METHOD_HANDLE.bindTo(type).bindTo(argumentMethods.build()),
+                        new ScalarImplementationChoice(
+                                false,
+                                ImmutableList.of(valueTypeArgumentProperty(USE_NULL_FLAG), valueTypeArgumentProperty(USE_NULL_FLAG)),
+                                METHOD_HANDLE_NULL_FLAG.bindTo(type).bindTo(argumentMethods.build()),
+                                Optional.empty()),
+                        new ScalarImplementationChoice(
+                                false,
+                                ImmutableList.of(valueTypeArgumentProperty(BLOCK_AND_POSITION), valueTypeArgumentProperty(BLOCK_AND_POSITION)),
+                                METHOD_HANDLE_BLOCK_POSITION.bindTo(type).bindTo(argumentMethods.build()),
+                                Optional.empty())),
                 isDeterministic());
     }
 
@@ -115,4 +124,15 @@ public class RowDistinctFromOperator
         }
         return false;
     }
+
+    public static boolean isDistinctFrom(Type rowType, List<MethodHandle> argumentMethods, Block leftRow, int leftPosition, Block rightRow, int rightPosition)
+    {
+        return isDistinctFrom(
+                rowType,
+                argumentMethods,
+                (Block) rowType.getObject(leftRow, leftPosition),
+                leftRow.isNull(leftPosition),
+                (Block) rowType.getObject(rightRow, rightPosition),
+                rightRow.isNull(rightPosition));
+    }
 }
diff --git a/presto-main/src/main/java/com/facebook/presto/type/BigintOperators.java b/presto-main/src/main/java/com/facebook/presto/type/BigintOperators.java
index c6706c7833..9195b5d3ba 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/BigintOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/BigintOperators.java
@@ -14,6 +14,9 @@
 package com.facebook.presto.type;
 
 import com.facebook.presto.spi.PrestoException;
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarOperator;
@@ -48,6 +51,7 @@ import static com.facebook.presto.spi.function.OperatorType.NOT_EQUAL;
 import static com.facebook.presto.spi.function.OperatorType.SATURATED_FLOOR_CAST;
 import static com.facebook.presto.spi.function.OperatorType.SUBTRACT;
 import static com.facebook.presto.spi.function.OperatorType.XX_HASH_64;
+import static com.facebook.presto.spi.type.BigintType.BIGINT;
 import static io.airlift.slice.Slices.utf8Slice;
 import static java.lang.Float.floatToRawIntBits;
 import static java.lang.Math.toIntExact;
@@ -280,20 +284,39 @@ public final class BigintOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(StandardTypes.BIGINT) long left,
-            @IsNull boolean leftNull,
-            @SqlType(StandardTypes.BIGINT) long right,
-            @IsNull boolean rightNull)
+    public static class BigintDistinctFromOperator
     {
-        if (leftNull != rightNull) {
-            return true;
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(StandardTypes.BIGINT) long left,
+                @IsNull boolean leftNull,
+                @SqlType(StandardTypes.BIGINT) long right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = StandardTypes.BIGINT, nativeContainerType = long.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = StandardTypes.BIGINT, nativeContainerType = long.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+            return notEqual(BIGINT.getLong(left, leftPosition), BIGINT.getLong(right, rightPosition));
         }
-        return notEqual(left, right);
     }
 
     @ScalarOperator(XX_HASH_64)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/BooleanOperators.java b/presto-main/src/main/java/com/facebook/presto/type/BooleanOperators.java
index b9c572c42d..e684186460 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/BooleanOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/BooleanOperators.java
@@ -13,6 +13,9 @@
  */
 package com.facebook.presto.type;
 
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarFunction;
@@ -34,6 +37,7 @@ import static com.facebook.presto.spi.function.OperatorType.IS_DISTINCT_FROM;
 import static com.facebook.presto.spi.function.OperatorType.LESS_THAN;
 import static com.facebook.presto.spi.function.OperatorType.LESS_THAN_OR_EQUAL;
 import static com.facebook.presto.spi.function.OperatorType.NOT_EQUAL;
+import static com.facebook.presto.spi.type.BooleanType.BOOLEAN;
 import static java.lang.Float.floatToRawIntBits;
 import static java.nio.charset.StandardCharsets.US_ASCII;
 
@@ -169,19 +173,38 @@ public final class BooleanOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(StandardTypes.BOOLEAN) boolean left,
-            @IsNull boolean leftNull,
-            @SqlType(StandardTypes.BOOLEAN) boolean right,
-            @IsNull boolean rightNull)
-    {
-        if (leftNull != rightNull) {
-            return true;
+    public static class BooleanDistinctFromOperator
+    {
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(StandardTypes.BOOLEAN) boolean left,
+                @IsNull boolean leftNull,
+                @SqlType(StandardTypes.BOOLEAN) boolean right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = StandardTypes.BOOLEAN, nativeContainerType = boolean.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = StandardTypes.BOOLEAN, nativeContainerType = boolean.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+            return notEqual(BOOLEAN.getBoolean(left, leftPosition), BOOLEAN.getBoolean(right, rightPosition));
         }
-        return notEqual(left, right);
     }
 }
diff --git a/presto-main/src/main/java/com/facebook/presto/type/CharOperators.java b/presto-main/src/main/java/com/facebook/presto/type/CharOperators.java
index ec64e2fddb..88a582752e 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/CharOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/CharOperators.java
@@ -13,6 +13,9 @@
  */
 package com.facebook.presto.type;
 
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarOperator;
@@ -113,22 +116,48 @@ public final class CharOperators
         return XxHash64.hash(slice);
     }
 
-    @LiteralParameters("x")
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType("char(x)") Slice left,
-            @IsNull boolean leftNull,
-            @SqlType("char(x)") Slice right,
-            @IsNull boolean rightNull)
+    public static class CharDistinctFromOperator
     {
-        if (leftNull != rightNull) {
-            return true;
+        @LiteralParameters("x")
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType("char(x)") Slice left,
+                @IsNull boolean leftNull,
+                @SqlType("char(x)") Slice right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @LiteralParameters("x")
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = "char(x)", nativeContainerType = Slice.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = "char(x)", nativeContainerType = Slice.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+
+            int leftLength = left.getSliceLength(leftPosition);
+            int rightLength = right.getSliceLength(rightPosition);
+            if (leftLength != rightLength) {
+                return true;
+            }
+            return !left.equals(leftPosition, 0, right, rightPosition, 0, leftLength);
         }
-        return notEqual(left, right);
     }
 
     @LiteralParameters("x")
diff --git a/presto-main/src/main/java/com/facebook/presto/type/ColorOperators.java b/presto-main/src/main/java/com/facebook/presto/type/ColorOperators.java
index b18e7cbc9b..2008888025 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/ColorOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/ColorOperators.java
@@ -13,6 +13,9 @@
  */
 package com.facebook.presto.type;
 
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.ScalarOperator;
 import com.facebook.presto.spi.function.SqlNullable;
@@ -24,6 +27,7 @@ import static com.facebook.presto.spi.function.OperatorType.HASH_CODE;
 import static com.facebook.presto.spi.function.OperatorType.INDETERMINATE;
 import static com.facebook.presto.spi.function.OperatorType.IS_DISTINCT_FROM;
 import static com.facebook.presto.spi.function.OperatorType.NOT_EQUAL;
+import static com.facebook.presto.type.ColorType.COLOR;
 
 public final class ColorOperators
 {
@@ -55,20 +59,39 @@ public final class ColorOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(ColorType.NAME) long left,
-            @IsNull boolean leftNull,
-            @SqlType(ColorType.NAME) long right,
-            @IsNull boolean rightNull)
+    public static class ColorDistinctFromOperator
     {
-        if (leftNull != rightNull) {
-            return true;
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(ColorType.NAME) long left,
+                @IsNull boolean leftNull,
+                @SqlType(ColorType.NAME) long right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = ColorType.NAME, nativeContainerType = long.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = ColorType.NAME, nativeContainerType = long.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+            return notEqual(COLOR.getLong(left, leftPosition), COLOR.getLong(right, rightPosition));
         }
-        return notEqual(left, right);
     }
 
     @ScalarOperator(INDETERMINATE)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/DateOperators.java b/presto-main/src/main/java/com/facebook/presto/type/DateOperators.java
index 170ad45585..253f2ee144 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/DateOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/DateOperators.java
@@ -15,6 +15,9 @@ package com.facebook.presto.type;
 
 import com.facebook.presto.spi.ConnectorSession;
 import com.facebook.presto.spi.PrestoException;
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarFunction;
@@ -43,6 +46,7 @@ import static com.facebook.presto.spi.function.OperatorType.LESS_THAN_OR_EQUAL;
 import static com.facebook.presto.spi.function.OperatorType.NOT_EQUAL;
 import static com.facebook.presto.spi.function.OperatorType.XX_HASH_64;
 import static com.facebook.presto.spi.type.DateTimeEncoding.packDateTimeWithZone;
+import static com.facebook.presto.spi.type.DateType.DATE;
 import static com.facebook.presto.util.DateTimeUtils.parseDate;
 import static com.facebook.presto.util.DateTimeUtils.printDate;
 import static com.facebook.presto.util.DateTimeZoneIndex.getChronology;
@@ -166,20 +170,39 @@ public final class DateOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(StandardTypes.DATE) long left,
-            @IsNull boolean leftNull,
-            @SqlType(StandardTypes.DATE) long right,
-            @IsNull boolean rightNull)
-    {
-        if (leftNull != rightNull) {
-            return true;
+    public static class DateDistinctFromOperator
+    {
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(StandardTypes.DATE) long left,
+                @IsNull boolean leftNull,
+                @SqlType(StandardTypes.DATE) long right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = StandardTypes.DATE, nativeContainerType = long.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = StandardTypes.DATE, nativeContainerType = long.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+            return notEqual(DATE.getLong(left, leftPosition), DATE.getLong(right, rightPosition));
         }
-        return notEqual(left, right);
     }
 
     @ScalarOperator(INDETERMINATE)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/DoubleOperators.java b/presto-main/src/main/java/com/facebook/presto/type/DoubleOperators.java
index da899bcfac..9bb6c1d1cd 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/DoubleOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/DoubleOperators.java
@@ -15,6 +15,9 @@ package com.facebook.presto.type;
 
 import com.facebook.presto.operator.scalar.MathFunctions;
 import com.facebook.presto.spi.PrestoException;
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarOperator;
@@ -50,6 +53,7 @@ import static com.facebook.presto.spi.function.OperatorType.NOT_EQUAL;
 import static com.facebook.presto.spi.function.OperatorType.SATURATED_FLOOR_CAST;
 import static com.facebook.presto.spi.function.OperatorType.SUBTRACT;
 import static com.facebook.presto.spi.function.OperatorType.XX_HASH_64;
+import static com.facebook.presto.spi.type.DoubleType.DOUBLE;
 import static com.google.common.base.Preconditions.checkState;
 import static io.airlift.slice.Slices.utf8Slice;
 import static java.lang.Double.doubleToLongBits;
@@ -318,23 +322,47 @@ public final class DoubleOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(StandardTypes.DOUBLE) double left,
-            @IsNull boolean leftNull,
-            @SqlType(StandardTypes.DOUBLE) double right,
-            @IsNull boolean rightNull)
+    public static class DoubleDistinctFromOperator
     {
-        if (leftNull != rightNull) {
-            return true;
-        }
-        if (leftNull) {
-            return false;
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(StandardTypes.DOUBLE) double left,
+                @IsNull boolean leftNull,
+                @SqlType(StandardTypes.DOUBLE) double right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            if (Double.isNaN(left) && Double.isNaN(right)) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (Double.isNaN(left) && Double.isNaN(right)) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = StandardTypes.DOUBLE, nativeContainerType = double.class) Block leftBlock,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = StandardTypes.DOUBLE, nativeContainerType = double.class) Block rightBlock,
+                @BlockIndex int rightPosition)
+        {
+            if (leftBlock.isNull(leftPosition) != rightBlock.isNull(rightPosition)) {
+                return true;
+            }
+            if (leftBlock.isNull(leftPosition)) {
+                return false;
+            }
+            double left = DOUBLE.getDouble(leftBlock, leftPosition);
+            double right = DOUBLE.getDouble(rightBlock, rightPosition);
+            if (Double.isNaN(left) && Double.isNaN(right)) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        return notEqual(left, right);
     }
 
     @ScalarOperator(XX_HASH_64)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/IntegerOperators.java b/presto-main/src/main/java/com/facebook/presto/type/IntegerOperators.java
index 73aaa1a577..5592502ce3 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/IntegerOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/IntegerOperators.java
@@ -14,6 +14,9 @@
 package com.facebook.presto.type;
 
 import com.facebook.presto.spi.PrestoException;
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarOperator;
@@ -47,6 +50,7 @@ import static com.facebook.presto.spi.function.OperatorType.NOT_EQUAL;
 import static com.facebook.presto.spi.function.OperatorType.SATURATED_FLOOR_CAST;
 import static com.facebook.presto.spi.function.OperatorType.SUBTRACT;
 import static com.facebook.presto.spi.function.OperatorType.XX_HASH_64;
+import static com.facebook.presto.spi.type.IntegerType.INTEGER;
 import static io.airlift.slice.Slices.utf8Slice;
 import static java.lang.Float.floatToRawIntBits;
 import static java.lang.String.format;
@@ -249,20 +253,39 @@ public final class IntegerOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(StandardTypes.INTEGER) long left,
-            @IsNull boolean leftNull,
-            @SqlType(StandardTypes.INTEGER) long right,
-            @IsNull boolean rightNull)
+    public static class IntegerDistinctFromOperator
     {
-        if (leftNull != rightNull) {
-            return true;
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(StandardTypes.INTEGER) long left,
+                @IsNull boolean leftNull,
+                @SqlType(StandardTypes.INTEGER) long right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = StandardTypes.INTEGER, nativeContainerType = long.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = StandardTypes.INTEGER, nativeContainerType = long.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+            return notEqual(INTEGER.getLong(left, leftPosition), INTEGER.getLong(right, rightPosition));
         }
-        return notEqual(left, right);
     }
 
     @ScalarOperator(SATURATED_FLOOR_CAST)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/IntervalDayTimeOperators.java b/presto-main/src/main/java/com/facebook/presto/type/IntervalDayTimeOperators.java
index 3cc49c82f1..d56d3e366e 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/IntervalDayTimeOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/IntervalDayTimeOperators.java
@@ -13,6 +13,9 @@
  */
 package com.facebook.presto.type;
 
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarOperator;
@@ -39,6 +42,7 @@ import static com.facebook.presto.spi.function.OperatorType.MULTIPLY;
 import static com.facebook.presto.spi.function.OperatorType.NEGATION;
 import static com.facebook.presto.spi.function.OperatorType.NOT_EQUAL;
 import static com.facebook.presto.spi.function.OperatorType.SUBTRACT;
+import static com.facebook.presto.type.IntervalDayTimeType.INTERVAL_DAY_TIME;
 import static io.airlift.slice.Slices.utf8Slice;
 
 public final class IntervalDayTimeOperators
@@ -173,20 +177,39 @@ public final class IntervalDayTimeOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(StandardTypes.INTERVAL_DAY_TO_SECOND) long left,
-            @IsNull boolean leftNull,
-            @SqlType(StandardTypes.INTERVAL_DAY_TO_SECOND) long right,
-            @IsNull boolean rightNull)
-    {
-        if (leftNull != rightNull) {
-            return true;
+    public static class IntervalDayTimeDistinctFromOperator
+    {
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(StandardTypes.INTERVAL_DAY_TO_SECOND) long left,
+                @IsNull boolean leftNull,
+                @SqlType(StandardTypes.INTERVAL_DAY_TO_SECOND) long right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = StandardTypes.INTERVAL_DAY_TO_SECOND, nativeContainerType = long.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = StandardTypes.INTERVAL_DAY_TO_SECOND, nativeContainerType = long.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+            return notEqual(INTERVAL_DAY_TIME.getLong(left, leftPosition), INTERVAL_DAY_TIME.getLong(right, rightPosition));
         }
-        return notEqual(left, right);
     }
 
     @ScalarOperator(INDETERMINATE)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/IntervalYearMonthOperators.java b/presto-main/src/main/java/com/facebook/presto/type/IntervalYearMonthOperators.java
index ed678424ed..7987b0af91 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/IntervalYearMonthOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/IntervalYearMonthOperators.java
@@ -14,6 +14,9 @@
 package com.facebook.presto.type;
 
 import com.facebook.presto.client.IntervalYearMonth;
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarOperator;
@@ -39,6 +42,7 @@ import static com.facebook.presto.spi.function.OperatorType.MULTIPLY;
 import static com.facebook.presto.spi.function.OperatorType.NEGATION;
 import static com.facebook.presto.spi.function.OperatorType.NOT_EQUAL;
 import static com.facebook.presto.spi.function.OperatorType.SUBTRACT;
+import static com.facebook.presto.type.IntervalYearMonthType.INTERVAL_YEAR_MONTH;
 import static io.airlift.slice.Slices.utf8Slice;
 import static java.lang.Math.toIntExact;
 
@@ -174,20 +178,39 @@ public final class IntervalYearMonthOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(StandardTypes.INTERVAL_YEAR_TO_MONTH) long left,
-            @IsNull boolean leftNull,
-            @SqlType(StandardTypes.INTERVAL_YEAR_TO_MONTH) long right,
-            @IsNull boolean rightNull)
-    {
-        if (leftNull != rightNull) {
-            return true;
+    public static class IntervalYearMonthDistinctFromOperator
+    {
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(StandardTypes.INTERVAL_YEAR_TO_MONTH) long left,
+                @IsNull boolean leftNull,
+                @SqlType(StandardTypes.INTERVAL_YEAR_TO_MONTH) long right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = StandardTypes.INTERVAL_YEAR_TO_MONTH, nativeContainerType = long.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = StandardTypes.INTERVAL_YEAR_TO_MONTH, nativeContainerType = long.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+            return notEqual(INTERVAL_YEAR_MONTH.getLong(left, leftPosition), INTERVAL_YEAR_MONTH.getLong(right, rightPosition));
         }
-        return notEqual(left, right);
     }
 
     @ScalarOperator(INDETERMINATE)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/IpAddressOperators.java b/presto-main/src/main/java/com/facebook/presto/type/IpAddressOperators.java
index 3e5c31ee2f..4d457354b6 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/IpAddressOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/IpAddressOperators.java
@@ -14,6 +14,9 @@
 package com.facebook.presto.type;
 
 import com.facebook.presto.spi.PrestoException;
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarOperator;
@@ -41,6 +44,7 @@ import static com.facebook.presto.spi.function.OperatorType.LESS_THAN;
 import static com.facebook.presto.spi.function.OperatorType.LESS_THAN_OR_EQUAL;
 import static com.facebook.presto.spi.function.OperatorType.NOT_EQUAL;
 import static com.facebook.presto.spi.function.OperatorType.XX_HASH_64;
+import static com.facebook.presto.type.IpAddressType.IPADDRESS;
 import static io.airlift.slice.Slices.utf8Slice;
 import static io.airlift.slice.Slices.wrappedBuffer;
 import static java.lang.System.arraycopy;
@@ -186,20 +190,39 @@ public final class IpAddressOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(StandardTypes.IPADDRESS) Slice left,
-            @IsNull boolean leftNull,
-            @SqlType(StandardTypes.IPADDRESS) Slice right,
-            @IsNull boolean rightNull)
-    {
-        if (leftNull != rightNull) {
-            return true;
+    public static class IpAddressDistinctFromOperator
+    {
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(StandardTypes.IPADDRESS) Slice left,
+                @IsNull boolean leftNull,
+                @SqlType(StandardTypes.IPADDRESS) Slice right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = StandardTypes.IPADDRESS, nativeContainerType = Slice.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = StandardTypes.IPADDRESS, nativeContainerType = Slice.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+            return left.compareTo(leftPosition, 0, IPADDRESS.getFixedSize(), right, rightPosition, 0, IPADDRESS.getFixedSize()) != 0;
         }
-        return notEqual(left, right);
     }
 
     @ScalarOperator(INDETERMINATE)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/RealOperators.java b/presto-main/src/main/java/com/facebook/presto/type/RealOperators.java
index 538c944c4f..594ee8ac38 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/RealOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/RealOperators.java
@@ -15,6 +15,9 @@ package com.facebook.presto.type;
 
 import com.facebook.presto.operator.scalar.MathFunctions;
 import com.facebook.presto.spi.PrestoException;
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarOperator;
@@ -48,6 +51,7 @@ import static com.facebook.presto.spi.function.OperatorType.NOT_EQUAL;
 import static com.facebook.presto.spi.function.OperatorType.SATURATED_FLOOR_CAST;
 import static com.facebook.presto.spi.function.OperatorType.SUBTRACT;
 import static com.facebook.presto.spi.function.OperatorType.XX_HASH_64;
+import static com.facebook.presto.spi.type.RealType.REAL;
 import static io.airlift.slice.Slices.utf8Slice;
 import static java.lang.Float.floatToIntBits;
 import static java.lang.Float.floatToRawIntBits;
@@ -244,25 +248,44 @@ public final class RealOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(StandardTypes.REAL) long left,
-            @IsNull boolean leftNull,
-            @SqlType(StandardTypes.REAL) long right,
-            @IsNull boolean rightNull)
+    public static class RealDistinctFromOperator
     {
-        if (leftNull != rightNull) {
-            return true;
-        }
-        if (leftNull) {
-            return false;
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(StandardTypes.REAL) long left,
+                @IsNull boolean leftNull,
+                @SqlType(StandardTypes.REAL) long right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            float leftFloat = intBitsToFloat((int) left);
+            float rightFloat = intBitsToFloat((int) right);
+            if (Float.isNaN(leftFloat) && Float.isNaN(rightFloat)) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        float leftFloat = intBitsToFloat((int) left);
-        float rightFloat = intBitsToFloat((int) right);
-        if (Float.isNaN(leftFloat) && Float.isNaN(rightFloat)) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = StandardTypes.REAL, nativeContainerType = long.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = StandardTypes.REAL, nativeContainerType = long.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+            return notEqual(REAL.getLong(left, leftPosition), REAL.getLong(right, rightPosition));
         }
-        return notEqual(left, right);
     }
 
     @ScalarOperator(SATURATED_FLOOR_CAST)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/SmallintOperators.java b/presto-main/src/main/java/com/facebook/presto/type/SmallintOperators.java
index 5cf30a3228..87480ee83b 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/SmallintOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/SmallintOperators.java
@@ -14,6 +14,9 @@
 package com.facebook.presto.type;
 
 import com.facebook.presto.spi.PrestoException;
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarOperator;
@@ -47,6 +50,7 @@ import static com.facebook.presto.spi.function.OperatorType.NOT_EQUAL;
 import static com.facebook.presto.spi.function.OperatorType.SATURATED_FLOOR_CAST;
 import static com.facebook.presto.spi.function.OperatorType.SUBTRACT;
 import static com.facebook.presto.spi.function.OperatorType.XX_HASH_64;
+import static com.facebook.presto.spi.type.SmallintType.SMALLINT;
 import static io.airlift.slice.Slices.utf8Slice;
 import static java.lang.Float.floatToRawIntBits;
 import static java.lang.String.format;
@@ -244,20 +248,39 @@ public final class SmallintOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(StandardTypes.SMALLINT) long left,
-            @IsNull boolean leftNull,
-            @SqlType(StandardTypes.SMALLINT) long right,
-            @IsNull boolean rightNull)
+    public static class SmallintDistinctFromOperator
     {
-        if (leftNull != rightNull) {
-            return true;
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(StandardTypes.SMALLINT) long left,
+                @IsNull boolean leftNull,
+                @SqlType(StandardTypes.SMALLINT) long right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = StandardTypes.SMALLINT, nativeContainerType = long.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = StandardTypes.SMALLINT, nativeContainerType = long.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+            return notEqual(SMALLINT.getLong(left, leftPosition), SMALLINT.getLong(right, rightPosition));
         }
-        return notEqual(left, right);
     }
 
     @ScalarOperator(SATURATED_FLOOR_CAST)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/TimeOperators.java b/presto-main/src/main/java/com/facebook/presto/type/TimeOperators.java
index 89a5f3ae50..86fe1a4a37 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/TimeOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/TimeOperators.java
@@ -15,6 +15,9 @@ package com.facebook.presto.type;
 
 import com.facebook.presto.spi.ConnectorSession;
 import com.facebook.presto.spi.PrestoException;
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarOperator;
@@ -41,6 +44,7 @@ import static com.facebook.presto.spi.function.OperatorType.NOT_EQUAL;
 import static com.facebook.presto.spi.function.OperatorType.SUBTRACT;
 import static com.facebook.presto.spi.function.OperatorType.XX_HASH_64;
 import static com.facebook.presto.spi.type.DateTimeEncoding.packDateTimeWithZone;
+import static com.facebook.presto.spi.type.TimeType.TIME;
 import static com.facebook.presto.util.DateTimeUtils.parseTimeWithoutTimeZone;
 import static com.facebook.presto.util.DateTimeUtils.printTimeWithoutTimeZone;
 import static com.facebook.presto.util.DateTimeZoneIndex.getChronology;
@@ -189,20 +193,39 @@ public final class TimeOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(StandardTypes.TIME) long left,
-            @IsNull boolean leftNull,
-            @SqlType(StandardTypes.TIME) long right,
-            @IsNull boolean rightNull)
-    {
-        if (leftNull != rightNull) {
-            return true;
+    public static class TimeDistinctFromOperator
+    {
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(StandardTypes.TIME) long left,
+                @IsNull boolean leftNull,
+                @SqlType(StandardTypes.TIME) long right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = StandardTypes.TIME, nativeContainerType = long.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = StandardTypes.TIME, nativeContainerType = long.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+            return notEqual(TIME.getLong(left, leftPosition), TIME.getLong(right, rightPosition));
         }
-        return notEqual(left, right);
     }
 
     @ScalarOperator(INDETERMINATE)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/TimeWithTimeZoneOperators.java b/presto-main/src/main/java/com/facebook/presto/type/TimeWithTimeZoneOperators.java
index 0369f5efef..a02f285123 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/TimeWithTimeZoneOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/TimeWithTimeZoneOperators.java
@@ -14,6 +14,9 @@
 package com.facebook.presto.type;
 
 import com.facebook.presto.spi.ConnectorSession;
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarOperator;
@@ -44,6 +47,7 @@ import static com.facebook.presto.spi.function.OperatorType.SUBTRACT;
 import static com.facebook.presto.spi.function.OperatorType.XX_HASH_64;
 import static com.facebook.presto.spi.type.DateTimeEncoding.unpackMillisUtc;
 import static com.facebook.presto.spi.type.DateTimeEncoding.unpackZoneKey;
+import static com.facebook.presto.spi.type.TimeWithTimeZoneType.TIME_WITH_TIME_ZONE;
 import static com.facebook.presto.util.DateTimeUtils.parseTimeWithTimeZone;
 import static com.facebook.presto.util.DateTimeUtils.printTimeWithTimeZone;
 import static com.facebook.presto.util.DateTimeZoneIndex.getChronology;
@@ -180,20 +184,39 @@ public final class TimeWithTimeZoneOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(StandardTypes.TIME_WITH_TIME_ZONE) long left,
-            @IsNull boolean leftNull,
-            @SqlType(StandardTypes.TIME_WITH_TIME_ZONE) long right,
-            @IsNull boolean rightNull)
-    {
-        if (leftNull != rightNull) {
-            return true;
+    public static class TimeWithTimeZoneDistinctFromOperator
+    {
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(StandardTypes.TIME_WITH_TIME_ZONE) long left,
+                @IsNull boolean leftNull,
+                @SqlType(StandardTypes.TIME_WITH_TIME_ZONE) long right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = StandardTypes.TIME_WITH_TIME_ZONE, nativeContainerType = long.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = StandardTypes.TIME_WITH_TIME_ZONE, nativeContainerType = long.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) && right.isNull(rightPosition)) {
+                return false;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+            return notEqual(TIME_WITH_TIME_ZONE.getLong(left, leftPosition), TIME_WITH_TIME_ZONE.getLong(right, rightPosition));
         }
-        return notEqual(left, right);
     }
 
     @ScalarOperator(INDETERMINATE)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/TimestampOperators.java b/presto-main/src/main/java/com/facebook/presto/type/TimestampOperators.java
index 81b7e5f5b7..affc2fc468 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/TimestampOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/TimestampOperators.java
@@ -15,6 +15,9 @@ package com.facebook.presto.type;
 
 import com.facebook.presto.spi.ConnectorSession;
 import com.facebook.presto.spi.PrestoException;
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarFunction;
@@ -44,6 +47,7 @@ import static com.facebook.presto.spi.function.OperatorType.NOT_EQUAL;
 import static com.facebook.presto.spi.function.OperatorType.SUBTRACT;
 import static com.facebook.presto.spi.function.OperatorType.XX_HASH_64;
 import static com.facebook.presto.spi.type.DateTimeEncoding.packDateTimeWithZone;
+import static com.facebook.presto.spi.type.TimestampType.TIMESTAMP;
 import static com.facebook.presto.type.DateTimeOperators.modulo24Hour;
 import static com.facebook.presto.util.DateTimeUtils.parseTimestampWithoutTimeZone;
 import static com.facebook.presto.util.DateTimeUtils.printTimestampWithoutTimeZone;
@@ -225,20 +229,39 @@ public final class TimestampOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(StandardTypes.TIMESTAMP) long left,
-            @IsNull boolean leftNull,
-            @SqlType(StandardTypes.TIMESTAMP) long right,
-            @IsNull boolean rightNull)
+    public static class TimestampDistinctFromOperator
     {
-        if (leftNull != rightNull) {
-            return true;
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(StandardTypes.TIMESTAMP) long left,
+                @IsNull boolean leftNull,
+                @SqlType(StandardTypes.TIMESTAMP) long right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = StandardTypes.TIMESTAMP, nativeContainerType = long.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = StandardTypes.TIMESTAMP, nativeContainerType = long.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+            return notEqual(TIMESTAMP.getLong(left, leftPosition), TIMESTAMP.getLong(right, rightPosition));
         }
-        return notEqual(left, right);
     }
 
     @ScalarOperator(INDETERMINATE)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/TimestampWithTimeZoneOperators.java b/presto-main/src/main/java/com/facebook/presto/type/TimestampWithTimeZoneOperators.java
index 7c40470485..80fe5d559a 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/TimestampWithTimeZoneOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/TimestampWithTimeZoneOperators.java
@@ -15,6 +15,9 @@ package com.facebook.presto.type;
 
 import com.facebook.presto.spi.ConnectorSession;
 import com.facebook.presto.spi.PrestoException;
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarFunction;
@@ -46,6 +49,7 @@ import static com.facebook.presto.spi.function.OperatorType.XX_HASH_64;
 import static com.facebook.presto.spi.type.DateTimeEncoding.packDateTimeWithZone;
 import static com.facebook.presto.spi.type.DateTimeEncoding.unpackMillisUtc;
 import static com.facebook.presto.spi.type.DateTimeEncoding.unpackZoneKey;
+import static com.facebook.presto.spi.type.TimestampWithTimeZoneType.TIMESTAMP_WITH_TIME_ZONE;
 import static com.facebook.presto.type.DateTimeOperators.modulo24Hour;
 import static com.facebook.presto.util.DateTimeUtils.parseTimestampWithTimeZone;
 import static com.facebook.presto.util.DateTimeUtils.printTimestampWithTimeZone;
@@ -217,20 +221,39 @@ public final class TimestampWithTimeZoneOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(StandardTypes.TIMESTAMP_WITH_TIME_ZONE) long left,
-            @IsNull boolean leftNull,
-            @SqlType(StandardTypes.TIMESTAMP_WITH_TIME_ZONE) long right,
-            @IsNull boolean rightNull)
-    {
-        if (leftNull != rightNull) {
-            return true;
+    public static class TimestampWithTimeZoneDistinctFromOperator
+    {
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(StandardTypes.TIMESTAMP_WITH_TIME_ZONE) long left,
+                @IsNull boolean leftNull,
+                @SqlType(StandardTypes.TIMESTAMP_WITH_TIME_ZONE) long right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = StandardTypes.TIMESTAMP_WITH_TIME_ZONE, nativeContainerType = long.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = StandardTypes.TIMESTAMP_WITH_TIME_ZONE, nativeContainerType = long.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+            return notEqual(TIMESTAMP_WITH_TIME_ZONE.getLong(left, leftPosition), TIMESTAMP_WITH_TIME_ZONE.getLong(right, rightPosition));
         }
-        return notEqual(left, right);
     }
 
     @ScalarOperator(INDETERMINATE)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/TinyintOperators.java b/presto-main/src/main/java/com/facebook/presto/type/TinyintOperators.java
index bf8ca5cc93..ca557df1a3 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/TinyintOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/TinyintOperators.java
@@ -14,6 +14,9 @@
 package com.facebook.presto.type;
 
 import com.facebook.presto.spi.PrestoException;
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarOperator;
@@ -45,6 +48,7 @@ import static com.facebook.presto.spi.function.OperatorType.NEGATION;
 import static com.facebook.presto.spi.function.OperatorType.NOT_EQUAL;
 import static com.facebook.presto.spi.function.OperatorType.SUBTRACT;
 import static com.facebook.presto.spi.function.OperatorType.XX_HASH_64;
+import static com.facebook.presto.spi.type.TinyintType.TINYINT;
 import static io.airlift.slice.Slices.utf8Slice;
 import static java.lang.Float.floatToRawIntBits;
 import static java.lang.String.format;
@@ -244,20 +248,39 @@ public final class TinyintOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(StandardTypes.TINYINT) long left,
-            @IsNull boolean leftNull,
-            @SqlType(StandardTypes.TINYINT) long right,
-            @IsNull boolean rightNull)
+    public static class TinyintDistinctFromOperator
     {
-        if (leftNull != rightNull) {
-            return true;
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(StandardTypes.TINYINT) long left,
+                @IsNull boolean leftNull,
+                @SqlType(StandardTypes.TINYINT) long right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = StandardTypes.TINYINT, nativeContainerType = long.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = StandardTypes.TINYINT, nativeContainerType = long.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+            return notEqual(TINYINT.getLong(left, leftPosition), TINYINT.getLong(right, rightPosition));
         }
-        return notEqual(left, right);
     }
 
     @ScalarOperator(INDETERMINATE)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/UnknownOperators.java b/presto-main/src/main/java/com/facebook/presto/type/UnknownOperators.java
index 32241a65ad..f50896fa30 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/UnknownOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/UnknownOperators.java
@@ -13,6 +13,9 @@
  */
 package com.facebook.presto.type;
 
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.ScalarOperator;
 import com.facebook.presto.spi.function.SqlNullable;
@@ -93,14 +96,27 @@ public final class UnknownOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType("unknown") boolean left,
-            @IsNull boolean leftNull,
-            @SqlType("unknown") boolean right,
-            @IsNull boolean rightNull)
+    public static class UnknownDistinctFromOperator
     {
-        return false;
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType("unknown") boolean left,
+                @IsNull boolean leftNull,
+                @SqlType("unknown") boolean right,
+                @IsNull boolean rightNull)
+        {
+            return false;
+        }
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = "unknown", nativeContainerType = boolean.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = "unknown", nativeContainerType = boolean.class) Block right,
+                @BlockIndex int rightNull)
+        {
+            return false;
+        }
     }
 
     @ScalarOperator(INDETERMINATE)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/VarbinaryOperators.java b/presto-main/src/main/java/com/facebook/presto/type/VarbinaryOperators.java
index ff6418b8b2..9c9c305ea6 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/VarbinaryOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/VarbinaryOperators.java
@@ -13,6 +13,9 @@
  */
 package com.facebook.presto.type;
 
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.ScalarOperator;
 import com.facebook.presto.spi.function.SqlNullable;
@@ -101,20 +104,45 @@ public final class VarbinaryOperators
     }
 
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType(StandardTypes.VARBINARY) Slice left,
-            @IsNull boolean leftNull,
-            @SqlType(StandardTypes.VARBINARY) Slice right,
-            @IsNull boolean rightNull)
+    public static class VarbinaryDistinctFromOperator
     {
-        if (leftNull != rightNull) {
-            return true;
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType(StandardTypes.VARBINARY) Slice left,
+                @IsNull boolean leftNull,
+                @SqlType(StandardTypes.VARBINARY) Slice right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = StandardTypes.VARBINARY, nativeContainerType = Slice.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = StandardTypes.VARBINARY, nativeContainerType = Slice.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+
+            int leftLength = left.getSliceLength(leftPosition);
+            int rightLength = right.getSliceLength(rightPosition);
+            if (leftLength != rightLength) {
+                return true;
+            }
+            return !left.equals(leftPosition, 0, right, rightPosition, 0, leftLength);
         }
-        return notEqual(left, right);
     }
 
     @ScalarOperator(XX_HASH_64)
diff --git a/presto-main/src/main/java/com/facebook/presto/type/VarcharOperators.java b/presto-main/src/main/java/com/facebook/presto/type/VarcharOperators.java
index ff2fb6ba9a..c395834cdb 100644
--- a/presto-main/src/main/java/com/facebook/presto/type/VarcharOperators.java
+++ b/presto-main/src/main/java/com/facebook/presto/type/VarcharOperators.java
@@ -14,6 +14,9 @@
 package com.facebook.presto.type;
 
 import com.facebook.presto.spi.PrestoException;
+import com.facebook.presto.spi.block.Block;
+import com.facebook.presto.spi.function.BlockIndex;
+import com.facebook.presto.spi.function.BlockPosition;
 import com.facebook.presto.spi.function.IsNull;
 import com.facebook.presto.spi.function.LiteralParameters;
 import com.facebook.presto.spi.function.ScalarOperator;
@@ -238,22 +241,48 @@ public final class VarcharOperators
         return xxHash64(value);
     }
 
-    @LiteralParameters({"x", "y"})
     @ScalarOperator(IS_DISTINCT_FROM)
-    @SqlType(StandardTypes.BOOLEAN)
-    public static boolean isDistinctFrom(
-            @SqlType("varchar(x)") Slice left,
-            @IsNull boolean leftNull,
-            @SqlType("varchar(y)") Slice right,
-            @IsNull boolean rightNull)
+    public static class VarcharDistinctFromOperator
     {
-        if (leftNull != rightNull) {
-            return true;
+        @LiteralParameters({"x", "y"})
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @SqlType("varchar(x)") Slice left,
+                @IsNull boolean leftNull,
+                @SqlType("varchar(y)") Slice right,
+                @IsNull boolean rightNull)
+        {
+            if (leftNull != rightNull) {
+                return true;
+            }
+            if (leftNull) {
+                return false;
+            }
+            return notEqual(left, right);
         }
-        if (leftNull) {
-            return false;
+
+        @LiteralParameters({"x", "y"})
+        @SqlType(StandardTypes.BOOLEAN)
+        public static boolean isDistinctFrom(
+                @BlockPosition @SqlType(value = "varchar(x)", nativeContainerType = Slice.class) Block left,
+                @BlockIndex int leftPosition,
+                @BlockPosition @SqlType(value = "varchar(y)", nativeContainerType = Slice.class) Block right,
+                @BlockIndex int rightPosition)
+        {
+            if (left.isNull(leftPosition) != right.isNull(rightPosition)) {
+                return true;
+            }
+            if (left.isNull(leftPosition)) {
+                return false;
+            }
+
+            int leftLength = left.getSliceLength(leftPosition);
+            int rightLength = right.getSliceLength(rightPosition);
+            if (leftLength != rightLength) {
+                return true;
+            }
+            return !left.equals(leftPosition, 0, right, rightPosition, 0, leftLength);
         }
-        return notEqual(left, right);
     }
 
     @LiteralParameters("x")
diff --git a/presto-main/src/test/java/com/facebook/presto/type/TestArrayOperators.java b/presto-main/src/test/java/com/facebook/presto/type/TestArrayOperators.java
index d87419fb30..6dd39bcab4 100644
--- a/presto-main/src/test/java/com/facebook/presto/type/TestArrayOperators.java
+++ b/presto-main/src/test/java/com/facebook/presto/type/TestArrayOperators.java
@@ -1358,9 +1358,15 @@ public class TestArrayOperators
         assertFunction("ARRAY [1, NULL] IS DISTINCT FROM ARRAY [1, NULL]", BOOLEAN, false);
         assertFunction("ARRAY [1, NULL] IS DISTINCT FROM ARRAY [1, NULL]", BOOLEAN, false);
         assertFunction("ARRAY [1, 2, NULL] IS DISTINCT FROM ARRAY [1, 2]", BOOLEAN, true);
+        assertFunction("ARRAY [TRUE, FALSE] IS DISTINCT FROM ARRAY [TRUE, FALSE]", BOOLEAN, false);
+        assertFunction("ARRAY [TRUE, NULL] IS DISTINCT FROM ARRAY [TRUE, FALSE]", BOOLEAN, true);
+        assertFunction("ARRAY [FALSE, NULL] IS DISTINCT FROM ARRAY [NULL, FALSE]", BOOLEAN, true);
         assertFunction("ARRAY ['puppies', 'kittens'] IS DISTINCT FROM ARRAY ['puppies', 'kittens']", BOOLEAN, false);
         assertFunction("ARRAY ['puppies', NULL] IS DISTINCT FROM ARRAY ['puppies', 'kittens']", BOOLEAN, true);
         assertFunction("ARRAY ['puppies', NULL] IS DISTINCT FROM ARRAY [NULL, 'kittens']", BOOLEAN, true);
+        assertFunction("ARRAY [ARRAY ['puppies'], ARRAY ['kittens']] IS DISTINCT FROM ARRAY [ARRAY ['puppies'], ARRAY ['kittens']]", BOOLEAN, false);
+        assertFunction("ARRAY [ARRAY ['puppies'], NULL] IS DISTINCT FROM ARRAY [ARRAY ['puppies'], ARRAY ['kittens']]", BOOLEAN, true);
+        assertFunction("ARRAY [ARRAY ['puppies'], NULL] IS DISTINCT FROM ARRAY [NULL, ARRAY ['kittens']]", BOOLEAN, true);
     }
 
     @Test
diff --git a/presto-main/src/test/java/com/facebook/presto/type/TestDecimalOperators.java b/presto-main/src/test/java/com/facebook/presto/type/TestDecimalOperators.java
index 2a90ab08f6..580ce6f997 100644
--- a/presto-main/src/test/java/com/facebook/presto/type/TestDecimalOperators.java
+++ b/presto-main/src/test/java/com/facebook/presto/type/TestDecimalOperators.java
@@ -787,6 +787,14 @@ public class TestDecimalOperators
         assertFunction("DECIMAL '-2' IS DISTINCT FROM NULL", BOOLEAN, true);
         assertFunction("NULL IS DISTINCT FROM DECIMAL '12345678901234567.89012345678901234567'", BOOLEAN, true);
         assertFunction("DECIMAL '12345678901234567.89012345678901234567' IS DISTINCT FROM NULL", BOOLEAN, true);
+
+        // delegation from other operator (exercises block-position convention implementation)
+        assertFunction("ARRAY [1.23, 4.56] IS DISTINCT FROM ARRAY [1.23, 4.56]", BOOLEAN, false);
+        assertFunction("ARRAY [1.23, NULL] IS DISTINCT FROM ARRAY [1.23, 4.56]", BOOLEAN, true);
+        assertFunction("ARRAY [1.23, NULL] IS DISTINCT FROM ARRAY [NULL, 4.56]", BOOLEAN, true);
+        assertFunction("ARRAY [1234567890.123456789, 9876543210.987654321] IS DISTINCT FROM ARRAY [1234567890.123456789, 9876543210.987654321]", BOOLEAN, false);
+        assertFunction("ARRAY [1234567890.123456789, NULL] IS DISTINCT FROM ARRAY [1234567890.123456789, 9876543210.987654321]", BOOLEAN, true);
+        assertFunction("ARRAY [1234567890.123456789, NULL] IS DISTINCT FROM ARRAY [NULL, 9876543210.987654321]", BOOLEAN, true);
     }
 
     @Test
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
