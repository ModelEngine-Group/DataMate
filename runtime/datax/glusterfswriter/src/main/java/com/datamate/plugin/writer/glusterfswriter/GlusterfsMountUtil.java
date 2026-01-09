package com.datamate.plugin.writer.glusterfswriter;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.DirectoryNotEmptyException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

/**
 * GlusterFS 挂载工具类
 * 通过系统命令 mount -t glusterfs 进行挂载
 */
public final class GlusterfsMountUtil {
    private static final Logger LOG = LoggerFactory.getLogger(GlusterfsMountUtil.class);

    private GlusterfsMountUtil() {
    }

    /**
     * 挂载 GlusterFS 卷
     *
     * @param remote     远程地址，格式: ip:/volume
     * @param mountPoint 本地挂载点
     */
    public static void mount(String remote, String mountPoint) {
        try {
            Path mp = Paths.get(mountPoint);
            if (isMounted(mountPoint)) {
                throw new IOException("Already mounted: " + mountPoint);
            }

            Files.createDirectories(mp);

            ProcessBuilder pb = new ProcessBuilder();
            pb.command("mount", "-t", "glusterfs", remote, mountPoint);

            LOG.info("Mounting GlusterFS: {}", pb.command());
            pb.redirectErrorStream(true);
            Process p = pb.start();
            StringBuilder output = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    output.append(line).append(System.lineSeparator());
                }
            }
            int rc = p.waitFor();
            if (rc != 0) {
                throw new RuntimeException("GlusterFS mount failed, exit=" + rc + ", output: " + output);
            }
            LOG.info("GlusterFS mounted successfully: {} -> {}", remote, mountPoint);
        } catch (IOException | InterruptedException e) {
            throw new RuntimeException("Failed to mount GlusterFS: " + remote, e);
        }
    }

    /**
     * 卸载挂载点
     *
     * @param mountPoint 挂载点路径
     * @throws IOException          卸载失败
     * @throws InterruptedException 进程等待中断
     */
    public static void umount(String mountPoint) throws IOException, InterruptedException {
        if (!isMounted(mountPoint)) {
            return;
        }

        ProcessBuilder pb = new ProcessBuilder("umount", "-l", mountPoint);
        pb.redirectErrorStream(true);
        Process p = pb.start();
        StringBuilder output = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append(System.lineSeparator());
            }
        }
        int rc = p.waitFor();
        if (rc != 0) {
            throw new RuntimeException("GlusterFS umount failed, exit=" + rc + ", output: " + output);
        }

        // 清理空目录
        try {
            Files.deleteIfExists(Paths.get(mountPoint));
        } catch (DirectoryNotEmptyException ignore) {
            // 目录非空，保留
        }
        LOG.info("GlusterFS unmounted: {}", mountPoint);
    }

    /**
     * 判断挂载点是否已挂载
     *
     * @param mountPoint 挂载点路径
     * @return true 表示已挂载
     * @throws IOException 读取 /proc/mounts 失败
     */
    public static boolean isMounted(String mountPoint) throws IOException {
        Path procMounts = Paths.get("/proc/mounts");
        if (!Files.exists(procMounts)) {
            throw new IOException("/proc/mounts not found");
        }
        String expected = mountPoint.trim();
        List<String> lines = Files.readAllLines(procMounts);
        return lines.stream()
                .map(l -> l.split("\\s+"))
                .filter(a -> a.length >= 2)
                .anyMatch(a -> a[1].equals(expected));
    }
}
