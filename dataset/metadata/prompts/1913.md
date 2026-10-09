This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: 5aa5d814676caf9691c19a250043b48c2438171b
- Commit message: fixed some compilations issues and added more type information
- Diff:
```
commit 5aa5d814676caf9691c19a250043b48c2438171b
Author: Steven Arzt <Steven.Arzt@cased.de>
Date:   Mon Mar 2 10:00:03 2015 +0100

    fixed some compilations issues and added more type information
---
 .../toolkits/infoflow/CallLocalityContext.java     | 10 ++--
 .../toolkits/infoflow/ClassInfoFlowAnalysis.java   | 32 ++++++-------
 .../infoflow/ClassLocalObjectsAnalysis.java        |  8 +---
 .../jimple/toolkits/infoflow/InfoFlowAnalysis.java | 56 ++++++++++------------
 .../infoflow/SimpleMethodInfoFlowAnalysis.java     | 35 ++++++--------
 tests/soot/toolkits/graph/TestDominance.java       | 51 ++++++++++----------
 6 files changed, 82 insertions(+), 110 deletions(-)

diff --git a/src/soot/jimple/toolkits/infoflow/CallLocalityContext.java b/src/soot/jimple/toolkits/infoflow/CallLocalityContext.java
index 6bb9a63e1..3d4a1b078 100644
--- a/src/soot/jimple/toolkits/infoflow/CallLocalityContext.java
+++ b/src/soot/jimple/toolkits/infoflow/CallLocalityContext.java
@@ -12,12 +12,12 @@ import java.util.*;
 
 public class CallLocalityContext
 {
-	List<Object> nodes;
+	List<EquivalentValue> nodes;
 	List<Boolean> isNodeLocal;
 
-	public CallLocalityContext(List<Object> nodes)
+	public CallLocalityContext(List<EquivalentValue> nodes)
 	{
-		this.nodes = new ArrayList<Object>();
+		this.nodes = new ArrayList<EquivalentValue>();
 		this.nodes.addAll(nodes);
 
 		isNodeLocal = new ArrayList<Boolean>(nodes.size());
@@ -29,7 +29,6 @@ public class CallLocalityContext
 	
 	public void setFieldLocal(EquivalentValue fieldRef)
 	{
-		List ret = new ArrayList();
 		for(int i = 0; i < nodes.size(); i++)
 		{
 			if( fieldRef.equals(nodes.get(i)) )
@@ -47,7 +46,6 @@ public class CallLocalityContext
 	
 	public void setFieldShared(EquivalentValue fieldRef)
 	{
-		List ret = new ArrayList();
 		for(int i = 0; i < nodes.size(); i++)
 		{
 			if( fieldRef.equals(nodes.get(i)) )
@@ -217,7 +215,6 @@ public class CallLocalityContext
 	
 	public boolean isFieldLocal(EquivalentValue fieldRef)
 	{
-		List ret = new ArrayList();
 		for(int i = 0; i < nodes.size(); i++)
 		{
 			if( fieldRef.equals(nodes.get(i)) )
@@ -230,7 +227,6 @@ public class CallLocalityContext
 	
 	public boolean containsField(EquivalentValue fieldRef)
 	{
-		List ret = new ArrayList();
 		for(int i = 0; i < nodes.size(); i++)
 		{
 			if( fieldRef.equals(nodes.get(i)) )
diff --git a/src/soot/jimple/toolkits/infoflow/ClassInfoFlowAnalysis.java b/src/soot/jimple/toolkits/infoflow/ClassInfoFlowAnalysis.java
index 5c3af1ee9..22e84e7fb 100644
--- a/src/soot/jimple/toolkits/infoflow/ClassInfoFlowAnalysis.java
+++ b/src/soot/jimple/toolkits/infoflow/ClassInfoFlowAnalysis.java
@@ -20,7 +20,7 @@ public class ClassInfoFlowAnalysis
 	InfoFlowAnalysis dfa; // used to access the data flow analyses of other classes
 	
 	Map<SootMethod, SmartMethodInfoFlowAnalysis> methodToInfoFlowAnalysis;
-	Map<SootMethod, HashMutableDirectedGraph> methodToInfoFlowSummary;
+	Map<SootMethod, HashMutableDirectedGraph<EquivalentValue>> methodToInfoFlowSummary;
 	
 	public static int methodCount = 0;
 	
@@ -29,7 +29,7 @@ public class ClassInfoFlowAnalysis
 		 this.sootClass = sootClass;
 		 this.dfa = dfa;
 		 methodToInfoFlowAnalysis = new HashMap<SootMethod, SmartMethodInfoFlowAnalysis>();
-		 methodToInfoFlowSummary = new HashMap<SootMethod, HashMutableDirectedGraph>();
+		 methodToInfoFlowSummary = new HashMap<SootMethod, HashMutableDirectedGraph<EquivalentValue>>();
 		 
 //		 doSimpleConservativeDataFlowAnalysis();
 	}
@@ -45,7 +45,8 @@ public class ClassInfoFlowAnalysis
 			// request its own DataFlowGraph, we need this simple version first.
 			if(!methodToInfoFlowSummary.containsKey(method))
 			{
-				HashMutableDirectedGraph dataFlowGraph = simpleConservativeInfoFlowAnalysis(method);
+				HashMutableDirectedGraph<EquivalentValue> dataFlowGraph =
+						simpleConservativeInfoFlowAnalysis(method);
 				methodToInfoFlowSummary.put(method, dataFlowGraph);
 			}
 			
@@ -68,8 +69,8 @@ public class ClassInfoFlowAnalysis
 		return methodToInfoFlowAnalysis.get(method);
 	}
 	
-	public MutableDirectedGraph getMethodInfoFlowSummary(SootMethod method) { return getMethodInfoFlowSummary(method, true); }
-	public HashMutableDirectedGraph getMethodInfoFlowSummary(SootMethod method, boolean doFullAnalysis)
+	public MutableDirectedGraph<EquivalentValue> getMethodInfoFlowSummary(SootMethod method) { return getMethodInfoFlowSummary(method, true); }
+	public HashMutableDirectedGraph<EquivalentValue> getMethodInfoFlowSummary(SootMethod method, boolean doFullAnalysis)
 	{
 		if(!methodToInfoFlowSummary.containsKey(method))
 		{
@@ -78,7 +79,8 @@ public class ClassInfoFlowAnalysis
 			// First do simple version that doesn't follow invoke expressions
 			// The "smart" version will be computed later, but since it may
 			// request its own DataFlowGraph, we need this simple version first.
-			HashMutableDirectedGraph dataFlowGraph = simpleConservativeInfoFlowAnalysis(method);
+			HashMutableDirectedGraph<EquivalentValue> dataFlowGraph =
+					simpleConservativeInfoFlowAnalysis(method);
 			methodToInfoFlowSummary.put(method, dataFlowGraph);
 			
 			// Then do smart version that does follow invoke expressions, if possible
@@ -155,7 +157,7 @@ public class ClassInfoFlowAnalysis
 	}
 //*/	
 	/** Does not require any fixed point calculation */
-	private HashMutableDirectedGraph simpleConservativeInfoFlowAnalysis(SootMethod sm)
+	private HashMutableDirectedGraph<EquivalentValue> simpleConservativeInfoFlowAnalysis(SootMethod sm)
 	{
 		// Constructs a graph representing the data flow between fields, parameters, and the
 		// return value of this method.  The graph nodes are EquivalentValue wrapped Refs.
@@ -174,10 +176,9 @@ public class ClassInfoFlowAnalysis
 		HashSet<EquivalentValue> fieldsStaticsParamsAccessed = new HashSet<EquivalentValue>();		
 
 		// Get list of fields, globals, and parameters that are accessed
-		Iterator stmtIt = g.iterator();
-		while(stmtIt.hasNext())
+		for (Unit u : g)
 		{
-			Stmt s = (Stmt) stmtIt.next();
+			Stmt s = (Stmt) u;
 			if( s instanceof IdentityStmt )
 			{
 				IdentityStmt is = (IdentityStmt) s;
@@ -232,9 +233,8 @@ public class ClassInfoFlowAnalysis
 		}
 		
 		// Add every relevant field of this class (static methods don't get non-static fields)
-		for(Iterator it = sm.getDeclaringClass().getFields().iterator(); it.hasNext(); )
+		for (SootField sf : sm.getDeclaringClass().getFields())
 		{
-			SootField sf = (SootField) it.next();
 			if(sf.isStatic() || !sm.isStatic())
 			{
 				EquivalentValue fieldRefEqVal = InfoFlowAnalysis.getNodeForFieldRef(sm, sf);
@@ -249,10 +249,8 @@ public class ClassInfoFlowAnalysis
 			superclass = sm.getDeclaringClass().getSuperclass();
 		while(superclass.hasSuperclass()) // we don't want to process Object
 		{
-	        Iterator scFieldsIt = superclass.getFields().iterator();
-	        while(scFieldsIt.hasNext())
+			for (SootField scField : superclass.getFields())
 	        {
-				SootField scField = (SootField) scFieldsIt.next();
 				if(scField.isStatic() || !sm.isStatic())
 				{
 					EquivalentValue fieldRefEqVal = InfoFlowAnalysis.getNodeForFieldRef(sm, scField);
@@ -310,7 +308,7 @@ public class ClassInfoFlowAnalysis
 	}
 	
 	/** Does not require the method to have a body */
-	public HashMutableDirectedGraph triviallyConservativeInfoFlowAnalysis(SootMethod sm)
+	public HashMutableDirectedGraph<EquivalentValue> triviallyConservativeInfoFlowAnalysis(SootMethod sm)
 	{
 		HashSet<EquivalentValue> fieldsStaticsParamsAccessed = new HashSet<EquivalentValue>();
 		
@@ -371,10 +369,8 @@ public class ClassInfoFlowAnalysis
 			dataFlowGraph.addNode(InfoFlowAnalysis.getNodeForReturnRef(sm));
 		}
 		
-		ThisRef thisRef = null;
 		if(!sm.isStatic())
 		{
-			thisRef = new ThisRef(sootClass.getType());
 			dataFlowGraph.addNode(InfoFlowAnalysis.getNodeForThisRef(sm));
 			fieldsStaticsParamsAccessed.add(InfoFlowAnalysis.getNodeForThisRef(sm));
 		}
diff --git a/src/soot/jimple/toolkits/infoflow/ClassLocalObjectsAnalysis.java b/src/soot/jimple/toolkits/infoflow/ClassLocalObjectsAnalysis.java
index 24d72a888..832f97844 100644
--- a/src/soot/jimple/toolkits/infoflow/ClassLocalObjectsAnalysis.java
+++ b/src/soot/jimple/toolkits/infoflow/ClassLocalObjectsAnalysis.java
@@ -187,10 +187,8 @@ public class ClassLocalObjectsAnalysis
 		// Get list of reachable methods declared in this class
 		// Also get list of fields declared in this class
 		List<SootField> allFields = new ArrayList<SootField>();
-		Iterator fieldsIt = sc.getFields().iterator();
-		while(fieldsIt.hasNext())
+		for (SootField field : sc.getFields())
 		{
-			SootField field = (SootField) fieldsIt.next();
 			allFields.add(field);
 		}
 		
@@ -200,10 +198,8 @@ public class ClassLocalObjectsAnalysis
 			superclass = superclass.getSuperclass();
 		while(superclass.hasSuperclass()) // we don't want to process Object
 		{
-	        Iterator scFieldsIt = superclass.getFields().iterator();
-	        while(scFieldsIt.hasNext())
+			for (SootField scField : superclass.getFields())
 	        {
-				SootField scField = (SootField) scFieldsIt.next();
 				allFields.add(scField);
 	        }
 			superclass = superclass.getSuperclass();
diff --git a/src/soot/jimple/toolkits/infoflow/InfoFlowAnalysis.java b/src/soot/jimple/toolkits/infoflow/InfoFlowAnalysis.java
index 2c1584d70..48f90ab5d 100644
--- a/src/soot/jimple/toolkits/infoflow/InfoFlowAnalysis.java
+++ b/src/soot/jimple/toolkits/infoflow/InfoFlowAnalysis.java
@@ -105,8 +105,8 @@ public class InfoFlowAnalysis
 	/** Returns a BACKED MutableDirectedGraph whose nodes are EquivalentValue 
 	  * wrapped Refs. It's perfectly safe to modify this graph, just so long as 
 	  * new nodes are EquivalentValue wrapped Refs. */
-	public HashMutableDirectedGraph getMethodInfoFlowSummary(SootMethod sm) { return getMethodInfoFlowSummary(sm, true); }
-	public HashMutableDirectedGraph getMethodInfoFlowSummary(SootMethod sm, boolean doFullAnalysis)
+	public HashMutableDirectedGraph<EquivalentValue> getMethodInfoFlowSummary(SootMethod sm) { return getMethodInfoFlowSummary(sm, true); }
+	public HashMutableDirectedGraph<EquivalentValue> getMethodInfoFlowSummary(SootMethod sm, boolean doFullAnalysis)
 	{
 		ClassInfoFlowAnalysis cdfa = getClassInfoFlowAnalysis(sm.getDeclaringClass());
 		return cdfa.getMethodInfoFlowSummary(sm, doFullAnalysis);
@@ -190,11 +190,12 @@ public class InfoFlowAnalysis
 		return new CachedEquivalentValue(new ThisRef(sm.getDeclaringClass().getType()));
 	}
 	
-	protected HashMutableDirectedGraph getInvokeInfoFlowSummary(InvokeExpr ie, Stmt is, SootMethod context)
+	protected HashMutableDirectedGraph<EquivalentValue> getInvokeInfoFlowSummary(
+			InvokeExpr ie, Stmt is, SootMethod context)
 	{
 		// get the data flow graph for each possible target of ie,
 		// then combine them conservatively and return the result.
-		HashMutableDirectedGraph ret = null;
+		HashMutableDirectedGraph<EquivalentValue> ret = null;
 		
 		SootMethodRef methodRef = ie.getMethodRef();
 		String subSig = methodRef.resolve().getSubSignature();
@@ -207,16 +208,17 @@ public class InfoFlowAnalysis
 			// and not just a class initializer or other unintended control flow.
 			if(target.getSubSignature().equals(subSig))
 			{
-				HashMutableDirectedGraph ifs = getMethodInfoFlowSummary(target, context.getDeclaringClass().isApplicationClass());
+				HashMutableDirectedGraph<EquivalentValue> ifs = getMethodInfoFlowSummary(
+						target, context.getDeclaringClass().isApplicationClass());
 				if(ret == null)
 					ret = ifs;
 				else
 				{
-					for(Object node : ifs.getNodes())
+					for(EquivalentValue node : ifs.getNodes())
 					{
 						if(!ret.containsNode(node))
 							ret.addNode(node);
-						for(Object succ : ifs.getSuccsOf(node))
+						for(EquivalentValue succ : ifs.getSuccsOf(node))
 							ret.addEdge(node, succ);
 					}
 				}
@@ -227,7 +229,8 @@ public class InfoFlowAnalysis
 //		return getMethodInfoFlowSummary(methodRef.resolve(), context.getDeclaringClass().isApplicationClass());
 	}
 	
-	protected MutableDirectedGraph getInvokeAbbreviatedInfoFlowGraph(InvokeExpr ie, SootMethod context)
+	protected MutableDirectedGraph<EquivalentValue> getInvokeAbbreviatedInfoFlowGraph(
+			InvokeExpr ie, SootMethod context)
 	{
 		// get the data flow graph for each possible target of ie,
 		// then combine them conservatively and return the result.
@@ -235,24 +238,22 @@ public class InfoFlowAnalysis
 		return getMethodInfoFlowAnalysis(methodRef.resolve()).getMethodAbbreviatedInfoFlowGraph();
 	}
 	
-	public static void printInfoFlowSummary(DirectedGraph g)
+	public static void printInfoFlowSummary(DirectedGraph<EquivalentValue> g)
 	{
-		Iterator nodeIt = g.iterator();
-		if(!nodeIt.hasNext())
+		if(g.size() > 0)
 			G.v().out.println("    " + " --> ");
-		while(nodeIt.hasNext())
+		for (EquivalentValue node : g)
 		{
-			Object node = nodeIt.next();
-			List sources = g.getPredsOf(node);
-			Iterator sourcesIt = sources.iterator();
-			if(!sourcesIt.hasNext())
+			List<EquivalentValue> sources = g.getPredsOf(node);
+			if(sources.isEmpty())
 				continue;
 			G.v().out.print("    [ ");
 			int sourcesnamelength = 0;
 			int lastnamelength = 0;
-			while(sourcesIt.hasNext())
+			int idx = 0;
+			for (EquivalentValue t : sources)
 			{
-				Value v = ((EquivalentValue) sourcesIt.next()).getValue();
+				Value v = t.getValue();
 				if(v instanceof FieldRef)
 				{
 					FieldRef fr = (FieldRef) v;
@@ -278,7 +279,7 @@ public class InfoFlowAnalysis
 						sourcesnamelength = lastnamelength;
 					G.v().out.print(name);
 				}
-				if(sourcesIt.hasNext())
+				if((idx++) < sources.size())
 					G.v().out.print("\n      ");
 			}
 			for(int i = 0; i < sourcesnamelength - lastnamelength; i++)
@@ -287,11 +288,11 @@ public class InfoFlowAnalysis
 		}
 	}
 		
-	public static void printGraphToDotFile(String filename, DirectedGraph graph, String graphname, boolean onePage)
+	public static void printGraphToDotFile(String filename,
+			DirectedGraph<EquivalentValue> graph, String graphname, boolean onePage)
 	{
 		// this makes the node name unique
 		nodecount = 0; // reset node counter first.
-		Hashtable nodeindex = new Hashtable(graph.size());
 		
 		// file name is the method name + .dot
 		DotGraph canvas = new DotGraph(filename);
@@ -302,20 +303,13 @@ public class InfoFlowAnalysis
 		canvas.setNodeShape(DotGraphConstants.NODE_SHAPE_BOX);
 		canvas.setGraphLabel(graphname);
 		
-		Iterator nodesIt = graph.iterator();
-		while (nodesIt.hasNext())
+		for (EquivalentValue node : graph)
 		{
-			Object node = nodesIt.next();
-
 			canvas.drawNode(getNodeName(node));
 			canvas.getNode(getNodeName(node)).setLabel(getNodeLabel(node));
 
-			Iterator succsIt = graph.getSuccsOf(node).iterator();
-			
-			while (succsIt.hasNext())
+			for (EquivalentValue s : graph.getSuccsOf(node))
 			{
-				Object s= succsIt.next();
-
 				canvas.drawNode(getNodeName(s));
 				canvas.getNode(getNodeName(s)).setLabel(getNodeLabel(s));
 
@@ -327,7 +321,7 @@ public class InfoFlowAnalysis
 	}
 
 	static int nodecount = 0;
-	static Map nodeToNodeName = new HashMap();
+//	static Map nodeToNodeName = new HashMap();
 	public static String getNodeName(Object o)
 	{
 //		if(!nodeToNodeName.containsKey(o)) // Since this uses all different kinds of objects, we
diff --git a/src/soot/jimple/toolkits/infoflow/SimpleMethodInfoFlowAnalysis.java b/src/soot/jimple/toolkits/infoflow/SimpleMethodInfoFlowAnalysis.java
index 0691d8f3b..9063eec02 100644
--- a/src/soot/jimple/toolkits/infoflow/SimpleMethodInfoFlowAnalysis.java
+++ b/src/soot/jimple/toolkits/infoflow/SimpleMethodInfoFlowAnalysis.java
@@ -50,9 +50,8 @@ public class SimpleMethodInfoFlowAnalysis extends ForwardFlowAnalysis<Unit, Flow
 		}
 		
 		// Add every field of this class
-		for(Iterator it = sm.getDeclaringClass().getFields().iterator(); it.hasNext(); )
+		for (SootField sf : sm.getDeclaringClass().getFields())
 		{
-			SootField sf = (SootField) it.next();
 			EquivalentValue fieldRefEqVal = InfoFlowAnalysis.getNodeForFieldRef(sm, sf);
 			if(!infoFlowGraph.containsNode(fieldRefEqVal))
 				infoFlowGraph.addNode(fieldRefEqVal);
@@ -64,10 +63,8 @@ public class SimpleMethodInfoFlowAnalysis extends ForwardFlowAnalysis<Unit, Flow
 			superclass = sm.getDeclaringClass().getSuperclass();
 		while(superclass.hasSuperclass()) // we don't want to process Object
 		{
-	        Iterator scFieldsIt = superclass.getFields().iterator();
-	        while(scFieldsIt.hasNext())
+			for (SootField scField : superclass.getFields())
 	        {
-				SootField scField = (SootField) scFieldsIt.next();
 				EquivalentValue fieldRefEqVal = InfoFlowAnalysis.getNodeForFieldRef(sm, scField);
 				if(!infoFlowGraph.containsNode(fieldRefEqVal))
 					infoFlowGraph.addNode(fieldRefEqVal);
@@ -212,7 +209,8 @@ public class SimpleMethodInfoFlowAnalysis extends ForwardFlowAnalysis<Unit, Flow
 			EquivalentValue sourceEqVal = new CachedEquivalentValue(source);
 			if(sinkEqVal.equals(sourceEqVal))
 				continue;
-			Pair<EquivalentValue,EquivalentValue> pair = new Pair<>(sinkEqVal, sourceEqVal);
+			Pair<EquivalentValue,EquivalentValue> pair = new Pair<EquivalentValue,EquivalentValue>(
+					sinkEqVal, sourceEqVal);
 			if(!fs.contains(pair))
 			{
 				fs.add(pair);
@@ -254,7 +252,8 @@ public class SimpleMethodInfoFlowAnalysis extends ForwardFlowAnalysis<Unit, Flow
 				EquivalentValue sinkEqVal = new CachedEquivalentValue(sink);
 				if(sinkEqVal.equals(sourceEqVal))
 					continue;
-				Pair<EquivalentValue,EquivalentValue> pair = new Pair<>(sinkEqVal, sourceEqVal);
+				Pair<EquivalentValue,EquivalentValue> pair = new Pair<EquivalentValue,EquivalentValue>(
+						sinkEqVal, sourceEqVal);
 				if(!fs.contains(pair))
 				{
 					fs.add(pair);
@@ -294,7 +293,7 @@ public class SimpleMethodInfoFlowAnalysis extends ForwardFlowAnalysis<Unit, Flow
 				// if the sink is the return value
 					// add node to list of return value sources
 
-	protected List handleInvokeExpr(InvokeExpr ie, Stmt is,
+	protected List<Value> handleInvokeExpr(InvokeExpr ie, Stmt is,
                                 FlowSet<Pair<EquivalentValue,EquivalentValue>> fs)
 	{
 		// get the data flow graph
@@ -490,7 +489,7 @@ public class SimpleMethodInfoFlowAnalysis extends ForwardFlowAnalysis<Unit, Flow
 				}
 			}
 			
-			List sources = new ArrayList();
+			List<Value> sources = new ArrayList<Value>();
 			boolean interestingFlow = true;
 			
 			if(rv instanceof Local)
@@ -569,21 +568,13 @@ public class SimpleMethodInfoFlowAnalysis extends ForwardFlowAnalysis<Unit, Flow
 			{
 				if(flowsToDataStructure)
 				{
-					Iterator sourcesIt = sources.iterator();
-					while(sourcesIt.hasNext())
-					{
-						Value source = (Value) sourcesIt.next();
+					for (Value source : sources)
 						handleFlowsToDataStructure(sink, source, changedFlow);
-					}
 				}
 				else
 				{
-					Iterator sourcesIt = sources.iterator();
-					while(sourcesIt.hasNext())
-					{
-						Value source = (Value) sourcesIt.next();
+					for (Value source : sources)
 						handleFlowsToValue(sink, source, changedFlow);
-					}
 				}
 			}
 		}
@@ -618,7 +609,8 @@ public class SimpleMethodInfoFlowAnalysis extends ForwardFlowAnalysis<Unit, Flow
 		EquivalentValue sourceEqVal = new CachedEquivalentValue(source);
 		if(sinkEqVal.equals(sourceEqVal))
 			return;
-		Pair<EquivalentValue,EquivalentValue> pair = new Pair<>(sinkEqVal, sourceEqVal);
+		Pair<EquivalentValue,EquivalentValue> pair = new Pair<EquivalentValue,EquivalentValue>(
+				sinkEqVal, sourceEqVal);
 		if(!entrySet.contains(pair))
 		{
 			entrySet.add(pair);
@@ -631,7 +623,8 @@ public class SimpleMethodInfoFlowAnalysis extends ForwardFlowAnalysis<Unit, Flow
 		EquivalentValue sourceEqVal = new CachedEquivalentValue(source);
 		if(sinkEqVal.equals(sourceEqVal))
 			return;
-		Pair<EquivalentValue,EquivalentValue> pair = new Pair<>(sinkEqVal, sourceEqVal);
+		Pair<EquivalentValue,EquivalentValue> pair = new Pair<EquivalentValue,EquivalentValue>(
+				sinkEqVal, sourceEqVal);
 		if(!emptySet.contains(pair))
 		{
 			emptySet.add(pair);
diff --git a/tests/soot/toolkits/graph/TestDominance.java b/tests/soot/toolkits/graph/TestDominance.java
index 1e862cac7..3f7a552c1 100644
--- a/tests/soot/toolkits/graph/TestDominance.java
+++ b/tests/soot/toolkits/graph/TestDominance.java
@@ -45,21 +45,19 @@ import soot.toolkits.graph.pdg.MHGDominatorTree;
 
 public class TestDominance {
 
-    public Set<Integer> kid_ids(DominatorNode dn) {
+    public Set<Integer> kid_ids(DominatorNode<Node> dn) {
         Set<Integer> kids = new HashSet<Integer>();
-        for (Object o : dn.getChildren()) {
-            DominatorNode dkid = (DominatorNode)o;
-            Node kid = (Node)dkid.getGode();
+        for (DominatorNode<Node> dkid : dn.getChildren()) {
+            Node kid = dkid.getGode();
             kids.add(kid.id);
         }
         return kids;
     }
 
-    public Map<Integer,DominatorNode> kid_map(DominatorNode dn) {
-        Map<Integer,DominatorNode> kids = new HashMap<Integer,DominatorNode>();
-        for (Object o : dn.getChildren()) {
-            DominatorNode dkid = (DominatorNode)o;
-            Node kid = (Node)dkid.getGode();
+    public Map<Integer,DominatorNode<Node>> kid_map(DominatorNode<Node> dn) {
+        Map<Integer,DominatorNode<Node>> kids = new HashMap<Integer,DominatorNode<Node>>();
+        for (DominatorNode<Node> dkid : dn.getChildren()) {
+            Node kid = dkid.getGode();
             kids.put(kid.id, dkid);
         }
         return kids;
@@ -71,11 +69,11 @@ public class TestDominance {
         Node n = new Node(1).addkid((new Node(2)).addkid(x)).addkid((new Node(3)).addkid(x));
         Graph g = new Graph(n);
         MHGDominatorsFinder<Node> finder = new MHGDominatorsFinder<Node>(g);
-        DominatorTree tree = new DominatorTree(finder);
+        DominatorTree<Node> tree = new DominatorTree<Node>(finder);
         assertThat(tree.getHeads().size(), is(1));
 
-        DominatorNode head = tree.getHeads().get(0);
-        assertThat(((Node)head.getGode()).id, is(1));
+        DominatorNode<Node> head = tree.getHeads().get(0);
+        assertThat(head.getGode().id, is(1));
 
         Set<Integer> kids = kid_ids(head);
         assertThat(kids.size(), is(3));
@@ -108,17 +106,17 @@ public class TestDominance {
         Graph g = new Graph(n1);
 
         MHGDominatorsFinder<Node> finder = new MHGDominatorsFinder<Node>(g);
-        DominatorTree tree = new DominatorTree(finder);
+        DominatorTree<Node> tree = new DominatorTree<Node>(finder);
         assertThat(tree.getHeads().size(), is(1));
 
-        DominatorNode n = tree.getHeads().get(0);
-        assertThat(((Node)n.getGode()).id, is(1));
+        DominatorNode<Node> n = tree.getHeads().get(0);
+        assertThat(n.getGode().id, is(1));
         Set<Integer> kids = kid_ids(n);
         assertThat(kids.size(), is(4));
         assertThat(kids, contains(2, 3, 9, 11));
 
-        Map<Integer, DominatorNode> KM = kid_map(n);
-        DominatorNode m = KM.get(2);
+        Map<Integer, DominatorNode<Node>> KM = kid_map(n);
+        DominatorNode<Node> m = KM.get(2);
         kids = kid_ids(m);
         assertThat(kids.size(), is(0));
 
@@ -180,17 +178,17 @@ public class TestDominance {
         Graph g = new Graph(n1);
 
         MHGDominatorsFinder<Node> finder = new MHGDominatorsFinder<Node>(g);
-        MHGDominatorTree tree = new MHGDominatorTree(finder);
+        MHGDominatorTree<Node> tree = new MHGDominatorTree<Node>(finder);
         assertThat(tree.getHeads().size(), is(1));
 
-        DominatorNode n = tree.getHeads().get(0);
-        assertThat(((Node)n.getGode()).id, is(1));
+        DominatorNode<Node> n = tree.getHeads().get(0);
+        assertThat(n.getGode().id, is(1));
         Set<Integer> kids = kid_ids(n);
         assertThat(kids.size(), is(2));
         assertThat(kids, contains(2, 3));
 
-        Map<Integer, DominatorNode> KM = kid_map(n);
-        DominatorNode m = KM.get(2);
+        Map<Integer, DominatorNode<Node>> KM = kid_map(n);
+        DominatorNode<Node> m = KM.get(2);
         kids = kid_ids(m);
         assertThat(kids.size(), is(0));
 
@@ -215,12 +213,11 @@ public class TestDominance {
         // ---------- now post-dom --------------
 
         MHGPostDominatorsFinder<Node> pfinder = new MHGPostDominatorsFinder<Node>(g);
-        tree = new MHGDominatorTree(pfinder);
+        tree = new MHGDominatorTree<Node>(pfinder);
 
-        Map<Integer,DominatorNode> heads = new HashMap<Integer,DominatorNode>();
-        for (Object o : tree.getHeads()) {
-            DominatorNode dhead = (DominatorNode)o;
-            Node head = (Node)dhead.getGode();
+        Map<Integer,DominatorNode<Node>> heads = new HashMap<Integer,DominatorNode<Node>>();
+        for (DominatorNode<Node> dhead : tree.getHeads()) {
+            Node head = dhead.getGode();
             heads.put(head.id, dhead);
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
