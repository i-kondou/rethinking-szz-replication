import jpcsp.HLE.kernel.types.pspFileBuffer;
public class Capsule3530 {
  public static class AtracFileInfo { public int atracChannels,atracBytesPerFrame,inputFileDataOffset,inputFileSize,atracCodingMode; }
  AtracFileInfo info; int channels,currentReadPosition,atracCurrentSample,currentLoopNum,lastDecodedSamples,outputChannels;
  pspFileBuffer inputBuffer;
  static class CodecBoundary { int init(int frame,int channels,int output,int mode){return 0;} }
  CodecBoundary codec=new CodecBoundary();
  void setOutputChannels(int n){outputChannels=n;}
  void setCodecInitialized(){}
public int setHalfwayBuffer(int addr, int readSize, int bufferSize, boolean isMonoOutput, AtracFileInfo info) {
        	this.info = info;
        	channels = info.atracChannels;
    		inputBuffer = new pspFileBuffer(addr, bufferSize, readSize, readSize);
        	inputBuffer.notifyRead(info.inputFileDataOffset);
    		inputBuffer.setFileMaxSize(info.inputFileSize);
        	currentReadPosition = info.inputFileDataOffset;
        	atracCurrentSample = 0;
        	currentLoopNum = -1;
        	lastDecodedSamples = 0;

    		setOutputChannels(isMonoOutput ? 1 : 2);

        	int result = codec.init(info.atracBytesPerFrame, channels, outputChannels, info.atracCodingMode);
        	if (result < 0) {
        		return result;
        	}

        	setCodecInitialized();

        	return 0;
        }
}
