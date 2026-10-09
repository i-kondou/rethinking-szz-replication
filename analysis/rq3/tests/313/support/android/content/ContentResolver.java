package android.content;
import android.net.Uri;
import android.database.Cursor;
import java.util.*;
public final class ContentResolver {
    public final List<Map<String,Object>> rows=new ArrayList<>();
    public int updates=0;
    public Cursor query(Uri uri,String[] cols,String selection,String[] args,String order) {
        if(selection!=null) throw new UnsupportedOperationException("Unmodelled query: "+selection);
        return new Cursor(rows,cols);
    }
    public int update(Uri uri,ContentValues values,String where,String[] args) {
        if(where!=null) throw new UnsupportedOperationException("Unmodelled update");
        long id=ContentUris.parseId(uri);
        for(Map<String,Object> row:rows) if(((Number)row.get("_id")).longValue()==id) {
            row.putAll(values);updates++;return 1;
        }
        throw new IllegalArgumentException("Unknown alarm id "+id);
    }
    public Uri insert(Uri uri,ContentValues values) { throw new UnsupportedOperationException("insert"); }
    public int delete(Uri uri,String where,String[] args) { throw new UnsupportedOperationException("delete"); }
}
