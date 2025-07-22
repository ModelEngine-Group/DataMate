package com.edatamate.common.schedule;

import com.cronutils.model.Cron;
import com.cronutils.model.CronType;
import com.cronutils.model.time.ExecutionTime;
import com.cronutils.parser.CronParser;
import com.cronutils.model.definition.CronDefinitionBuilder;

import java.time.Duration;
import java.time.ZonedDateTime;
import java.util.Optional;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

public class SimpleCronTask {

    private final Runnable taskLogic;          // Task logic
    private final ExecutionTime executionTime; // Cron execution time
    private final int maxTimes;                // Max allowed executions
    private final AtomicInteger executedTimes; // Executed count
    private final ScheduledExecutorService scheduler;

    private ScheduledFuture<?> future;         // Current schedule handle

    public SimpleCronTask(Runnable taskLogic,
                          String cron,
                          int maxTimes,
                          ScheduledExecutorService scheduler) {
        this.taskLogic = taskLogic;
        CronParser parser = new CronParser(CronDefinitionBuilder.instanceDefinitionFor(CronType.SPRING));
        Cron cronExpr = parser.parse(cron);
        this.executionTime = ExecutionTime.forCron(cronExpr);
        this.maxTimes = maxTimes;
        this.executedTimes = new AtomicInteger(0);
        this.scheduler = scheduler;
    }

    public synchronized void start() {
        if (future != null && !future.isDone()) {
            throw new IllegalStateException("Task already started");
        }
        scheduleNext();
    }

    public void runOnceNow() {
        if (executedTimes.get() >= maxTimes) {
            System.out.println("Max times reached, skip manual trigger.");
            return;
        }
        taskLogic.run();
        executedTimes.incrementAndGet();
    }

    public synchronized void cancel() {
        if (future != null) {
            future.cancel(false);
            future = null;
        }
    }

    private void scheduleNext() {
        if (executedTimes.get() >= maxTimes) {
            cancel();
            return;
        }
        ZonedDateTime now = ZonedDateTime.now();
        Optional<ZonedDateTime> next = executionTime.nextExecution(now);
        if (next.isEmpty()) {
            cancel();
            return;
        }
        long delayMillis = Duration.between(now, next.get()).toMillis();
        future = scheduler.schedule(() -> {
            if (executedTimes.incrementAndGet() <= maxTimes) {
                taskLogic.run();
            }
            scheduleNext();
        }, delayMillis, TimeUnit.MILLISECONDS);
    }

    /* ------------------- 测试示例 ------------------- */
    public static void main(String[] args) throws Exception {
        ScheduledExecutorService pool = java.util.concurrent.Executors.newScheduledThreadPool(2);

        // 任务逻辑：打印当前时间
        Runnable job = () -> System.out.println("task executed at " + java.time.LocalTime.now());

        // 每 10 秒执行一次，最多执行 5 次
        SimpleCronTask task = new SimpleCronTask(job, "*/10 * * * * *", 5, pool);

        task.start();        // 开始调度

        // 主线程等待演示
        Thread.sleep(30_000);
        task.cancel();
        pool.shutdown();
    }
}