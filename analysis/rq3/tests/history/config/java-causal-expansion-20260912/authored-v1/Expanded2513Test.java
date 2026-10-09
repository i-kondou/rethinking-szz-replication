import org.junit.Test;
import static org.junit.Assert.*;
import java.nio.file.*;
import java.util.*;
import javax.tools.*;
import spoon.Launcher;
public class Expanded2513Test {
  static String input(String pkg) {
    return "package " + pkg + "; public class DigestUtil { private static final int STREAM_BUFFER_LENGTH=1024; public static int digest(){return STREAM_BUFFER_LENGTH;} public static byte[] allocate(){return new byte[STREAM_BUFFER_LENGTH];} }";
  }
  static String generate(String pkg, boolean checkImport) throws Exception {
    Path root=Files.createTempDirectory("spoon-causal-"); Path source=root.resolve("input").resolve(pkg.replace('.', '/')).resolve("DigestUtil.java");
    Files.createDirectories(source.getParent());Files.write(source,input(pkg).getBytes("UTF-8"));
    Launcher launcher=new Launcher(); launcher.addInputResource(source.toString());launcher.setSourceOutputDirectory(root.resolve("output").toFile());launcher.run();
    Path generated=root.resolve("output").resolve(pkg.replace('.', '/')).resolve("DigestUtil.java");
    assertTrue("generated file control",Files.exists(generated));String text=new String(Files.readAllBytes(generated),"UTF-8");
    System.out.println("OUTPUT_2513 package="+pkg+"\n"+text+"\nEND_OUTPUT_2513");
    boolean selfImport=text.contains("import static "+pkg+".DigestUtil.STREAM_BUFFER_LENGTH;");
    if(checkImport) assertFalse("TARGET_2513_SELF_IMPORT",selfImport);
    else {
      JavaCompiler compiler=ToolProvider.getSystemJavaCompiler();DiagnosticCollector<JavaFileObject> ds=new DiagnosticCollector<JavaFileObject>();
      StandardJavaFileManager fm=compiler.getStandardFileManager(ds,Locale.US,null); Path classes=Files.createDirectory(root.resolve("compiled"));
      try {
        boolean ok=compiler.getTask(null,fm,ds,Arrays.asList("-proc:none","-d",classes.toString()),null,fm.getJavaFileObjects(generated.toFile())).call();
        System.out.println("OBS_2513 package="+pkg+" javac="+ok+" diagnostics="+ds.getDiagnostics());
        assertTrue("TARGET_2513_OUTPUT_COMPILE",ok);
      } finally {fm.close();}
    }
    return text;
  }
  @Test public void collidingPackageHasNoPrivateSelfImport() throws Exception {generate("example.digest",true);}
  @Test public void collidingPackageOutputCompiles() throws Exception {generate("example.digest",false);}
  @Test public void ordinaryPackageHasNoPrivateSelfImport() throws Exception {generate("example.normal",true);}
  @Test public void ordinaryPackageOutputCompiles() throws Exception {generate("example.normal",false);}
}
