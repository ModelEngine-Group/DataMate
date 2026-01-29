package com.datamate.plugin.reader.apireader;

import com.alibaba.datax.common.element.*;
import com.alibaba.datax.common.plugin.RecordSender;
import com.alibaba.datax.common.spi.Reader;
import com.alibaba.datax.common.util.Configuration;
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import com.alibaba.fastjson.JSONPath;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.charset.StandardCharsets;

import org.apache.hc.client5.http.classic.methods.HttpDelete;
import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.classic.methods.HttpPost;
import org.apache.hc.client5.http.classic.methods.HttpPut;
import org.apache.hc.client5.http.classic.methods.HttpUriRequestBase;
import org.apache.hc.client5.http.config.RequestConfig;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.http.ContentType;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.apache.hc.core5.http.io.entity.StringEntity;
import java.util.Collections;
import java.util.List;

/**
 * API读取器
 * 支持符合restful api的接口
 */
public class APIReader extends Reader {

    private static final Logger LOG = LoggerFactory.getLogger(APIReader.class);

    public static class Job extends Reader.Job {
        private Configuration jobConfig = null;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
        }

        @Override
        public void prepare() {
            String api = this.jobConfig.getString("api");
            Object schema = this.jobConfig.get("schema");

            if (StringUtils.isBlank(api)) {
                throw new RuntimeException("api is required for APIReader");
            }
            if (schema == null) {
                throw new RuntimeException("schema configuration is required for APIReader");
            }
        }

        @Override
        public List<Configuration> split(int adviceNumber) {
            // API通常不支持并行分片读取，除非有分页参数逻辑，此处暂按单通道处理
            return Collections.singletonList(this.jobConfig);
        }

        @Override
        public void destroy() {
        }
    }

    public static class Task extends Reader.Task {

        private Configuration jobConfig;
        private String api;
        private String method;
        private String dataPath; // 用于指定返回json中哪个节点是数据列表，例如 "data.list"
        private List<Configuration> schemaFields;
        private String requestBody;
        private Configuration requestHeaders;

        @Override
        public void init() {
            this.jobConfig = super.getPluginJobConf();
            this.api = this.jobConfig.getString("api");
            this.method = this.jobConfig.getString("method", "GET");
            this.requestBody = this.jobConfig.getString("body", "");
            this.requestHeaders = this.jobConfig.getConfiguration("headers");
            parseSchema();
        }

        private void parseSchema() {
            Configuration schemaConfig = this.jobConfig.getConfiguration("schema");
            if (schemaConfig != null && !schemaConfig.getKeys().isEmpty()) {
                this.dataPath = schemaConfig.getString("dataPath", "");
                this.schemaFields = schemaConfig.getListConfiguration("fields");
                return;
            }

            if (this.schemaFields == null || this.schemaFields.isEmpty()) {
                throw new RuntimeException("schema.fields is required and cannot be empty");
            }

            for (Configuration fieldConfig : this.schemaFields) {
                String name = fieldConfig.getString("name"); // JSON中的字段名
                String path = fieldConfig.getString("path"); // 可选：支持深层提取
                if (StringUtils.isBlank(name) && StringUtils.isBlank(path)) {
                    throw new RuntimeException("schema.fields must contain name or path");
                }
            }
        }

        @Override
        public void startRead(RecordSender recordSender) {
            LOG.info("Start reading from API: [{}]", this.api);

            try {
                // 1. 发起HTTP请求
                String responseBody = doHttpRequest(this.api, this.method, this.requestBody, this.requestHeaders);

                // 2. 解析响应
                JSONArray dataArray = parseResponse(responseBody);

                if (dataArray.isEmpty()) {
                    LOG.warn("API returned empty data.");
                    return;
                }

                // 3. 添加文件表头
                addDataHeader(recordSender);

                // 4. 遍历数据并转换为DataX Record
                addData(recordSender, dataArray);

            } catch (Exception e) {
                LOG.error("Error occurred while reading from API", e);
                throw new RuntimeException(e);
            }
        }

        private void addData(RecordSender recordSender, JSONArray dataArray) {
            for (Object itemObj : dataArray) {
                JSONObject item = (JSONObject) itemObj;
                Record record = recordSender.createRecord();

                for (Configuration fieldConfig : this.schemaFields) {
                    String name = fieldConfig.getString("name"); // JSON中的字段名
                    String path = fieldConfig.getString("path"); // 可选：支持深层提取
                    if (StringUtils.isBlank(name) && StringUtils.isBlank(path)) {
                        throw new RuntimeException("schema.fields must contain name or path");
                    }

                    Object val;
                    if (StringUtils.isNotBlank(path)) {
                        val = JSONPath.eval(item, path);
                    } else {
                        val = item.get(name);
                    }

                    if (val == null) {
                        record.addColumn(new StringColumn(""));
                        continue;
                    }

                    record.addColumn(new StringColumn(val.toString()));
                }
                recordSender.sendToWriter(record);
            }
        }

        private void addDataHeader(RecordSender recordSender) {
            Record recordHeader = recordSender.createRecord();
            for (Configuration fieldConfig : this.schemaFields) {
                String name = fieldConfig.getString("name"); // JSON中的字段名
                String alias = fieldConfig.getString("alias"); // 自定义的字段别名
                if (StringUtils.isNotBlank(alias)) {
                    recordHeader.addColumn(new StringColumn(alias));
                } else {
                    recordHeader.addColumn(new StringColumn(name));
                }
            }
            recordSender.sendToWriter(recordHeader);
        }

        private JSONArray parseResponse(String responseBody) {
            Object responseJson = JSON.parse(responseBody);
            JSONArray dataArray;

            // 定位数据节点
            if (StringUtils.isNotBlank(this.dataPath)) {
                // 使用 JSONPath 提取
                Object extracted = JSONPath.eval(responseJson, this.dataPath);
                if (extracted instanceof JSONArray) {
                    dataArray = (JSONArray) extracted;
                } else {
                    throw new RuntimeException("The dataPath configured [" + this.dataPath + "] does not point to a JSON Array.");
                }
            } else {
                if (responseJson instanceof JSONArray) {
                    dataArray = (JSONArray) responseJson;
                } else if (responseJson instanceof JSONObject) {
                    throw new RuntimeException("Response is an Object, please configure schema.dataPath to point to the list.");
                } else {
                    throw new RuntimeException("Unknown response format.");
                }
            }
            return dataArray;
        }

        /**
         * 简单的HTTP请求实现
         */
        private String doHttpRequest(String urlStr, String method, String body, Configuration headers) throws Exception {
            RequestConfig requestConfig = RequestConfig.custom().build();

            try (CloseableHttpClient client = HttpClients.custom()
                    .setDefaultRequestConfig(requestConfig)
                    .build()) {

                HttpUriRequestBase request = buildRequest(urlStr, method, body);

                if (headers != null && !headers.getKeys().isEmpty()) {
                    for (String key : headers.getKeys()) {
                        String value = headers.getString(key);
                        if (StringUtils.isNotBlank(key) && value != null) {
                            request.addHeader(key, value);
                        }
                    }
                }

                try (CloseableHttpResponse response = client.execute(request)) {
                    int status = response.getCode();
                    if (status >= 200 && status < 300) {
                        return EntityUtils.toString(response.getEntity(), StandardCharsets.UTF_8);
                    }
                    throw new RuntimeException("API Call failed. Http Code: " + status);
                }
            }
        }

        private HttpUriRequestBase buildRequest(String urlStr, String method, String body) {
            String verb = StringUtils.defaultIfBlank(method, "GET").toUpperCase();
            HttpUriRequestBase request;
            switch (verb) {
                case "POST":
                    request = new HttpPost(urlStr);
                    break;
                case "PUT":
                    request = new HttpPut(urlStr);
                    break;
                case "DELETE":
                    request = new HttpDelete(urlStr);
                    break;
                default:
                    request = new HttpGet(urlStr);
                    break;
            }

            if (request instanceof HttpPost || request instanceof HttpPut) {
                if (StringUtils.isNotBlank(body)) {
                    request.setEntity(new StringEntity(body, ContentType.APPLICATION_JSON));
                }
            }
            return request;
        }

        @Override
        public void destroy() {

        }
    }
}