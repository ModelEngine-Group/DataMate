package com.datamate.common.setting.interfaces.rest;

import com.datamate.common.setting.application.SysParamApplicationService;
import com.datamate.common.setting.interfaces.rest.dto.ParamRequest;
import com.datamate.common.setting.domain.entity.SysParam;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 系统参数控制器
 *
 * @author dallas
 * @since 2025-11-04
 */
@RestController
@RequestMapping("/sys-param")
@RequiredArgsConstructor
public class SysParamController {
    private final SysParamApplicationService sysParamApplicationService;

    /**
     * 获取系统参数列表
     *
     * @return 系统参数列表
     */
    @GetMapping("/list")
    public List<SysParam> list() {
        return sysParamApplicationService.list();
    }

    /**
     * 根据参数id修改系统参数值
     *
     * @param paramId    参数id
     * @param paramRequest 参数值请求体
     */
    @PutMapping("/{paramId}")
    public void updateParamValueById(@PathVariable("paramId") String paramId, @RequestBody ParamRequest paramRequest) {
        sysParamApplicationService.updateParamValueById(paramId, paramRequest.paramValue());
    }

    /**
     * 根据参数id删除系统参数
     *
     * @param paramId 参数id
     */
    @DeleteMapping("/{paramId}")
    public void deleteParamById(@PathVariable("paramId") String paramId) {
        sysParamApplicationService.deleteParamById(paramId);
    }
}

