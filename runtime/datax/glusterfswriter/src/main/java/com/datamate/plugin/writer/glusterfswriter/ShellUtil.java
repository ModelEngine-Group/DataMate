package com.datamate.plugin.writer.glusterfswriter;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

/**
 * Shell 命令执行工具类
 */
public class ShellUtil {
    /**
     * 执行 shell 命令
     *
     * @param cmd       命令
     * @param extraArgs 额外参数，可为空
     * @return 命令完整输出（stdout + stderr）
     * @throws Exception 如果命令返回非 0 或发生 IO 异常
     */
    public static String runCommand(String cmd, List<String> extraArgs) throws Exception {
        List<String> commands = new ArrayList<>();
        commands.add(cmd);
        if (extraArgs != null && !extraArgs.isEmpty()) {
            commands.addAll(extraArgs);
        }

        ProcessBuilder pb = new ProcessBuilder(commands);
        pb.redirectErrorStream(true);          // 合并 stdout & stderr
        Process p = pb.start();

        StringBuilder sb = new StringBuilder();
        try (BufferedReader br = new BufferedReader(
                new InputStreamReader(p.getInputStream()))) {
            String line;
            while ((line = br.readLine()) != null) {
                sb.append(line).append(System.lineSeparator());
            }
        }

        int exit = p.waitFor();
        if (exit != 0) {
            throw new RuntimeException("Command exited with code " + exit + System.lineSeparator() + sb);
        }
        return sb.toString();
    }
}
