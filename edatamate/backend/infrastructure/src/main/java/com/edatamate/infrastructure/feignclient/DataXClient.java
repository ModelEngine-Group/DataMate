package com.edatamate.infrastructure.feignclient;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import java.util.Map;

@Component
@FeignClient(name = "dataxClient", url = "${datax.url}")
public interface DataXClient {

    @PostMapping("/process")
    Map<String, Object> process(@RequestBody Map<String, Object> params);
}