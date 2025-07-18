package com.edatamate.interfaces;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.ComponentScan;

/**
 * 数据工程启动类
 *
 * @author: dallas
 * @since: 2025-07-14
 */
@SpringBootApplication
@ComponentScan(basePackages = "com.edatamate")
@MapperScan(basePackages = "com.edatamate.infrastructure.mapper")
@EnableFeignClients(basePackages = "com.edatamate")
public class EdatamateApplication {
    public static void main(String[] args) {
        SpringApplication.run(EdatamateApplication.class, args);
    }
}
