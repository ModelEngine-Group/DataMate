package com.edatamate.application.datax;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import java.util.Map;

@FeignClient(name = "dataxClient", url = "${datax.url}")
public interface DataXClient {

    @PostMapping("/process")
    Map<String, Object> process(@RequestBody Map<String, Object> params);
}