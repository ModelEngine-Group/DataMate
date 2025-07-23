package com.edatamate.domain.dataset.parser.datasetconfig;

import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
public class SyncConfig extends CommonConfig {
    private String syncType;

    private String cron;

    private int maxExecuteTimes;

    private boolean executeCurrent;

    // For fixed interval scheduling
    private ScheduleType scheduleType; // CRON or FIXED

    private FixedType fixedType;       // HOURLY, DAILY, MONTHLY

    private String fixedTime;          // e.g., "14:00", "02", "15 10:00"

    private enum ScheduleType {
        CRON, FIXED
    }

    private enum FixedType {
        HOURLY, DAILY, MONTHLY
    }

    public void toCronFromFixed() {
        if (scheduleType != ScheduleType.FIXED || fixedType == null || fixedTime == null) {
            return;
        }
        switch (fixedType) {
            case HOURLY:
                // fixedTime: "ss:mm"
                String[] hourly = fixedTime.split(":");
                if (hourly.length == 2) {
                    cron = String.format("%s %s * * * *", hourly[0], hourly[1]);
                }
                break;
            case DAILY:
                // fixedTime: "ss:mm:HH"
                String[] daily = fixedTime.split(":");
                if (daily.length == 3) {
                    cron = String.format("%s %s %s * * *", daily[0], daily[1], daily[2]);
                }
                break;
            case MONTHLY:
                // fixedTime: "ss:mm:HH:dd"
                String[] monthly = fixedTime.split(":");
                if (monthly.length == 4) {
                    cron = String.format("%s %s %s %s * *", monthly[0], monthly[1], monthly[2], monthly[3]);
                }
                break;
            default:
                break;
        }
    }
}
