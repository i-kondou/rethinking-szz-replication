package com.better.alarm.model;
import android.content.Context;
public final class AlarmReceiver {
    public static int scheduled=0,removed=0;
    public static void setUpRTCAlarm(Context c,Alarm a,long time) { scheduled++; }
    public static void removeRTCAlarm(Context c) { removed++; }
}
