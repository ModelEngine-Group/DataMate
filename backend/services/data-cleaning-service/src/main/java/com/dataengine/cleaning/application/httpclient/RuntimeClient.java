package com.dataengine.cleaning.application.httpclient;

import lombok.extern.slf4j.Slf4j;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.text.MessageFormat;
import java.time.Duration;

@Slf4j
public class RuntimeClient {
    private static final String BASE_URL = "http://runtime:8081/api";

    private static final String CREATE_TASK_URL = BASE_URL + "/task/{0}/submit";

    private static final String STOP_TASK_URL = BASE_URL + "/task/{0}/stop";

    private static final HttpClient CLIENT = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();

    public static void submitTask(String taskId) {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(MessageFormat.format(CREATE_TASK_URL, taskId)))
                .timeout(Duration.ofSeconds(30))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.noBody())
                .build();

        try {
            HttpResponse<String> response = CLIENT.send(request, HttpResponse.BodyHandlers.ofString());
            int statusCode = response.statusCode();

            if (statusCode < 200 || statusCode >= 300) {
                log.error("Request failed with status code: {}", statusCode);
                throw new RuntimeException();
            }
        } catch (IOException | InterruptedException e) {
            log.error("Error occurred while making the request: {}", e.getMessage());
            throw new RuntimeException();
        }
    }

    public static void stopTask(String taskId) {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(MessageFormat.format(STOP_TASK_URL, taskId)))
                .timeout(Duration.ofSeconds(30))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.noBody())
                .build();

        try {
            HttpResponse<String> response = CLIENT.send(request, HttpResponse.BodyHandlers.ofString());
            int statusCode = response.statusCode();

            if (statusCode < 200 || statusCode >= 300) {
                log.error("Request failed with status code: {}", statusCode);
                throw new RuntimeException();
            }
        } catch (IOException | InterruptedException e) {
            log.error("Error occurred while making the request: {}", e.getMessage());
            throw new RuntimeException();
        }
    }
}
