package com.datamate.operator.infrastructure.parser;

import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.datamate.operator.infrastructure.exception.OperatorErrorCode;
import com.datamate.operator.interfaces.dto.OperatorDto;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Enumeration;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

public class ZipParser extends AbstractParser {

    @Override
    public OperatorDto parseYamlFromArchive(File archive, String entryPath) {
        try (ZipFile zipFile = new ZipFile(archive)) {
            // 允许带或不带前导 "./"
            String normalized = entryPath.startsWith("./") ? entryPath.substring(2) : entryPath;
            ZipEntry entry = zipFile.getEntry(entryPath);
            if (entry == null) {
                entry = zipFile.getEntry(normalized);
            }
            if (entry == null) {
                throw BusinessException.of(OperatorErrorCode.YAML_NOT_FOUND, "Entry not found in zip: " + entryPath);
            }
            try (InputStream is = zipFile.getInputStream(entry)) {
                // 使用 SnakeYAML 解析为目标类型
                return parseYaml(is);
            }
        } catch (IOException e) {
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR, e.getMessage());
        }
    }

    @Override
    public void extractTo(File archive, String targetDir) {
        Path targetPath = Paths.get(targetDir);
        try (ZipFile zipFile = new ZipFile(archive)) {
            Files.createDirectories(targetPath);
            Enumeration<? extends ZipEntry> entries = zipFile.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                String entryName = entry.getName();

                // 防止 Zip Slip：确保解压路径仍在 targetDir 下
                Path resolved = targetPath.resolve(entryName).toAbsolutePath().normalize();
                if (!resolved.startsWith(targetPath.toAbsolutePath().normalize())) {
                    throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR, "Bad zip entry: " + entryName);
                }

                if (entry.isDirectory()) {
                    Files.createDirectories(resolved);
                } else {
                    Files.createDirectories(resolved.getParent());
                    try (InputStream is = zipFile.getInputStream(entry);
                         OutputStream os = Files.newOutputStream(resolved)) {
                        byte[] buffer = new byte[8192];
                        int len;
                        while ((len = is.read(buffer)) != -1) {
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
