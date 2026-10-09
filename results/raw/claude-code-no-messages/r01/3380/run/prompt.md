This repository contains a bug that was introduced at some point in the past
and later fixed. Below is the bug-fixing commit information.

Your task is to identify the commit(s) that introduced the bug, and explain
your reasoning.

[Bug-Fixing Commit]
- Commit hash: c39570755c737cb066b9a579ee68612c7ee13f5d
- Commit message: 
- Diff:
```
commit c39570755c737cb066b9a579ee68612c7ee13f5d
Author: jiangxincode <jiangxinnju@163.com>
Date:   Sun May 19 12:41:55 2019 +0800
---
 .../com/vladium/emma/report/IReportProperties.java |  7 ++-
 .../com/vladium/emma/report/ReportProperties.java  | 54 +++++++++++-----------
 .../vladium/emma/report/html/ReportGenerator.java  | 12 ++---
 .../vladium/emma/report/txt/ReportGenerator.java   |  2 +-
 .../vladium/emma/report/xml/ReportGenerator.java   |  4 +-
 5 files changed, 39 insertions(+), 40 deletions(-)

diff --git a/src/main/java/com/vladium/emma/report/IReportProperties.java b/src/main/java/com/vladium/emma/report/IReportProperties.java
index 907d9c1..87e6bf4 100755
--- a/src/main/java/com/vladium/emma/report/IReportProperties.java
+++ b/src/main/java/com/vladium/emma/report/IReportProperties.java
@@ -21,6 +21,9 @@ interface IReportProperties
     
     String PREFIX = "report.";
     
+    // parameter:
+    String IN_ENCODING = "in.encoding";
+    
     // parameter:
     String OUT_ENCODING     = "out.encoding";
     String OUT_DIR          = "out.dir";
@@ -68,10 +71,6 @@ interface IReportProperties
     String METRICS          = "metrics"; // comma-separated list of (column name:metric) pairs
     char MSEPARATOR         = ':';
 
-    // addition parameters by terry
-    String OUTPUT_ENCODING = "html.outputEncoding";
-    String SOURCE_ENCODING = "html.sourceEncoding";
-
     // defaults:
     
     String DEFAULT_UNITS_TYPE = INSTR_UNITS;
diff --git a/src/main/java/com/vladium/emma/report/ReportProperties.java b/src/main/java/com/vladium/emma/report/ReportProperties.java
index 8518d6c..7b51001 100755
--- a/src/main/java/com/vladium/emma/report/ReportProperties.java
+++ b/src/main/java/com/vladium/emma/report/ReportProperties.java
@@ -38,6 +38,30 @@ abstract class ReportProperties implements IAppErrorCodes
        
     public static final class ParsedProperties
     {
+        public void setInEncoding (final String inEncoding)
+        {
+            if ($assert.ENABLED) $assert.ASSERT (inEncoding != null, "null input: inEncoding");
+            
+            m_inEncoding = inEncoding;
+        }
+
+        public String getInEncoding ()
+        {
+            return m_inEncoding;
+        }
+        
+        public void setOutEncoding (final String outEncoding)
+        {
+            if ($assert.ENABLED) $assert.ASSERT (outEncoding != null, "null input: outEncoding");
+            
+            m_outEncoding = outEncoding;
+        }
+
+        public String getOutEncoding ()
+        {
+            return m_outEncoding;
+        }
+        
         public void setOutDir (final File outDir)
         {
             if ($assert.ENABLED) $assert.ASSERT (outDir != null, "null input: outDir");
@@ -155,12 +179,10 @@ abstract class ReportProperties implements IAppErrorCodes
                 $assert.ASSERT (m_columnOrder != null, "m_columnOrder not set");
                 $assert.ASSERT (m_sortOrder != null, "m_sortOrder not set");
                 $assert.ASSERT (m_metrics != null, "m_metrics not set");
-                $assert.ASSERT (m_sourceEncoding != null, "m_sourceEncoding not set");
-                $assert.ASSERT (m_outputEncoding != null, "m_outputEncoding not set");
             }
         }
 
-
+        private String m_inEncoding;
         private String m_outEncoding;
         private File m_outDir;
         private File m_outFile;
@@ -176,28 +198,6 @@ abstract class ReportProperties implements IAppErrorCodes
         private int [] m_columnOrder; // attribute IDs [order indicates column order] 
         private int [] m_sortOrder; // if m_sortOrder[i+1]>0 , sort m_columnOrder[m_sortOrder[i]] in ascending order
         private IntIntMap m_metrics; // pass criteria (column attribute ID -> metric)
-
-        // addition parameters by terry
-        private String m_outputEncoding;
-        private String m_sourceEncoding;
-
-        public String getSourceEncoding() {
-            return m_sourceEncoding;
-        }
-
-        public void setSourceEncoding(String sourceEncoding) {
-            if ($assert.ENABLED) $assert.ASSERT (sourceEncoding != null, "null input: sourceEncoding");
-            this.m_sourceEncoding = sourceEncoding;
-        }
-
-        public String getOutputEncoding() {
-            return m_outputEncoding;
-        }
-
-        public void setOutputEncoding(String outputEncoding) {
-            if ($assert.ENABLED) $assert.ASSERT (outputEncoding != null, "null input: outputEncoding");
-            this.m_outputEncoding = outputEncoding;
-        }
     } // end of nested class
     
     
@@ -256,8 +256,8 @@ abstract class ReportProperties implements IAppErrorCodes
         
         final ParsedProperties result = new ParsedProperties ();
         {
-            result.setOutputEncoding(getReportProperty (properties, type, IReportProperties.OUTPUT_ENCODING, false, false));
-            result.setSourceEncoding(getReportProperty (properties, type, IReportProperties.SOURCE_ENCODING, false, false));
+            result.setOutEncoding(getReportProperty (properties, type, IReportProperties.OUT_ENCODING, false, false));
+            result.setInEncoding(getReportProperty (properties, type, IReportProperties.IN_ENCODING, false, false));
         }
         
         // TODO: outDirName is no longer supported
diff --git a/src/main/java/com/vladium/emma/report/html/ReportGenerator.java b/src/main/java/com/vladium/emma/report/html/ReportGenerator.java
index a7a34f7..2e4efb1 100755
--- a/src/main/java/com/vladium/emma/report/html/ReportGenerator.java
+++ b/src/main/java/com/vladium/emma/report/html/ReportGenerator.java
@@ -141,7 +141,7 @@ final class ReportGenerator extends AbstractReportGenerator
             
             m_log.info ("writing [" + getType () + "] report to [" + fullOutFile.getAbsolutePath () + "] ...");
             
-            out = openOutFile (fullOutFile, m_settings.getOutputEncoding(), true);
+            out = openOutFile (fullOutFile, m_settings.getOutEncoding(), true);
             
             final int [] columns = m_settings.getColumnOrder ();
             final StringBuffer buf = new StringBuffer ();
@@ -319,7 +319,7 @@ final class ReportGenerator extends AbstractReportGenerator
             
             final File outFile = getItemFile (NESTED_ITEMS_PARENT_DIR, m_reportIDNamespace.getID (getItemKey (item)));
             
-            out = openOutFile (Files.newFile (m_settings.getOutDir (), outFile), m_settings.getOutputEncoding (), true);
+            out = openOutFile (Files.newFile (m_settings.getOutDir (), outFile), m_settings.getOutEncoding (), true);
             
             final int [] columns = m_settings.getColumnOrder ();            
             final StringBuffer buf = new StringBuffer ();
@@ -436,7 +436,7 @@ final class ReportGenerator extends AbstractReportGenerator
         {
             final File outFile = getItemFile (NESTED_ITEMS_PARENT_DIR, m_reportIDNamespace.getID (getItemKey (item)));
 
-            out = openOutFile (Files.newFile (m_settings.getOutDir (), outFile), m_settings.getOutputEncoding (), true);
+            out = openOutFile (Files.newFile (m_settings.getOutDir (), outFile), m_settings.getOutEncoding (), true);
 
             final int [] columns = m_settings.getColumnOrder ();
             final StringBuffer buf = new StringBuffer ();
@@ -612,7 +612,7 @@ final class ReportGenerator extends AbstractReportGenerator
             final File outFile = getItemFile (NESTED_ITEMS_PARENT_DIR, m_reportIDNamespace.getID (getItemKey (item)));
             
             // TODO: deal with overwrites
-            out = openOutFile (Files.newFile (m_settings.getOutDir (), outFile), m_settings.getOutputEncoding (), true);
+            out = openOutFile (Files.newFile (m_settings.getOutDir (), outFile), m_settings.getOutEncoding (), true);
             
             final int [] columns = m_settings.getColumnOrder ();            
             final StringBuffer buf = new StringBuffer ();
@@ -756,7 +756,7 @@ final class ReportGenerator extends AbstractReportGenerator
     
     private HTMLDocument createPage (final String title)
     {
-        final HTMLDocument page = new HTMLDocument (title, m_settings.getOutputEncoding ());
+        final HTMLDocument page = new HTMLDocument (title, m_settings.getOutEncoding ());
         page.addStyle (CSS); // TODO: split by visit type
         
         return page;
@@ -1135,7 +1135,7 @@ final class ReportGenerator extends AbstractReportGenerator
                 BufferedReader in = null;
                 try
                 {
-                    in = new BufferedReader (new InputStreamReader (new FileInputStream(srcFile), m_settings.getSourceEncoding ()), IO_BUF_SIZE);
+                    in = new BufferedReader (new InputStreamReader (new FileInputStream(srcFile), m_settings.getInEncoding ()), IO_BUF_SIZE);
 
                     final boolean markupCoverage = m_hasLineNumberInfo;
                     
diff --git a/src/main/java/com/vladium/emma/report/txt/ReportGenerator.java b/src/main/java/com/vladium/emma/report/txt/ReportGenerator.java
index 11a06e3..6d2529c 100755
--- a/src/main/java/com/vladium/emma/report/txt/ReportGenerator.java
+++ b/src/main/java/com/vladium/emma/report/txt/ReportGenerator.java
@@ -113,7 +113,7 @@ final class ReportGenerator extends AbstractReportGenerator
         
         m_log.info ("writing [" + getType () + "] report to [" + fullOutFile.getAbsolutePath () + "] ...");
         
-        openOutFile (fullOutFile, m_settings.getOutputEncoding (), true);
+        openOutFile (fullOutFile, m_settings.getOutEncoding (), true);
         
         // build ID stamp:
         try
diff --git a/src/main/java/com/vladium/emma/report/xml/ReportGenerator.java b/src/main/java/com/vladium/emma/report/xml/ReportGenerator.java
index 5baebe4..0584830 100755
--- a/src/main/java/com/vladium/emma/report/xml/ReportGenerator.java
+++ b/src/main/java/com/vladium/emma/report/xml/ReportGenerator.java
@@ -106,10 +106,10 @@ final class ReportGenerator extends AbstractReportGenerator
             
             m_log.info ("writing [" + getType () + "] report to [" + fullOutFile.getAbsolutePath () + "] ...");
             
-            openOutFile (fullOutFile, m_settings.getOutputEncoding (), true);
+            openOutFile (fullOutFile, m_settings.getOutEncoding (), true);
             
             // XML header:
-            m_out.write ("<?xml version=\"1.0\" encoding=\"" + m_settings.getOutputEncoding () + "\"?>");
+            m_out.write ("<?xml version=\"1.0\" encoding=\"" + m_settings.getOutEncoding () + "\"?>");
             
             // build ID stamp:
             try
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
