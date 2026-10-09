package android.preference;
import android.content.Context;
public final class PreferenceManager {
    public static Preferences getDefaultSharedPreferences(Context c) { return new Preferences(); }
    public static final class Preferences { public String getString(String key,String fallback) { throw new UnsupportedOperationException("preference path was not expected"); } }
}
