package com.datamate.cleaning.infrastructure.httpclient;

import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.text.MessageFormat;
import java.time.Duration;

@Slf4j
@Component
public class RuntimeClient {
    private final String CREATE_TASK_URL = "/api/task/{0}/submit";

    private final String STOP_TASK_URL = "/api/task/{0}/stop";

    @Value("${runtime.protocol:http}")
    private String protocol;

    @Value("${runtime.host:datamate-runtime}")
    private String host;

    @Value("${runtime.port:8081}")
    private int port;

    private final HttpClient CLIENT = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();

    public void submitTask(String taskId) {
        send(MessageFormat.format(getRequestUrl(CREATE_TASK_URL), taskId));
    }

    public void stopTask(String taskId) {
        send(MessageFormat.format(getRequestUrl(STOP_TASK_URL), taskId));
    }

    private String getRequestUrl(String url) {
        return protocol + "://" + host + ":" + port + url;
    }

    private void send(String url) {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(30))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.noBody())
                .build();

        try {
            HttpResponse<String> response = CLIENT.send(request, HttpResponse.BodyHandlers.ofString());
            int statusCode = response.statusCode();

            if (statusCode < 200 || statusCode >= 300) {
                log.error("Request failed with status code: {}", statusCode);
                throw BusinessException.of(SystemErrorCode.SYSTEM_BUSY);
            }
        } catch (IOException | InterruptedException e) {
            log.error("Error occurred while making the request.", e);
            throw BusinessException.of(SystemErrorCode.UNKNOWN_ERROR);
        }
    }
}
