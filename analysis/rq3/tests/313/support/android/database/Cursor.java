package android.database;
import java.util.*;
public final class Cursor {
    private final List<Map<String,Object>> rows;
    private final String[] projection;
    private int index=-1;
    public Cursor(List<Map<String,Object>> rows,String[] projection) { this.rows=rows;this.projection=projection; }
    public boolean moveToFirst() { index=0;return !rows.isEmpty(); }
    public boolean moveToNext() { return ++index<rows.size(); }
    public int getCount() { return rows.size(); }
    private Object value(int col) { return rows.get(index).get(projection[col]); }
    public int getInt(int col) { Object v=value(col);return v instanceof Boolean ? ((Boolean)v?1:0) : v==null?0:((Number)v).intValue(); }
    public long getLong(int col) { Object v=value(col);return v==null?0:((Number)v).longValue(); }
    public String getString(int col) { Object v=value(col);return v==null?null:v.toString(); }
    public void close() {}
}
