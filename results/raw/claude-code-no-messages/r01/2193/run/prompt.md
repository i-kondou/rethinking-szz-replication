This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 8acbfba9a519e67e4652ce1118157fceadcbbc92
- Commit message: 
- Diff:
```
commit 8acbfba9a519e67e4652ce1118157fceadcbbc92
Author: doe300 <stadeldani@web.de>
Date:   Wed Mar 25 13:24:18 2015 +0100
---
 .../store/impl/SimpleJDBCRecordStore.java          | 45 +++++++++++-----------
 .../activerecord/TestActiveRecordSyntax.java       | 20 ++++++----
 .../proxy/handlers/InterfaceProxyHandlerTest.java  | 22 ++++-------
 3 files changed, 42 insertions(+), 45 deletions(-)

diff --git a/src/de/doe300/activerecord/store/impl/SimpleJDBCRecordStore.java b/src/de/doe300/activerecord/store/impl/SimpleJDBCRecordStore.java
index 0fc10c4..77c72fd 100644
--- a/src/de/doe300/activerecord/store/impl/SimpleJDBCRecordStore.java
+++ b/src/de/doe300/activerecord/store/impl/SimpleJDBCRecordStore.java
@@ -382,10 +382,9 @@ public class SimpleJDBCRecordStore implements RecordStore
 			{
 				fillStatement( stm, scope.getCondition() );
 			}
-			try (final ResultSet res = stm.executeQuery())
-			{
-				return allWithDataStream(columns, res);
-			}
+			//this result-set can't be try-with-resource because it is required to stay open
+			final ResultSet res = stm.executeQuery();
+			return allWithDataStream(columns, res);
 		}
 		catch ( final SQLException ex )
 		{
@@ -516,7 +515,6 @@ public class SimpleJDBCRecordStore implements RecordStore
 					throw new RuntimeException("Failed to create table", e);
 				}
 			}
-			PreparedStatement stmt;
 			final Map<String,Object> rowData = new HashMap<>(columns != null ? columns.size() : 3 );
 			//set initial values
 			if(columns != null)
@@ -537,25 +535,27 @@ public class SimpleJDBCRecordStore implements RecordStore
 					" ("+rowData.entrySet().stream().map((final Map.Entry<String,Object> e) -> e.getKey()).map( this::convertIdentifier).collect( Collectors.joining( ", "))+
 					") VALUES ("+rowData.entrySet().stream().map((final Map.Entry<String,Object> e) -> "?").collect( Collectors.joining( ", "))+")";
 			Logging.getLogger().debug( "JDBCStore", sql);
-			stmt = con.prepareStatement( sql, Statement.RETURN_GENERATED_KEYS );
-
-			int i = 0;
-			for(final Map.Entry<String,Object> e : rowData.entrySet())
+			try (PreparedStatement stmt = con.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS))
 			{
-				stmt.setObject( i+1, e.getValue());
-				i++;
-			}
+				int i = 0;
+				for (final Map.Entry<String, Object> e : rowData.entrySet())
+				{
+					stmt.setObject(i + 1, e.getValue());
+					i++;
+				}
 
-			stmt.executeUpdate();
-			try (final ResultSet rs = stmt.getGeneratedKeys())
-			{
-				if (rs.next())
+				stmt.executeUpdate();
+				try (final ResultSet rs = stmt.getGeneratedKeys())
 				{
-					return rs.getInt(base.getPrimaryColumn());
+					if (rs.next())
+					{
+						return rs.getInt(base.getPrimaryColumn());
+					}
+					Logging.getLogger().error("JDBCStore", "Failed to insert new row!");
+					return -1;
 				}
-				Logging.getLogger().error("JDBCStore", "Failed to insert new row!");
-				return -1;
 			}
+
 		}
 		catch ( final SQLException ex )
 		{
@@ -580,10 +580,9 @@ public class SimpleJDBCRecordStore implements RecordStore
 		try(PreparedStatement stmt = con.prepareStatement( sql))
 		{
 			stmt.setObject( 1, condValue);
-			try (final ResultSet res = stmt.executeQuery())
-			{
-				return valuesStream(res);
-			}
+			//can't use try-with-resource here, because result-set is required to stay open
+			final ResultSet res = stmt.executeQuery();
+			return valuesStream(res);
 		}
 		catch ( final SQLException ex )
 		{
diff --git a/test/de/doe300/activerecord/TestActiveRecordSyntax.java b/test/de/doe300/activerecord/TestActiveRecordSyntax.java
index d3e9e62..f873168 100644
--- a/test/de/doe300/activerecord/TestActiveRecordSyntax.java
+++ b/test/de/doe300/activerecord/TestActiveRecordSyntax.java
@@ -24,9 +24,10 @@
  */
 package de.doe300.activerecord;
 
+import java.sql.SQLException;
+
 import de.doe300.activerecord.dsl.Comparison;
 import de.doe300.activerecord.dsl.SimpleCondition;
-import java.sql.SQLException;
 
 /**
  * Just some code to test the feeling of the syntax
@@ -34,14 +35,19 @@ import java.sql.SQLException;
  */
 public class TestActiveRecordSyntax
 {
-	public static void main(String[] args) throws SQLException, Exception
+	/**
+	 * @param args
+	 * @throws SQLException
+	 * @throws Exception
+	 */
+	public static void main(final String[] args) throws SQLException, Exception
 	{
 		//0, create new core
-		RecordCore core = RecordCore.fromDatabase( null, true );
+		final RecordCore core = RecordCore.fromDatabase(TestServer.getTestConnection(), true);
 		//1. create new recordbase
-		RecordBase<TestInterface> base = core.getBase( TestInterface.class);
+		final RecordBase<TestInterface> base = core.getBase( TestInterface.class);
 		//2. get record
-		TestInterface el = base.getRecord(1);
+		final TestInterface el = base.getRecord(1);
 		//3. change & store record
 		el.setAge( 23);
 		el.save();
@@ -49,8 +55,8 @@ public class TestActiveRecordSyntax
 		el.destroy();
 
 		//5. get all for attribute
-		base.findFor( "age", 23).forEach( (TestInterface i)-> System.err.println( i.getName() ));
-		
+		base.findFor( "age", 23).forEach( (final TestInterface i)-> System.err.println( i.getName() ));
+
 		//6. query
 		base.where( new SimpleCondition("name", "Max", Comparison.IS));
 	}
diff --git a/test/de/doe300/activerecord/proxy/handlers/InterfaceProxyHandlerTest.java b/test/de/doe300/activerecord/proxy/handlers/InterfaceProxyHandlerTest.java
index 2469074..61025d0 100644
--- a/test/de/doe300/activerecord/proxy/handlers/InterfaceProxyHandlerTest.java
+++ b/test/de/doe300/activerecord/proxy/handlers/InterfaceProxyHandlerTest.java
@@ -24,14 +24,15 @@
  */
 package de.doe300.activerecord.proxy.handlers;
 
-import de.doe300.activerecord.TestInterface;
-import de.doe300.activerecord.TestServer;
-import de.doe300.activerecord.proxy.RecordHandler;
 import org.junit.AfterClass;
 import org.junit.Assert;
 import org.junit.BeforeClass;
 import org.junit.Test;
 
+import de.doe300.activerecord.TestInterface;
+import de.doe300.activerecord.TestServer;
+import de.doe300.activerecord.proxy.RecordHandler;
+
 /**
  *
  * @author daniel
@@ -49,7 +50,7 @@ public class InterfaceProxyHandlerTest extends Assert
 	public static void createTables() throws Exception
 	{
 		TestServer.buildTestTables();
-		handler = new DummyInterfaceProxyHandler();
+		InterfaceProxyHandlerTest.handler = new DummyInterfaceProxyHandler();
 	}
 	
 	@AfterClass
@@ -68,15 +69,6 @@ public class InterfaceProxyHandlerTest extends Assert
 	{
 	}
 
-	public class InterfaceProxyHandlerImpl extends InterfaceProxyHandler
-	{
-
-		public InterfaceProxyHandlerImpl()
-		{
-			super( null );
-		}
-	}
-	
 	static class DummyInterfaceProxyHandler extends InterfaceProxyHandler<TestInterface>
 	{
 
@@ -85,12 +77,12 @@ public class InterfaceProxyHandlerTest extends Assert
 			super( TestInterface.class );
 		}
 		
-		public TestInterface getDirectionOne(TestInterface record, RecordHandler<TestInterface> handler)
+		public TestInterface getDirectionOne(final TestInterface record, final RecordHandler<TestInterface> handler)
 		{
 			return record;
 		}
 		
-		public void setDirectionOne(TestInterface record, RecordHandler<TestInterface> handler, TestInterface otherRecord)
+		public void setDirectionOne(final TestInterface record, final RecordHandler<TestInterface> handler, final TestInterface otherRecord)
 		{
 		}
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
