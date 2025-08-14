package com.dataengine.collection.infrastructure.datax;

import com.dataengine.collection.domain.service.DataXDomainService;
import com.dataengine.collection.domain.service.DataXJobStatus;
import com.dataengine.collection.domain.model.DataSource;
import com.dataengine.collection.domain.model.CollectionTask;
import com.dataengine.collection.infrastructure.config.DataXProperties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;

/**
 * DataX作业管理器实现
 * 
 * 负责DataX作业的执行、监控和管理
 */
@Service
public class DataXJobManager implements DataXDomainService {

    private static final Logger logger = LoggerFactory.getLogger(DataXJobManager.class);

    private final DataXProperties dataXProperties;
    private final DataXConfigGenerator configGenerator;
    
    // 存储运行中的作业信息
    private final Map<String, DataXJobInfo> runningJobs = new ConcurrentHashMap<>();

    public DataXJobManager(DataXProperties dataXProperties, DataXConfigGenerator configGenerator) {
        this.dataXProperties = dataXProperties;
        this.configGenerator = configGenerator;
    }

    @Override
    public String generateDataXConfig(CollectionTask task, DataSource sourceDataSource, DataSource targetDataSource) {
        return configGenerator.generateConfig(task, sourceDataSource, targetDataSource);
    }

    @Override
    public boolean validateDataXConfig(String config) {
        try {
            // 简单的JSON格式验证
            com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
            mapper.readTree(config);
            
            // 检查必要字段
            return config.contains("\"job\"") && 
                   config.contains("\"content\"") && 
                   config.contains("\"reader\"") && 
                   config.contains("\"writer\"");
        } catch (Exception e) {
            logger.error("DataX config validation failed", e);
            return false;
        }
    }

    @Override
    @Async
    public String executeDataXJob(String config) {
        String jobId = generateJobId();
        
        try {
            // 创建临时配置文件
            Path configFile = createTempConfigFile(jobId, config);
            
            // 构建DataX命令
            String command = buildDataXCommand(configFile.toString());
            
            // 执行DataX作业
            DataXJobInfo jobInfo = new DataXJobInfo(jobId, command, configFile);
            runningJobs.put(jobId, jobInfo);
            
            CompletableFuture.runAsync(() -> executeJobAsync(jobInfo));
            
            logger.info("DataX job started with ID: {}", jobId);
            return jobId;
            
        } catch (Exception e) {
            logger.error("Failed to execute DataX job", e);
            throw new RuntimeException("Failed to execute DataX job", e);
        }
    }

    @Override
    public boolean stopDataXJob(String jobId) {
        DataXJobInfo jobInfo = runningJobs.get(jobId);
        if (jobInfo == null) {
            logger.warn("Job not found: {}", jobId);
            return false;
        }
        
        try {
            Process process = jobInfo.getProcess();
            if (process != null && process.isAlive()) {
                process.destroyForcibly();
                jobInfo.setStatus(DataXJobStatus.JobState.STOPPED);
                logger.info("DataX job stopped: {}", jobId);
                return true;
            }
            return false;
        } catch (Exception e) {
            logger.error("Failed to stop DataX job: {}", jobId, e);
            return false;
        }
    }

    @Override
    public DataXJobStatus getJobStatus(String jobId) {
        DataXJobInfo jobInfo = runningJobs.get(jobId);
        if (jobInfo == null) {
            // 作业不存在或已完成
            return new DataXJobStatus(jobId, DataXJobStatus.JobState.COMPLETED, 1.0, 0, 0, null, 0, System.currentTimeMillis());
        }
        
        return new DataXJobStatus(
            jobId,
            jobInfo.getStatus(),
            jobInfo.getProgress(),
            jobInfo.getRecordsProcessed(),
            jobInfo.getRecordsTotal(),
            jobInfo.getErrorMessage(),
            jobInfo.getStartTime(),
            jobInfo.getEndTime()
        );
    }

    @Override
    public String getJobLogs(String jobId, int lines) {
        DataXJobInfo jobInfo = runningJobs.get(jobId);
        if (jobInfo == null) {
            return "Job not found: " + jobId;
        }
        
        try {
            Path logFile = jobInfo.getLogFile();
            if (Files.exists(logFile)) {
                return readLastLines(logFile, lines);
            }
            return "Log file not found";
        } catch (Exception e) {
            logger.error("Failed to read job logs: {}", jobId, e);
            return "Failed to read logs: " + e.getMessage();
        }
    }

    /**
     * 异步执行DataX作业
     */
    private void executeJobAsync(DataXJobInfo jobInfo) {
        try {
            jobInfo.setStartTime(System.currentTimeMillis());
            jobInfo.setStatus(DataXJobStatus.JobState.RUNNING);
            
            ProcessBuilder processBuilder = new ProcessBuilder(jobInfo.getCommand().split("\\s+"));
            processBuilder.redirectErrorStream(true);
            
            // 设置日志文件
            Path logFile = createLogFile(jobInfo.getJobId());
            jobInfo.setLogFile(logFile);
            processBuilder.redirectOutput(logFile.toFile());
            
            Process process = processBuilder.start();
            jobInfo.setProcess(process);
            
            // 监控进程执行
            int exitCode = process.waitFor();
            
            jobInfo.setEndTime(System.currentTimeMillis());
            
            if (exitCode == 0) {
                jobInfo.setStatus(DataXJobStatus.JobState.COMPLETED);
                jobInfo.setProgress(1.0);
            } else {
                jobInfo.setStatus(DataXJobStatus.JobState.FAILED);
                jobInfo.setErrorMessage("DataX job failed with exit code: " + exitCode);
            }
            
            // 解析执行结果
            parseJobResult(jobInfo);
            
        } catch (Exception e) {
            logger.error("DataX job execution failed: {}", jobInfo.getJobId(), e);
            jobInfo.setStatus(DataXJobStatus.JobState.FAILED);
            jobInfo.setErrorMessage(e.getMessage());
            jobInfo.setEndTime(System.currentTimeMillis());
        } finally {
            // 清理临时文件
            cleanupTempFiles(jobInfo);
        }
    }

    /**
     * 创建临时配置文件
     */
    private Path createTempConfigFile(String jobId, String config) throws IOException {
        Path tempDir = Paths.get(dataXProperties.getTemp().getDir());
        Files.createDirectories(tempDir);
        
        Path configFile = tempDir.resolve(jobId + "_config.json");
        Files.write(configFile, config.getBytes());
        
        return configFile;
    }

    /**
     * 创建日志文件
     */
    private Path createLogFile(String jobId) throws IOException {
        Path tempDir = Paths.get(dataXProperties.getTemp().getDir());
        Files.createDirectories(tempDir);
        
        return tempDir.resolve(jobId + "_log.txt");
    }

    /**
     * 构建DataX执行命令
     */
    private String buildDataXCommand(String configFile) {
        StringBuilder command = new StringBuilder();
        
        command.append(dataXProperties.getPython())
               .append(" ")
               .append(dataXProperties.getHome())
               .append("/bin/datax.py")
               .append(" ")
               .append(configFile);
        
        // 添加JVM参数
        command.append(" --jvm=\"-Xms")
               .append(dataXProperties.getJob().getMemory())
               .append("m -Xmx")
               .append(dataXProperties.getJob().getMemory())
               .append("m\"");
        
        return command.toString();
    }

    /**
     * 解析作业执行结果
     */
    private void parseJobResult(DataXJobInfo jobInfo) {
        try {
            Path logFile = jobInfo.getLogFile();
            if (Files.exists(logFile)) {
                String content = Files.readString(logFile);
                
                // 解析记录数
                if (content.contains("totalReadRecords")) {
                    // 解析DataX输出的统计信息
                    // 这里需要根据实际DataX输出格式进行解析
                    parseStatistics(content, jobInfo);
                }
            }
        } catch (Exception e) {
            logger.warn("Failed to parse job result: {}", jobInfo.getJobId(), e);
        }
    }

    /**
     * 解析统计信息
     */
    private void parseStatistics(String content, DataXJobInfo jobInfo) {
        // 这里实现DataX输出日志的解析逻辑
        // 提取记录数、字节数等统计信息
        try {
            // 示例解析逻辑（需要根据实际DataX输出调整）
            if (content.contains("读出记录总数")) {
                // 解析中文输出
                String[] lines = content.split("\n");
                for (String line : lines) {
                    if (line.contains("读出记录总数")) {
                        String records = line.replaceAll("[^0-9]", "");
                        if (!records.isEmpty()) {
                            jobInfo.setRecordsTotal(Long.parseLong(records));
                            jobInfo.setRecordsProcessed(Long.parseLong(records));
                        }
                    }
                }
            }
        } catch (Exception e) {
            logger.warn("Failed to parse statistics", e);
        }
    }

    /**
     * 读取文件最后几行
     */
    private String readLastLines(Path file, int lines) throws IOException {
        StringBuilder result = new StringBuilder();
        try (BufferedReader reader = Files.newBufferedReader(file)) {
            String line;
            java.util.List<String> lastLines = new java.util.ArrayList<>();
            
            while ((line = reader.readLine()) != null) {
                lastLines.add(line);
                if (lastLines.size() > lines) {
                    lastLines.remove(0);
                }
            }
            
            for (String lastLine : lastLines) {
                result.append(lastLine).append("\n");
            }
        }
        return result.toString();
    }

    /**
     * 清理临时文件
     */
    private void cleanupTempFiles(DataXJobInfo jobInfo) {
        if (dataXProperties.getTemp().isAutoClean()) {
            try {
                if (jobInfo.getConfigFile() != null && Files.exists(jobInfo.getConfigFile())) {
                    Files.delete(jobInfo.getConfigFile());
                }
            } catch (Exception e) {
                logger.warn("Failed to cleanup temp files for job: {}", jobInfo.getJobId(), e);
            }
        }
    }

    /**
     * 生成作业ID
     */
    private String generateJobId() {
        return "datax_" + UUID.randomUUID().toString().replace("-", "");
    }

    /**
     * DataX作业信息
     */
    private static class DataXJobInfo {
        private final String jobId;
        private final String command;
        private final Path configFile;
        private Path logFile;
        private Process process;
        private DataXJobStatus.JobState status = DataXJobStatus.JobState.RUNNING;
        private double progress = 0.0;
        private long recordsProcessed = 0;
        private long recordsTotal = 0;
        private String errorMessage;
        private long startTime;
        private long endTime;

        public DataXJobInfo(String jobId, String command, Path configFile) {
            this.jobId = jobId;
            this.command = command;
            this.configFile = configFile;
        }

        // Getters and Setters
        public String getJobId() { return jobId; }
        public String getCommand() { return command; }
        public Path getConfigFile() { return configFile; }
        public Path getLogFile() { return logFile; }
        public void setLogFile(Path logFile) { this.logFile = logFile; }
        public Process getProcess() { return process; }
        public void setProcess(Process process) { this.process = process; }
        public DataXJobStatus.JobState getStatus() { return status; }
        public void setStatus(DataXJobStatus.JobState status) { this.status = status; }
        public double getProgress() { return progress; }
        public void setProgress(double progress) { this.progress = progress; }
        public long getRecordsProcessed() { return recordsProcessed; }
        public void setRecordsProcessed(long recordsProcessed) { this.recordsProcessed = recordsProcessed; }
        public long getRecordsTotal() { return recordsTotal; }
        public void setRecordsTotal(long recordsTotal) { this.recordsTotal = recordsTotal; }
        public String getErrorMessage() { return errorMessage; }
        public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }
        public long getStartTime() { return startTime; }
        public void setStartTime(long startTime) { this.startTime = startTime; }
        public long getEndTime() { return endTime; }
        public void setEndTime(long endTime) { this.endTime = endTime; }
    }
}
