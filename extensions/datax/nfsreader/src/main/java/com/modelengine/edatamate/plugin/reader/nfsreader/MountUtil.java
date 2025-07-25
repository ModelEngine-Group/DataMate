package com.modelengine.edatamate.plugin.reader.nfsreader;

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
 * 一个简单的 Linux NAS 挂载工具类
 * 仅适用于 Linux，需具备 sudo 权限或 root。
 */
public final class MountUtil {
    private static final Logger LOG = LoggerFactory.getLogger(MountUtil.class);

    private MountUtil() {
    }

    /**
     * 挂载远程目录
     *
     * @param remote     远程地址，如 192.168.1.1:/test
     * @param mountPoint 本地挂载点，如 /mnt/nas
     * @param type       文件系统类型：nfs、cifs ...
     * @param options    额外挂载参数，如 ro,vers=3 或 username=xxx,password=xxx
     */
    public static void mount(String remote, String mountPoint, String type, String options) {
        try {
            Path mp = Paths.get(mountPoint);
            if (isMounted(mountPoint)) {
                throw new IOException("Already mounted: " + mountPoint);
            }

            Files.createDirectories(mp);

            ProcessBuilder pb = new ProcessBuilder();
            if (options == null || options.isEmpty()) {
                pb.command("mount", "-t", type, remote, mountPoint);
            } else {
                pb.command("mount", "-t", type, "-o", options, remote, mountPoint);
            }
            LOG.info(pb.command().toString());
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
                throw new RuntimeException("Mount failed, exit=" + rc + ", output: " + output);
            }
        } catch (IOException | InterruptedException e) {
            throw new RuntimeException(e);
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
            throw new RuntimeException("Mount failed, exit=" + rc + ", output: " + output);
        }

        // 清理空目录
        try {
            Files.deleteIfExists(Paths.get(mountPoint));
        } catch (DirectoryNotEmptyException ignore) {
            // 目录非空，保留
        }
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