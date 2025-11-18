package com.datamate.common.setting.application;

import com.datamate.common.infrastructure.exception.BusinessAssert;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.datamate.common.setting.domain.entity.SysParam;
import com.datamate.common.setting.domain.repository.SysParamRepository;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.util.Comparator;
import java.util.List;

/**
 * 系统参数应用服务
 *
 * @author dallas
 * @since 2025-11-04
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SysParamApplicationService {
    private final SysParamRepository sysParamRepository;
    private final StringRedisTemplate redisTemplate;

    /**
     * 列表查询系统参数
     *
     * @return 系统参数列表
     */
    public List<SysParam> list() {
        List<SysParam> sysParams = sysParamRepository.list();
        sysParams.sort(Comparator.comparing(SysParam::getParamType));
        return sysParams;
    }

    /**
     * 根据参数id修改系统参数值
     *
     * @param paramId    参数id
     * @param paramValue 参数值
     */
    public void updateParamValueById(String paramId, String paramValue) {
        SysParam sysParam = sysParamRepository.getById(paramId);
        BusinessAssert.notNull(sysParam, SystemErrorCode.RESOURCE_NOT_FOUND);
        sysParam.setParamValue(paramValue);
        sysParamRepository.updateById(sysParam);
        redisTemplate.opsForValue().set(sysParam.getParamKey(), paramValue);
    }

    public void deleteParamById(String paramId) {
        SysParam sysParam = sysParamRepository.getById(paramId);
        BusinessAssert.notNull(sysParam, SystemErrorCode.RESOURCE_NOT_FOUND);
        sysParamRepository.removeById(paramId);
        redisTemplate.delete(sysParam.getParamKey());
    }

    /**
     * 初始化系统参数到Redis
     */
    @PostConstruct
    public void init() {
        try {
            List<SysParam> sysParams = sysParamRepository.list();
            sysParams.forEach(sysParam -> redisTemplate.opsForValue().set(sysParam.getParamKey(), sysParam.getParamValue()));
        } catch (Exception e) {
            log.error("Init sys params to redis error", e);
        }
    }
}
