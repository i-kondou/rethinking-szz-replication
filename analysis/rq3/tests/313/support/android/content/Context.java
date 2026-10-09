package android.content;
public final class Context {
    private final ContentResolver resolver;
    public int broadcasts=0;
    public Context(ContentResolver r) { resolver=r; }
    public ContentResolver getContentResolver() { return resolver; }
    public String getString(int id) { return "resource-"+id; }
    public CharSequence getText(int id) { return getString(id); }
    public void sendBroadcast(Intent intent) { broadcasts++; }
}
