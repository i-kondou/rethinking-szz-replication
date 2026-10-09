package com.better.alarm.model;
import android.content.*;
import java.lang.reflect.*;
import java.time.Instant;
import java.util.*;

/** Synthetic fixture; original domain classes and their collection are not modified. */
public final class Replay {
    private static void result(String key,Object value) { System.out.println("RESULT "+key+"="+value); }
    public static void main(String[] args) throws Exception {
        String scenario=args[0];
        int count=scenario.contains("one")?1:2;
        boolean enabled=scenario.endsWith("_enabled");
        long stored=scenario.startsWith("zero")?0:Instant.parse(scenario.startsWith("future")?"2100-01-01T08:00:00Z":"2012-07-01T08:00:00Z").toEpochMilli();
        ContentResolver db=new ContentResolver();
        for(int id=1;id<=count;id++) {
            Map<String,Object> row=new LinkedHashMap<>();
            row.put(Alarm.Columns._ID,id);row.put(Alarm.Columns.HOUR,8);row.put(Alarm.Columns.MINUTES,0);
            row.put(Alarm.Columns.ALARM_TIME,stored);row.put(Alarm.Columns.ENABLED,enabled?1:0);
            row.put(Alarm.Columns.DAYS_OF_WEEK,0);row.put(Alarm.Columns.VIBRATE,0);row.put(Alarm.Columns.MESSAGE,"fixture-"+id);
            row.put(Alarm.Columns.ALERT,"silent");
            db.rows.add(row);
        }
        Context context=new Context(db);
        result("scenario",scenario);result("now_ms",System.currentTimeMillis());
        result("stored_ms",stored);result("input_count",count);result("enabled",enabled);result("input_rows",db.rows);
        String outcome="normal";String phase="construct";
        try {
            Class<?> cls;
            try { cls=Class.forName("com.better.alarm.model.Alarms"); }
            catch(ClassNotFoundException e) { cls=Class.forName("com.better.alarm.model.AlarmsManager"); }
            Constructor<?> ctor=cls.getDeclaredConstructors()[0];ctor.setAccessible(true);
            Object[] params=new Object[ctor.getParameterCount()];params[0]=context;
            if(params.length==2) {
                Class<?> scheduler=ctor.getParameterTypes()[1];
                params[1]=Proxy.newProxyInstance(scheduler.getClassLoader(),new Class[]{scheduler},(proxy,method,values)->null);
            }
            Object model=ctor.newInstance(params);
            // Observe the actual collection and getters before invoking the original init loop.
            Field sf=cls.getDeclaredField("set");sf.setAccessible(true);Set<?> set=(Set<?>)sf.get(model);
            result("set_class",set.getClass().getName());result("loaded_count",set.size());
            for(Object a:set) {
                Alarm alarm=(Alarm)a;result("computed_next_"+alarm.getId(),alarm.getTimeInMillis());
            }
            Method entry;
            try { entry=cls.getDeclaredMethod("init"); }
            catch(NoSuchMethodException e) { entry=cls.getDeclaredMethod("disableExpiredAlarms"); }
            entry.setAccessible(true);result("entry",cls.getName()+"."+entry.getName());phase="init";
            entry.invoke(model);
            result("remaining_count",set.size());
        } catch(Throwable t) {
            while(t instanceof InvocationTargetException && t.getCause()!=null)t=t.getCause();
            outcome=t.getClass().getName();t.printStackTrace(System.err);
        }
        result("phase",phase);result("outcome",outcome);result("db_updates",db.updates);result("output_rows",db.rows);
        result("broadcasts",context.broadcasts);
        if(!outcome.equals("normal") && !outcome.equals("java.util.ConcurrentModificationException"))System.exit(2);
    }
}
