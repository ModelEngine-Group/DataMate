package com.datamate.plugin.reader.s3reader;

import org.junit.Test;

import static org.junit.Assert.assertEquals;

public class HttpEndpointSecurityTest {
    @Test(expected = IllegalArgumentException.class)
    public void shouldRejectLoopbackHost() {
        HttpEndpointSecurity.validateExternalHttpUri("http://127.0.0.1:9000", "endpoint");
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldRejectLocalhost() {
        HttpEndpointSecurity.validateExternalHttpUri("http://localhost:9000", "endpoint");
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldRejectIpv6LoopbackHost() {
        HttpEndpointSecurity.validateExternalHttpUri("http://[::1]:9000", "endpoint");
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldRejectIpv4MappedIpv6LoopbackHost() {
        HttpEndpointSecurity.validateExternalHttpUri("http://[::ffff:127.0.0.1]:9000", "endpoint");
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldRejectIntegerEncodedLoopbackHost() {
        HttpEndpointSecurity.validateExternalHttpUri("http://2130706433:9000", "endpoint");
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldRejectHexEncodedLoopbackHost() {
        HttpEndpointSecurity.validateExternalHttpUri("http://0x7f000001:9000", "endpoint");
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldRejectOctalEncodedLoopbackHost() {
        HttpEndpointSecurity.validateExternalHttpUri("http://017700000001:9000", "endpoint");
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldRejectMetadataServiceAddress() {
        HttpEndpointSecurity.validateExternalHttpUri("http://169.254.169.254/latest/meta-data", "endpoint");
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldRejectPrivateNetworkAddress() {
        HttpEndpointSecurity.validateExternalHttpUri("http://192.168.1.10:9000", "endpoint");
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldRejectUnsupportedScheme() {
        HttpEndpointSecurity.validateExternalHttpUri("gopher://8.8.8.8:70", "endpoint");
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldRejectUserInfo() {
        HttpEndpointSecurity.validateExternalHttpUri("http://user@8.8.8.8:9000", "endpoint");
    }

    @Test
    public void shouldAllowPublicHttpAddress() {
        assertEquals("8.8.8.8",
                HttpEndpointSecurity.validateExternalHttpUri("https://8.8.8.8:9000", "endpoint").getHost());
    }

    @Test
    public void shouldAllowExplicitlyConfiguredHost() {
        String previous = System.getProperty("datamate.ssrf.allowedHosts");
        try {
            System.setProperty("datamate.ssrf.allowedHosts", "localhost");
            assertEquals("localhost",
                    HttpEndpointSecurity.validateExternalHttpUri("http://localhost:9000", "endpoint").getHost());
        } finally {
            if (previous == null) {
                System.clearProperty("datamate.ssrf.allowedHosts");
            } else {
                System.setProperty("datamate.ssrf.allowedHosts", previous);
            }
        }
    }
}
