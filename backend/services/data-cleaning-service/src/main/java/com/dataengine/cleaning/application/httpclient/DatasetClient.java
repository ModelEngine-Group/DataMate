package com.dataengine.cleaning.application.httpclient;

import com.dataengine.cleaning.domain.model.CreateDatasetRequest;
import com.dataengine.cleaning.domain.model.Dataset;
import com.dataengine.cleaning.domain.model.PagedDatasetFile;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.AbstractPageRequest;
import org.springframework.data.domain.Pageable;


import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.text.MessageFormat;
import java.time.Duration;

@Slf4j
public class DatasetClient {
    private static final String BASE_URL = "http://backend:8080/api";

    private static final String CREATE_DATASET_URL = BASE_URL + "/data-management/datasets";

    private static final String GET_DATASET_FILE_URL = BASE_URL + "/data-management/datasets/{0}/files";

    private static final HttpClient CLIENT = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    public static Dataset createDataset(String name, String type) {
        CreateDatasetRequest createDatasetRequest = new CreateDatasetRequest();
        createDatasetRequest.setName(name);
        createDatasetRequest.setType(type);


        String jsonPayload;
        try {
            jsonPayload = OBJECT_MAPPER.writeValueAsString(createDatasetRequest);
        } catch (IOException e) {
            throw new RuntimeException("Error serializing object to JSON: " + e.getMessage());
        }

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(CREATE_DATASET_URL))
                .timeout(Duration.ofSeconds(30))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

        try {
            HttpResponse<String> response = CLIENT.send(request, HttpResponse.BodyHandlers.ofString());
            int statusCode = response.statusCode();
            String responseBody = response.body();

            if (statusCode < 200 || statusCode >= 300) {
                log.error("Request failed with status code: {}", statusCode);
                throw new RuntimeException();
            }
            return OBJECT_MAPPER.readValue(responseBody, Dataset.class);
        } catch (IOException | InterruptedException e) {
            log.error("Error occurred while making the request: {}", e.getMessage());
            throw new RuntimeException();
        }
    }

    public static PagedDatasetFile getDatasetFile(String datasetId, Pageable page) {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(MessageFormat.format(GET_DATASET_FILE_URL, datasetId)))
                .timeout(Duration.ofSeconds(30))
                .header("Content-Type", "application/json")
                .GET()
                .build();

        try {
            HttpResponse<String> response = CLIENT.send(request, HttpResponse.BodyHandlers.ofString());
            int statusCode = response.statusCode();
            String responseBody = response.body();

            if (statusCode < 200 || statusCode >= 300) {
                log.error("Request failed with status code: {}", statusCode);
                throw new RuntimeException();
            }
            return OBJECT_MAPPER.readValue(responseBody, PagedDatasetFile.class);
        } catch (IOException | InterruptedException e) {
            log.error("Error occurred while making the request: {}", e.getMessage());
            throw new RuntimeException();
        }
    }
}
