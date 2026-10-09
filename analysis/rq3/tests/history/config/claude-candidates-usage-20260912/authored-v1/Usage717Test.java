import org.junit.Test;
import static org.junit.Assert.*;
import java.io.*;
import java.nio.file.*;
import java.lang.reflect.*;
import java.util.*;
import polyglot.main.Options;
public class Usage717Test {
  @SuppressWarnings("unchecked") static List<File> boot(Options options) throws Exception {
    try { return (List<File>) Options.class.getMethod("bootclasspathDirectories").invoke(options); }
    catch (NoSuchMethodException e) { return (List<File>) Options.class.getField("bootclasspath_directories").get(options); }
  }
  static void scenario(String mode) throws Exception {
    Path root = Files.createTempDirectory("polyglot-cli-");
    File base = Files.createDirectory(root.resolve("base")).toFile();
    File extra = Files.createDirectory(root.resolve("extra")).toFile();
    File source = root.resolve("Fixture.java").toFile();
    Files.write(source.toPath(), "class Fixture {}\n".getBytes("UTF-8"));
    String previous = System.getProperty("sun.boot.class.path");
    try {
      System.setProperty("sun.boot.class.path", base.getAbsolutePath());
      Options options = new Options(null, false);
      List<String> args = new ArrayList<String>();
      if (mode.equals("base-first")) Collections.addAll(args, "-bootclasspath", base.getAbsolutePath());
      if (!mode.equals("default-control") && !mode.equals("explicit-control")) Collections.addAll(args, "-addbootcp", extra.getAbsolutePath());
      if (mode.equals("extra-first") || mode.equals("explicit-control")) Collections.addAll(args, "-bootclasspath", base.getAbsolutePath());
      args.add(source.getAbsolutePath());
      Set<String> sources = new LinkedHashSet<String>();
      options.parseCommandLine(args.toArray(new String[0]), sources);
      assertTrue("source argument control", sources.contains(source.getAbsolutePath()));
      List<File> paths = boot(options);
      System.out.println("OBS_717 mode=" + mode + " paths=" + paths);
      assertTrue("base path control", paths.contains(base));
      if (mode.endsWith("control")) assertFalse(paths.contains(extra));
      else {
        assertTrue("extra path control", paths.contains(extra));
        assertTrue("TARGET_717_CLI_PRIORITY mode=" + mode + " paths=" + paths, paths.indexOf(extra) < paths.indexOf(base));
      }
    } finally {
      if (previous == null) System.clearProperty("sun.boot.class.path"); else System.setProperty("sun.boot.class.path", previous);
    }
  }
  @Test public void addbootcpWithDefaultBase() throws Exception { scenario("default-base"); }
  @Test public void explicitBaseThenAddition() throws Exception { scenario("base-first"); }
  @Test public void additionThenExplicitBase() throws Exception { scenario("extra-first"); }
  @Test public void defaultClasspathControl() throws Exception { scenario("default-control"); }
  @Test public void explicitClasspathControl() throws Exception { scenario("explicit-control"); }
}
