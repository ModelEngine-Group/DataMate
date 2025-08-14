package com.dataengine.collection.application.service;

import com.dataengine.collection.application.dto.DataSourceCreateDTO;
import com.dataengine.collection.application.dto.DataSourceUpdateDTO;
import com.dataengine.collection.application.dto.DataSourceDTO;
import com.dataengine.collection.application.dto.ConnectionTestResultDTO;
import com.dataengine.collection.domain.model.*;
import com.dataengine.collection.domain.repository.DataSourceRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;
import java.util.Optional;

/**
 * 数据源应用服务
 */
@Service
@Transactional
public class DataSourceApplicationService {

    private final DataSourceRepository dataSourceRepository;
    private final DataSourceConnectionService connectionService;

    public DataSourceApplicationService(DataSourceRepository dataSourceRepository,
                                      DataSourceConnectionService connectionService) {
        this.dataSourceRepository = dataSourceRepository;
        this.connectionService = connectionService;
    }

    /**
     * 创建数据源
     */
    public DataSourceDTO createDataSource(DataSourceCreateDTO createDTO) {
        // 检查名称是否已存在
        if (dataSourceRepository.findByName(createDTO.getName()).isPresent()) {
            throw new IllegalArgumentException("Data source name already exists: " + createDTO.getName());
        }

        DataSourceId id = DataSourceId.generate();
        DataSource dataSource = new DataSource(
            id,
            createDTO.getName(),
            createDTO.getType(),
            createDTO.getDescription(),
            createDTO.getConfig()
        );

        DataSource saved = dataSourceRepository.save(dataSource);
        return convertToDTO(saved);
    }

    /**
     * 更新数据源
     */
    public DataSourceDTO updateDataSource(String id, DataSourceUpdateDTO updateDTO) {
        DataSourceId dataSourceId = DataSourceId.of(id);
        DataSource dataSource = dataSourceRepository.findById(dataSourceId)
            .orElseThrow(() -> new IllegalArgumentException("Data source not found: " + id));

        if (updateDTO.getConfig() != null) {
            dataSource.updateConfig(updateDTO.getConfig());
        }

        DataSource saved = dataSourceRepository.save(dataSource);
        return convertToDTO(saved);
    }

    /**
     * 获取数据源详情
     */
    @Transactional(readOnly = true)
    public Optional<DataSourceDTO> getDataSource(String id) {
        DataSourceId dataSourceId = DataSourceId.of(id);
        return dataSourceRepository.findById(dataSourceId)
            .map(this::convertToDTO);
    }

    /**
     * 分页查询数据源
     */
    @Transactional(readOnly = true)
    public Page<DataSourceDTO> getDataSources(Pageable pageable, DataSourceType type) {
        Page<DataSource> page = type != null 
            ? dataSourceRepository.findByType(type, pageable)
            : dataSourceRepository.findAll(pageable);
        
        return page.map(this::convertToDTO);
    }

    /**
     * 删除数据源
     */
    public void deleteDataSource(String id) {
        DataSourceId dataSourceId = DataSourceId.of(id);
        if (!dataSourceRepository.existsById(dataSourceId)) {
            throw new IllegalArgumentException("Data source not found: " + id);
        }
        dataSourceRepository.deleteById(dataSourceId);
    }

    /**
     * 测试数据源连接
     */
    public ConnectionTestResultDTO testConnection(String id) {
        DataSourceId dataSourceId = DataSourceId.of(id);
        DataSource dataSource = dataSourceRepository.findById(dataSourceId)
            .orElseThrow(() -> new IllegalArgumentException("Data source not found: " + id));

        return connectionService.testConnection(dataSource);
    }

    /**
     * 激活数据源
     */
    public void activateDataSource(String id) {
        DataSourceId dataSourceId = DataSourceId.of(id);
        DataSource dataSource = dataSourceRepository.findById(dataSourceId)
            .orElseThrow(() -> new IllegalArgumentException("Data source not found: " + id));

        dataSource.activate();
        dataSourceRepository.save(dataSource);
    }

    private DataSourceDTO convertToDTO(DataSource dataSource) {
        return new DataSourceDTO(
            dataSource.getId().getValue(),
            dataSource.getName(),
            dataSource.getType(),
            dataSource.getDescription(),
            dataSource.getConfig(),
            dataSource.getStatus().name(),
            dataSource.getCreatedAt(),
            dataSource.getUpdatedAt()
        );
    }
}
