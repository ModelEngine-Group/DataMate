package com.datamate.plugin.reader.s3reader;

import java.net.IDN;
import java.net.InetAddress;
import java.net.URI;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

final class HttpEndpointSecurity {
    private static final String ALLOWED_HOSTS_PROPERTY = "datamate.ssrf.allowedHosts";
    private static final String ALLOWED_HOSTS_ENV = "DATAMATE_SSRF_ALLOWED_HOSTS";

    private HttpEndpointSecurity() {
    }

    static URI validateExternalHttpUri(String rawUri, String fieldName) {
        if (isBlank(rawUri)) {
            throw new IllegalArgumentException(fieldName + " is required");
        }
        if (rawUri.indexOf('\r') >= 0 || rawUri.indexOf('\n') >= 0) {
            throw new IllegalArgumentException(fieldName + " contains invalid control characters");
        }

        URI uri = URI.create(rawUri.trim()).normalize();
        String scheme = uri.getScheme() == null ? null : uri.getScheme().toLowerCase(Locale.ROOT);
        if (!"http".equals(scheme) && !"https".equals(scheme)) {
            throw new IllegalArgumentException(fieldName + " only supports http or https");
        }
        if (!isBlank(uri.getUserInfo())) {
            throw new IllegalArgumentException(fieldName + " must not contain user info");
        }
        if (uri.getFragment() != null) {
            throw new IllegalArgumentException(fieldName + " must not contain fragment");
        }
        int port = uri.getPort();
        if (port == 0 || port < -1 || port > 65535) {
            throw new IllegalArgumentException(fieldName + " contains invalid port");
        }

        String asciiHost = toAsciiHost(uri.getHost(), fieldName);
        if (isAllowedHost(asciiHost)) {
            return uri;
        }

        InetAddress[] addresses;
        try {
            addresses = InetAddress.getAllByName(asciiHost);
        } catch (Exception e) {
            throw new IllegalArgumentException(fieldName + " host cannot be resolved", e);
        }
        if (addresses.length == 0) {
            throw new IllegalArgumentException(fieldName + " host cannot be resolved");
        }
        for (InetAddress address : addresses) {
            if (!isPublicRoutableAddress(address)) {
                throw new IllegalArgumentException(fieldName + " points to a restricted network address");
            }
        }
        return uri;
    }

    private static String toAsciiHost(String host, String fieldName) {
        if (isBlank(host)) {
            throw new IllegalArgumentException(fieldName + " must contain a valid host");
        }
        try {
            String normalized = host.endsWith(".") ? host.substring(0, host.length() - 1) : host;
            return IDN.toASCII(normalized, IDN.USE_STD3_ASCII_RULES).toLowerCase(Locale.ROOT);
        } catch (Exception e) {
            throw new IllegalArgumentException(fieldName + " contains invalid host", e);
        }
    }

    private static boolean isAllowedHost(String host) {
        return configuredAllowedHosts().contains(host);
    }

    private static Set<String> configuredAllowedHosts() {
        Set<String> hosts = new HashSet<String>();
        addConfiguredHosts(hosts, System.getProperty(ALLOWED_HOSTS_PROPERTY));
        addConfiguredHosts(hosts, System.getenv(ALLOWED_HOSTS_ENV));
        return hosts;
    }

    private static void addConfiguredHosts(Set<String> hosts, String rawHosts) {
        if (isBlank(rawHosts)) {
            return;
        }
        String[] parts = rawHosts.split(",");
        for (String part : parts) {
            if (!isBlank(part)) {
                hosts.add(toAsciiHost(part.trim(), "allowed host"));
            }
        }
    }

    private static boolean isPublicRoutableAddress(InetAddress address) {
        if (address.isAnyLocalAddress() || address.isLoopbackAddress() || address.isLinkLocalAddress()
                || address.isSiteLocalAddress() || address.isMulticastAddress()) {
            return false;
        }
        byte[] bytes = address.getAddress();
        if (bytes.length == 4) {
            return isPublicRoutableIpv4(bytes);
        }
        if (bytes.length == 16) {
            return isPublicRoutableIpv6(bytes);
        }
        return false;
    }

    private static boolean isPublicRoutableIpv4(byte[] bytes) {
        int first = bytes[0] & 0xff;
        int second = bytes[1] & 0xff;
        int third = bytes[2] & 0xff;
        if (first == 0 || first == 10 || first == 127 || first >= 224) {
            return false;
        }
        if (first == 100 && second >= 64 && second <= 127) {
            return false;
        }
        if (first == 169 && second == 254) {
            return false;
        }
        if (first == 172 && second >= 16 && second <= 31) {
            return false;
        }
        if (first == 192 && second == 168) {
            return false;
        }
        if (first == 192 && second == 0 && (third == 0 || third == 2)) {
            return false;
        }
        if (first == 198 && (second == 18 || second == 19 || (second == 51 && third == 100))) {
            return false;
        }
        if (first == 203 && second == 0 && third == 113) {
            return false;
        }
        return true;
    }

    private static boolean isPublicRoutableIpv6(byte[] bytes) {
        int first = bytes[0] & 0xff;
        int second = bytes[1] & 0xff;
        if ((first & 0xfe) == 0xfc) {
            return false;
        }
        if (first == 0xfe && (second & 0xc0) == 0x80) {
            return false;
        }
        if (first == 0x20 && second == 0x01 && (bytes[2] & 0xff) == 0x0d && (bytes[3] & 0xff) == 0xb8) {
            return false;
        }
        return !isIpv4MappedPrivateAddress(bytes);
    }

    private static boolean isIpv4MappedPrivateAddress(byte[] bytes) {
        for (int i = 0; i < 10; i++) {
            if (bytes[i] != 0) {
                return false;
            }
        }
        if ((bytes[10] & 0xff) != 0xff || (bytes[11] & 0xff) != 0xff) {
            return false;
        }
        byte[] ipv4 = new byte[] {bytes[12], bytes[13], bytes[14], bytes[15]};
        return !isPublicRoutableIpv4(ipv4);
    }

    private static boolean isBlank(String value) {
        return value == null || value.trim().isEmpty();
    }
}
