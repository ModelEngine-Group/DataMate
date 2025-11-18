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

    private Float successRate;

    private Integer totalFileNum;

    private Integer succeedFileNum;

    private Integer failedFileNum;

    private Integer finishedFileNum;

    public CleaningProcess(int totalFileNum, int succeedFileNum, int failedFileNum) {
        this.totalFileNum = totalFileNum;
        this.succeedFileNum = succeedFileNum;
        this.failedFileNum = failedFileNum;
        this.finishedFileNum = succeedFileNum + failedFileNum;
        if (totalFileNum == 0) {
            this.process = 0.0f;
        } else {
            this.process = BigDecimal.valueOf(finishedFileNum * 100L)
                .divide(BigDecimal.valueOf(totalFileNum), 2, RoundingMode.HALF_UP).floatValue();
        }
        if (finishedFileNum == 0) {
            this.successRate = 0f;
        } else {
            this.successRate = BigDecimal.valueOf(succeedFileNum * 100L)
                    .divide(BigDecimal.valueOf(finishedFileNum), 2, RoundingMode.HALF_UP).floatValue();
        }
    }

    public static CleaningProcess of(int totalFileNum, int succeedFileNum, int failedFileNum) {
        return new CleaningProcess(totalFileNum, succeedFileNum, failedFileNum);
    }
}

