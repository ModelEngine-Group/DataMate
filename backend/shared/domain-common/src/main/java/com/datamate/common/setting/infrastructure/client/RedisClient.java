package com.datamate.common.setting.infrastructure.client;

import com.datamate.common.setting.infrastructure.utils.FunctionUtil;
import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@AllArgsConstructor
public class RedisClient {
    private final StringRedisTemplate redisTemplate;

    public void setParam(String key, String value) {
        FunctionUtil.doWithoutThrow((k, v) -> redisTemplate.opsForValue().set(k, v), key, value);
    }

    public String getParam(String key) {
        return FunctionUtil.getWithoutThrow((k) -> redisTemplate.opsForValue().get(k), key);
    }

    public void delParam(String key) {
        FunctionUtil.doWithoutThrow(redisTemplate::delete, key);
    }
}
