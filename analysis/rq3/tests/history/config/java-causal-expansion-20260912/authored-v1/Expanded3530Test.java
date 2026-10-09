import org.junit.Test;
import static org.junit.Assert.*;
public class Expanded3530Test {
  static void check(int readSize) {
    Capsule3530 c=new Capsule3530();Capsule3530.AtracFileInfo info=new Capsule3530.AtracFileInfo();
    info.atracChannels=2;info.atracBytesPerFrame=560;info.inputFileDataOffset=128;info.inputFileSize=8192;
    assertEquals("codec boundary control",0,c.setHalfwayBuffer(0x1000,readSize,4096,false,info));
    assertEquals("file position control",readSize,c.inputBuffer.getFilePosition());
    assertEquals("header consumption control",0x1080,c.inputBuffer.getReadAddr());
    System.out.println("OBS_3530 read="+readSize+" remaining="+c.inputBuffer.getCurrentSize()+" max="+c.inputBuffer.getMaxSize()+" writable="+c.inputBuffer.getWriteSize());
    assertEquals("TARGET_3530_BUFFERED_BYTES read="+readSize,readSize-128,c.inputBuffer.getCurrentSize());
  }
  @Test public void fullBufferRetainsAllReadData(){check(4096);}
  @Test public void nearlyFullBufferRetainsAllReadData(){check(4080);}
  @Test public void partialBufferControl(){check(2048);}
  @Test public void alignedBufferControl(){check(4048);}
}
