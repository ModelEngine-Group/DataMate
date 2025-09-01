package com.dataengine.collection.infrastructure.runtime.datax;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.exec.*;
import org.springframework.stereotype.Component;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.time.Duration;

@Slf4j
@Component
@RequiredArgsConstructor
public class DataxProcessRunner {

    private final DataxProperties props;

    public int runJob(File jobFile, String executionId, Duration timeout) throws Exception {
        File logFile = new File(props.getLogPath(), String.format("datax-%s.log", executionId));
        String python = props.getPythonPath();
        String dataxPy = props.getHomePath() + File.separator + "bin" + File.separator + "datax.py";
        String cmd = String.format("%s %s %s", python, dataxPy, jobFile.getAbsolutePath());

        log.info("Execute DataX: {}", cmd);

        CommandLine cl = CommandLine.parse(cmd);
        DefaultExecutor executor = new DefaultExecutor();

        // 将日志追加输出到文件
        File parent = logFile.getParentFile();
        if (!parent.exists()) parent.mkdirs();

        ExecuteStreamHandler streamHandler = new PumpStreamHandler(
                new org.apache.commons.io.output.TeeOutputStream(
                        new java.io.FileOutputStream(logFile, true), System.out),
                new org.apache.commons.io.output.TeeOutputStream(
                        new java.io.FileOutputStream(logFile, true), System.err)
        );
        executor.setStreamHandler(streamHandler);

        ExecuteWatchdog watchdog = new ExecuteWatchdog(timeout.toMillis());
        executor.setWatchdog(watchdog);

        return executor.execute(cl);
    }
}
