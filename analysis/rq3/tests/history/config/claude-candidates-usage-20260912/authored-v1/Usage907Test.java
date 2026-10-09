import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;
import java.util.logging.*;
import com.google.common.flogger.*;
import com.google.common.flogger.backend.*;
import com.google.common.flogger.backend.system.SimpleLoggerBackend;
import com.google.common.flogger.parser.*;
public class Usage907Test {
  interface Api extends LoggingApi<Api> {}
  static class NoOp extends LoggingApi.NoOp<Api> implements Api {}
  static final NoOp NO_OP = new NoOp();
  static class FixtureLogger extends AbstractLogger<Api> {
    final int depth;
    FixtureLogger(LoggerBackend backend, int depth) { super(backend); this.depth = depth; }
    public Api at(Level level) { return depth == 0 ? new Context(level) : depth == 1 ? new Child(level) : new Grandchild(level); }
    class Context extends LogContext<FixtureLogger, Api> implements Api {
      Context(Level level) { super(level, false); }
      protected Api api() { return this; }
      protected FixtureLogger getLogger() { return FixtureLogger.this; }
      protected Api noOp() { return NO_OP; }
      protected MessageParser getMessageParser() { return DefaultPrintfMessageParser.getInstance(); }
    }
    class Child extends Context {
      Child(Level level) { super(level); }
      @Override protected boolean postProcess(LogSiteKey key) { return super.postProcess(key); }
    }
    class Grandchild extends Child {
      Grandchild(Level level) { super(level); }
      @Override protected boolean postProcess(LogSiteKey key) { return super.postProcess(key); }
    }
  }
  static class CaptureHandler extends Handler {
    final List<LogRecord> records = new ArrayList<LogRecord>();
    public void publish(LogRecord record) { records.add(record); }
    public void flush() {}
    public void close() {}
  }
  static void userCaller(FixtureLogger logger, boolean stack, Throwable cause) {
    Api api = logger.at(Level.INFO);
    if (stack) api = api.withStackTrace(StackSize.MEDIUM);
    if (cause != null) api = api.withCause(cause);
    api.log("usage-message");
  }
  static LogRecord emitted(int depth, boolean stack, Throwable cause) {
    java.util.logging.Logger jul = java.util.logging.Logger.getLogger("usage907." + UUID.randomUUID());
    jul.setLevel(Level.ALL); jul.setUseParentHandlers(false);
    CaptureHandler handler = new CaptureHandler(); handler.setLevel(Level.ALL); jul.addHandler(handler);
    try {
      userCaller(new FixtureLogger(new SimpleLoggerBackend(jul), depth), stack, cause);
      assertEquals("one emitted JUL record control", 1, handler.records.size());
      LogRecord record = handler.records.get(0);
      assertEquals("message control", "usage-message", record.getMessage());
      System.out.println("OBS_907 depth=" + depth + " stack=" + stack + " top=" + (record.getThrown() == null ? "none" : record.getThrown().getStackTrace()[0]));
      return record;
    } finally { jul.removeHandler(handler); }
  }
  static void assertCaller(int depth) {
    Throwable stack = emitted(depth, true, null).getThrown(); assertNotNull("stack control", stack);
    assertTrue("nonempty stack control", stack.getStackTrace().length > 0);
    StackTraceElement top = stack.getStackTrace()[0];
    assertEquals("TARGET_907_JUL_CALLER", Usage907Test.class.getName(), top.getClassName());
    assertEquals("TARGET_907_JUL_CALLER", "userCaller", top.getMethodName());
  }
  @Test public void zeroOverrideStack() { assertCaller(0); }
  @Test public void singleOverrideStack() { assertCaller(1); }
  @Test public void nestedOverridesStack() { assertCaller(2); }
  @Test public void ordinaryLoggingControl() { assertNull(emitted(2, false, null).getThrown()); }
  @Test public void causeRetentionControl() {
    Throwable cause = new IllegalArgumentException("usage cause");
    assertSame(cause, emitted(2, true, cause).getThrown().getCause());
  }
}
