package com.datamate.cleaning.interfaces.dto;


import lombok.Getter;
import lombok.Setter;

import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * CleaningProcess
 */

@Getter
@Setter
public class CleaningProcess {
    private Float process;

    private Integer totalFileNum;

    private Integer finishedFileNum;

    public CleaningProcess(int totalFileNum, int finishedFileNum) {
        this.totalFileNum = totalFileNum;
        this.finishedFileNum = finishedFileNum;
        if (totalFileNum == 0) {
            this.process = 0.0f;
        } else {
            this.process = BigDecimal.valueOf(finishedFileNum * 100L)
                .divide(BigDecimal.valueOf(totalFileNum), 2, RoundingMode.HALF_UP).floatValue();
        }
    }

    public static CleaningProcess of(int totalFileNum, int finishedFileNum) {
        return new CleaningProcess(totalFileNum, finishedFileNum);
    }
}

