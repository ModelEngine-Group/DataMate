package com.datamate.operator.infrastructure.parser;

import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.datamate.operator.infrastructure.exception.OperatorErrorCode;
import com.datamate.operator.interfaces.dto.OperatorDto;
import org.apache.commons.compress.archivers.tar.TarArchiveEntry;
import org.apache.commons.compress.archivers.tar.TarArchiveInputStream;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Objects;

public class TarParser extends AbstractParser {

    @Override
    public OperatorDto parseYamlFromArchive(File archive, String entryPath) {
        // 允许带或不带前导 "./"
        String normalized = entryPath.startsWith("./") ? entryPath.substring(2) : entryPath;
        try (InputStream fis = Files.newInputStream(archive.toPath());
             TarArchiveInputStream tis = new TarArchiveInputStream(fis)) {
            TarArchiveEntry entry;
            while ((entry = tis.getNextEntry()) != null) {
                String name = entry.getName();
                if (Objects.equals(name, entryPath) || Objects.equals(name, normalized)) {
                    // 使用 SnakeYAML 解析当前 entry 的内容到目标类型
                    return parseYaml(tis);
                }
            }
        } catch (IOException e) {
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR, e.getMessage());
        }
        throw BusinessException.of(OperatorErrorCode.YAML_NOT_FOUND, "Entry not found in tar: " + entryPath);
    }

    @Override
    public void extractTo(File archive, String targetDir) {
        Path targetPath = Paths.get(targetDir);
        try (InputStream fis = Files.newInputStream(archive.toPath());
             TarArchiveInputStream tis = new TarArchiveInputStream(fis)) {
            Files.createDirectories(targetPath);
            TarArchiveEntry entry;
            while ((entry = tis.getNextEntry()) != null) {
                String entryName = entry.getName();
                // 去掉可能的前导 "./"
                if (entryName.startsWith("./")) {
                    entryName = entryName.substring(2);
                }

                Path resolved = targetPath.resolve(entryName).toAbsolutePath().normalize();
                if (!resolved.startsWith(targetPath.toAbsolutePath().normalize())) {
                    throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR, "Bad tar entry: " + entryName);
                }

                if (entry.isDirectory()) {
                    Files.createDirectories(resolved);
                } else {
                    Files.createDirectories(resolved.getParent());
                    try (OutputStream os = Files.newOutputStream(resolved)) {
                        byte[] buffer = new byte[8192];
                        int len;
                        while ((len = tis.read(buffer)) != -1) {
                            os.write(buffer, 0, len);
                        }
                    }
                }
            }
        } catch (IOException e) {
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR, e.getMessage());
        }
    }
}
