package android.content;
import android.net.Uri;
public final class ContentUris {
    public static Uri withAppendedId(Uri uri,long id) { return Uri.parse(uri+"/"+id); }
    public static long parseId(Uri uri) { String s=uri.toString();return Long.parseLong(s.substring(s.lastIndexOf('/')+1)); }
}
