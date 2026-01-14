package com.datamate.gateway.infrastructure.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.gateway.domain.entity.User;
import org.apache.ibatis.annotations.Mapper;

/**
 * UserMapper
 *
 * @since 2026/1/12
 */
@Mapper
public interface UserMapper extends BaseMapper<User> {
}
