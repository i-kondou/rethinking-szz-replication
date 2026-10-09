import org.junit.Test;
import static org.junit.Assert.*;
import java.io.File;
import java.util.*;
import polyglot.main.Options;
import polyglot.main.OptFlag;

public class Generated717Test {
  // Only the unrelated CLI flag population is disabled; original list logic is used.
  static class FixtureOptions extends Options {
    FixtureOptions() { super(null, false); }
    @Override protected void populateFlags(Set<OptFlag<?>> flags) {}
    void seed(File... paths) { setBootclasspath(Arrays.asList(paths)); }
    void prepend(File... paths) { addBootCP(Arrays.asList(paths)); }
  }
  private final File base = new File("base"), first = new File("first"), second = new File("second");
  @Test public void additionalBootPathHasSearchPriority() {
    FixtureOptions o = new FixtureOptions(); o.seed(base); o.prepend(first, second);
    assertEquals("TARGET_717_PRIORITY", Arrays.asList(first, second, base), o.bootclasspathDirectories());
  }
  @Test public void latestAdditionPrecedesEarlierAddition() {
    FixtureOptions o = new FixtureOptions(); o.seed(base); o.prepend(first); o.prepend(second);
    assertEquals("TARGET_717_PRIORITY", Arrays.asList(second, first, base), o.bootclasspathDirectories());
  }
  @Test public void emptyAdditionPreservesBase() {
    FixtureOptions o = new FixtureOptions(); o.seed(base); o.prepend();
    assertEquals(Arrays.asList(base), o.bootclasspathDirectories());
  }
  @Test public void emptyBasePreservesInputOrder() {
    FixtureOptions o = new FixtureOptions(); o.prepend(first, second);
    assertEquals(Arrays.asList(first, second), o.bootclasspathDirectories());
  }
}
