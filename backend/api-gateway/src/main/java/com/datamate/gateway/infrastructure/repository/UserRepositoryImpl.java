package com.datamate.gateway.infrastructure.repository;

import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.gateway.domain.entity.User;
import com.datamate.gateway.domain.repository.UserRepository;
import com.datamate.gateway.infrastructure.mapper.UserMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

/**
 * UserRepositoryImpl
 *
 * @since 2026/1/12
 */
@Repository
@RequiredArgsConstructor
public class UserRepositoryImpl extends CrudRepository<UserMapper, User> implements UserRepository {
}
