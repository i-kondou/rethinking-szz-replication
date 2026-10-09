import org.junit.Test;
import static org.junit.Assert.*;
import com.cloud.hypervisor.kvm.storage.KVMPhysicalDisk;

/** BFC-guided specification: RBD host/port separator has a single escape.
 * New boundary/authentication combinations; existing BFC assertion was not copied.
 * Does not execute QEMU or validate Ceph connectivity.
 */
public class Generated399Test {
  @Test public void positivePortHasOneEscape() {
    for (int port : new int[]{1, 6789, 65535}) {
      String actual=KVMPhysicalDisk.RBDStringBuilder("monitor.example",port,null,null,"pool/image");
      assertEquals("TARGET_399_ESCAPE port="+port,
        "rbd:pool/image:mon_host=monitor.example\\:"+port+
        ":auth_supported=none:rbd_default_format=2:client_mount_timeout=30",actual);
    }
  }
  @Test public void nonpositivePortIsOmitted() {
    for (int port : new int[]{-1,0}) {
      assertEquals("rbd:pool/image:mon_host=monitor.example:auth_supported=none:rbd_default_format=2:client_mount_timeout=30",
        KVMPhysicalDisk.RBDStringBuilder("monitor.example",port,null,null,"pool/image"));
    }
  }
  @Test public void authenticatedBoundaryPortHasOneEscape() {
    assertEquals("TARGET_399_ESCAPE authenticated",
      "rbd:pool/image:mon_host=monitor.example\\:1:auth_supported=cephx:id=client:key=test-key:rbd_default_format=2:client_mount_timeout=30",
      KVMPhysicalDisk.RBDStringBuilder("monitor.example",1,"client","test-key","pool/image"));
  }
}
