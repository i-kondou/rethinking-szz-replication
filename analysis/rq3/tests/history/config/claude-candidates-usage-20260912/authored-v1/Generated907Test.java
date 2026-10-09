import org.junit.Test;
import static org.junit.Assert.*;
import java.util.logging.Level;
import com.google.common.flogger.*;
import com.google.common.flogger.backend.*;
import com.google.common.flogger.parser.*;

public class Generated907Test {
  interface Api extends LoggingApi<Api> {}
  static class NoOp extends LoggingApi.NoOp<Api> implements Api {}
  static final NoOp NO_OP = new NoOp();
  static class Capture extends LoggerBackend {
    LogData last;
    public String getLoggerName() { return "batch3.fixture"; }
    public boolean isLoggable(Level level) { return true; }
    public void log(LogData data) { last = data; }
    public void handleError(RuntimeException error, LogData data) { throw error; }
  }
  static class Logger extends AbstractLogger<Api> {
    final int depth;
    Logger(Capture backend, int depth) { super(backend); this.depth = depth; }
    public Api at(Level level) { return depth == 2 ? new Grandchild(level) : new Child(level); }
    class Context extends LogContext<Logger, Api> implements Api {
      Context(Level level) { super(level, false, 123456L); }
      protected Api api() { return this; }
      protected Logger getLogger() { return Logger.this; }
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
  private static void userCaller(Logger logger, StackSize size, Throwable cause) {
    Api api = logger.at(Level.INFO).withStackTrace(size);
    if (cause != null) api = api.withCause(cause);
    api.log("message");
  }
  private static Throwable loggedStack(int depth, StackSize size, Throwable cause) {
    Capture capture = new Capture(); userCaller(new Logger(capture, depth), size, cause);
    assertNotNull("logging control", capture.last);
    Throwable stack = capture.last.getMetadata().findValue(LogContext.Key.LOG_CAUSE);
    assertNotNull("stack trace control", stack); return stack;
  }
  private static void assertUserFrame(Throwable stack) {
    assertTrue("nonempty stack control", stack.getStackTrace().length > 0);
    StackTraceElement top = stack.getStackTrace()[0];
    assertEquals("TARGET_907_CALLER_CLASS", Generated907Test.class.getName(), top.getClassName());
    assertEquals("TARGET_907_CALLER_METHOD", "userCaller", top.getMethodName());
  }
  @Test public void singleOverrideReportsUserCaller() { assertUserFrame(loggedStack(1, StackSize.SMALL, null)); }
  @Test public void nestedOverridesReportUserCaller() { assertUserFrame(loggedStack(2, StackSize.MEDIUM, null)); }
  @Test public void existingCauseIsRetained() {
    Throwable cause = new IllegalArgumentException("fixture cause");
    assertSame(cause, loggedStack(2, StackSize.SMALL, cause).getCause());
  }
  @Test public void ordinaryLoggingHasNoSyntheticCause() {
    Capture capture = new Capture(); new Logger(capture, 2).at(Level.INFO).log("message");
    assertNotNull(capture.last); assertNull(capture.last.getMetadata().findValue(LogContext.Key.LOG_CAUSE));
  }
}
