package com.datamate.common.setting.infrastructure.persistence.impl;

import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.common.setting.domain.entity.SysParam;
import com.datamate.common.setting.domain.repository.SysParamRepository;
import com.datamate.common.setting.infrastructure.persistence.mapper.SysParamMapper;
import org.springframework.stereotype.Repository;

/**
 * 系统参数仓储实现类
 *
 * @author dallas
 * @since 2025-11-04
 */
@Repository
public class SysParamRepositoryImpl extends CrudRepository<SysParamMapper, SysParam> implements SysParamRepository {
}
