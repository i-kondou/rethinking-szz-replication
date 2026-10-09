import org.junit.Test;
import static org.junit.Assert.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;
import java.util.jar.*;
import javax.tools.*;
import org.eclipse.scava.crossflow.runtime.Serializer;
public class Expanded2854Test {
  static URLClassLoader plugin() throws Exception {
    Path root=Files.createTempDirectory("crossflow-plugin-");
    String workflow="public class UploadedWorkflow extends Capsule2854.Workflow { public UploadedWorkflow(org.eclipse.scava.crossflow.runtime.Mode mode){super();} }";
    String payload="public class UploadedPayload { public String value; public UploadedPayload(){} }";
    Path w=root.resolve("UploadedWorkflow.java"),p=root.resolve("UploadedPayload.java");Files.write(w,workflow.getBytes("UTF-8"));Files.write(p,payload.getBytes("UTF-8"));
    assertEquals("plugin compilation control",0,ToolProvider.getSystemJavaCompiler().run(null,null,null,"-proc:none","-cp",System.getProperty("java.class.path"),"-d",root.toString(),w.toString(),p.toString()));
    Path jar=root.resolve("uploaded.jar");JarOutputStream out=new JarOutputStream(Files.newOutputStream(jar));
    for(String name:Arrays.asList("UploadedWorkflow","UploadedPayload")) {out.putNextEntry(new JarEntry(name+".class"));out.write(Files.readAllBytes(root.resolve(name+".class")));out.closeEntry();}out.close();
    return new URLClassLoader(new URL[]{jar.toUri().toURL()},Expanded2854Test.class.getClassLoader());
  }
  static void assertPayload(Serializer s,ClassLoader loader) throws Exception {
    Class<?> type=loader.loadClass("UploadedPayload");Object payload=type.newInstance();type.getField("value").set(payload,"kept");
    String xml=s.toString(payload);Object decoded=s.toObject(xml);
    assertSame("TARGET_2854_LOADER_IDENTITY",type,decoded.getClass());assertEquals("TARGET_2854_PAYLOAD","kept",type.getField("value").get(decoded));
  }
  @Test public void uploadedWorkflowCanStartAndDeserialize() throws Exception {
    URLClassLoader loader=plugin();
    try {
      try { Class.forName("UploadedPayload");fail("plugin must not be parent-visible"); } catch(ClassNotFoundException expected) {}
      Capsule2854.Workflow workflow;
      try { workflow=Capsule2854.start(loader,"UploadedWorkflow"); }
      catch(Exception e){System.out.println("OBS_2854 stage=constructor exception="+e.getClass().getName());throw e;}
      System.out.println("OBS_2854 stage=constructed");
      try { assertPayload(workflow.getSerializer(),loader); }
      catch(Exception e){System.out.println("OBS_2854 stage=deserialize exception="+e.getClass().getName());throw e;}
    } finally {loader.close();}
  }
  @Test public void explicitLoaderMechanismControl() throws Exception {
    URLClassLoader loader=plugin();try {Serializer s=new Serializer();s.setClassloader(loader);assertPayload(s,loader);}finally{loader.close();}
  }
  @Test public void parentVisibleXmlControl(){Serializer s=new Serializer();assertEquals("visible",s.toObject(s.toString("visible")));}
}
