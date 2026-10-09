import org.junit.runner.JUnitCore;
import org.junit.runner.Request;
import org.junit.runner.Result;
import org.junit.runner.notification.Failure;
public class OneMethod {
  public static void main(String[] args) throws Exception {
    Class<?> test = Class.forName("spoon.test.variable.AccessFullyQualifiedFieldTest");
    Result result = new JUnitCore().run(Request.method(test,
      "testPrivateStaticImportShouldNotBeImportedInSameClass"));
    for (Failure f : result.getFailures()) System.out.println(f.getTrace());
    System.out.println("RESULT runs=" + result.getRunCount() + " failures=" + result.getFailureCount() + " ignored=" + result.getIgnoreCount());
    System.exit(result.wasSuccessful() && result.getRunCount() == 1 && result.getIgnoreCount() == 0 ? 0 : 1);
  }
}
