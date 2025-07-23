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
                // fixedTime: "mm"
                cron = String.format("%s * * * *", fixedTime);
                break;
            case DAILY:
                // fixedTime: "HH:mm"
                String[] daily = fixedTime.split(":");
                if (daily.length == 2) {
                    cron = String.format("%s %s * * *", daily[1], daily[0]);
                }
                break;
            case MONTHLY:
                // fixedTime: "dd HH:mm"
                String[] monthly = fixedTime.split(" ");
                if (monthly.length != 2) {
                    break;
                }
                String[] hm = monthly[1].split(":");
                if (hm.length == 2) {
                    cron = String.format("%s %s %s * *", hm[1], hm[0], monthly[0]);
                }
                break;
            default:
                break;
        }
    }
}
