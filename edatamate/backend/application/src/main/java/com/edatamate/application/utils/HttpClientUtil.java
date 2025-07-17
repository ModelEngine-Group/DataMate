package com.edatamate.application.utils;

import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.security.KeyManagementException;
import java.security.NoSuchAlgorithmException;
import java.security.cert.X509Certificate;
import java.time.Duration;

public final class HttpClientUtil {

    private static final HttpClient HTTP_CLIENT;
    private static final HttpClient HTTPS_CLIENT;

    static {
        // 普通 HTTP 客户端
        HTTP_CLIENT = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();

        // 信任全部证书的 HTTPS 客户端（生产环境请使用真实证书）
        HTTPS_CLIENT = createInsecureHttpsClient();
    }

    /**
     * 发送 GET 请求
     *
     * @param url 请求地址
     * @return 响应体字符串
     */
    public static String get(String url) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .GET()
                .build();
        return send(request, url);
    }

    /**
     * 发送 POST 请求（JSON 格式）
     *
     * @param url  请求地址
     * @param json JSON 请求体
     * @return 响应体字符串
     */
    public static String postJson(String url, String json) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();
        return send(request, url);
    }

    /**
     * 公共发送方法
     */
    private static String send(HttpRequest request, String url) throws IOException, InterruptedException {
        HttpClient client = url.startsWith("https") ? HTTPS_CLIENT : HTTP_CLIENT;
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() >= 200 && response.statusCode() < 300) {
            return response.body();
        } else {
            throw new RuntimeException(
                    "HTTP request failed, status=" + response.statusCode() + ", body=" + response.body());
        }
    }

    /**
     * 创建一个信任全部证书的 HTTPS 客户端（仅示例用，生产环境请用真实证书）
     */
    private static HttpClient createInsecureHttpsClient() {
        try {
            TrustManager[] trustAllCerts = new TrustManager[]{
                    new X509TrustManager() {
                        public X509Certificate[] getAcceptedIssuers() { return null; }
                        public void checkClientTrusted(X509Certificate[] certs, String authType) {}
                        public void checkServerTrusted(X509Certificate[] certs, String authType) {}
                    }
            };
            SSLContext sslContext = SSLContext.getInstance("TLS");
            sslContext.init(null, trustAllCerts, new java.security.SecureRandom());

            return HttpClient.newBuilder()
                    .sslContext(sslContext)
                    .connectTimeout(Duration.ofSeconds(10))
                    .build();
        } catch (NoSuchAlgorithmException | KeyManagementException e) {
            throw new RuntimeException("Unable to create insecure HTTPS client", e);
        }
    }

    // 私有构造方法，防止实例化
    private HttpClientUtil() {}
}