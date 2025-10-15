package com.dataengine.cleaning.interfaces.dto;


import lombok.Getter;
import lombok.Setter;

/**
 * CleaningProcess
 */

@Getter
@Setter
public class CleaningProcess {
    private Float process;

    private Integer totalFileNum;

    private Integer finishedFileNum;
}

