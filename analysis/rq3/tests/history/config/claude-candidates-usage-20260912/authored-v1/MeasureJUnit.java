import org.junit.runner.JUnitCore;
import org.junit.runner.Result;
import org.junit.runner.notification.Failure;
public class MeasureJUnit {
  public static void main(String[] args) throws Exception {
    Result r=JUnitCore.runClasses(Class.forName(args[0]));
    for (Failure f:r.getFailures()) {
      System.out.println("FAILURE_TEST="+f.getTestHeader()); System.out.println(f.getTrace());
    }
    System.out.println("MEASURE tests="+r.getRunCount()+" failures="+r.getFailureCount()+" ignored="+r.getIgnoreCount()+" assumptions="+r.getAssumptionFailureCount());
    System.exit(r.wasSuccessful() && r.getRunCount()>0 && r.getIgnoreCount()==0 && r.getAssumptionFailureCount()==0 ? 0 : 1);
  }
}
