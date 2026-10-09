

package spoon.test.variable.testclasses.digest;


public class DigestUtil {
    private static final int STREAM_BUFFER_LENGTH = 1024;

    public static MessageDigest getDigest(final java.lang.String algorithm) {
        return new MessageDigest();
    }

    public static MessageDigest getMd2Digest() {
        return DigestUtil.getDigest(MessageDigest.MD2);
    }

    public static MessageDigest getMd5Digest() {
        return DigestUtil.getDigest(MessageDigest.MD5);
    }

    public static byte[] digest(final java.security.MessageDigest messageDigest, final byte[] data) {
        return messageDigest.digest(data);
    }

    public static byte[] digest(final java.security.MessageDigest messageDigest, final java.nio.ByteBuffer data) {
        messageDigest.update(data);
        return messageDigest.digest();
    }

    public static MessageDigest updateDigest(final MessageDigest digest, final java.io.InputStream data) throws java.io.IOException {
        final byte[] buffer = new byte[DigestUtil.STREAM_BUFFER_LENGTH];
        int read = data.read(buffer, 0, DigestUtil.STREAM_BUFFER_LENGTH);
        while (read > (-1)) {
            read = data.read(buffer, 0, DigestUtil.STREAM_BUFFER_LENGTH);
        } 
        return digest;
    }
}

