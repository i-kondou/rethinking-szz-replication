import org.junit.Test;
import static org.junit.Assert.*;
import java.lang.reflect.*;
public class Usage399Test {
  static String build(int port, boolean auth) throws Exception {
    Class<?> type;
    try { type = Class.forName("com.cloud.hypervisor.kvm.storage.KVMPhysicalDisk"); }
    catch (ClassNotFoundException e) { type = Class.forName("com.cloud.agent.storage.KVMPhysicalDisk"); }
    Method method = type.getMethod("RBDStringBuilder", String.class, int.class, String.class, String.class, String.class);
    return (String) method.invoke(null, "monitor.example", port, auth ? "client" : null, auth ? "test-key" : null, "pool/image");
  }
  static void checkPort(int port, boolean auth) throws Exception {
    String value = build(port, auth);
    int start = value.indexOf(":mon_host=") + ":mon_host=".length();
    int end = value.indexOf(":auth_supported=");
    assertTrue("argument syntax control", start >= ":mon_host=".length() && end > start);
    String host = value.substring(start, end);
    String explicit = "monitor.example\\:" + port;
    System.out.println("OBS_399 port=" + port + " auth=" + auth + " host=" + host);
    assertTrue("TARGET_399_PORT port=" + port + " actual=" + host,
        host.equals(explicit) || (port == 6789 && host.equals("monitor.example")));
  }
  @Test public void defaultPortWithoutAuth() throws Exception { checkPort(6789, false); }
  @Test public void defaultPortWithAuth() throws Exception { checkPort(6789, true); }
  @Test public void nondefaultPortWithoutAuth() throws Exception { checkPort(8000, false); }
  @Test public void nondefaultPortWithAuth() throws Exception { checkPort(8000, true); }
  @Test public void unauthenticatedControl() throws Exception {
    String value = build(6789, false); assertTrue(value.startsWith("rbd:pool/image:mon_host="));
    assertTrue(value.contains(":auth_supported=none")); assertFalse(value.contains(":key="));
  }
  @Test public void authenticatedControl() throws Exception {
    assertTrue(build(6789, true).contains(":auth_supported=cephx:id=client:key=test-key"));
  }
}
