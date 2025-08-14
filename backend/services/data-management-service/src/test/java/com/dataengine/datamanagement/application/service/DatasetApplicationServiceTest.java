package com.dataengine.datamanagement.application.service;

import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import com.dataengine.datamanagement.domain.model.dataset.DatasetStatus;
import com.dataengine.datamanagement.domain.repository.DatasetRepository;
import com.dataengine.datamanagement.domain.repository.TagRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;

import java.util.Arrays;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

/**
 * 数据集应用服务测试
 */
@ExtendWith(MockitoExtension.class)
class DatasetApplicationServiceTest {

    @Mock
    private DatasetRepository datasetRepository;

    @Mock
    private TagRepository tagRepository;

    @InjectMocks
    private DatasetApplicationService datasetApplicationService;

    @Test
    void testCreateDataset() {
        // Given
        when(datasetRepository.findByName(anyString())).thenReturn(Optional.empty());
        when(datasetRepository.save(any(Dataset.class))).thenAnswer(invocation -> invocation.getArgument(0));

        // When
        Dataset result = datasetApplicationService.createDataset(
            "Test Dataset",
            "Test Description",
            "IMAGE",
            "图像数据集",
            "测试图像数据集",
            Arrays.asList("tag1", "tag2"),
            "test source",
            "test location",
            "testUser"
        );

        // Then
        assertNotNull(result);
        assertEquals("Test Dataset", result.getName());
        assertEquals("Test Description", result.getDescription());
        assertEquals("IMAGE", result.getType().getCode());
        assertEquals(DatasetStatus.ACTIVE, result.getStatus());
        
        verify(datasetRepository).findByName("Test Dataset");
        verify(datasetRepository).save(any(Dataset.class));
    }

    @Test
    void testCreateDatasetWithDuplicateName() {
        // Given
        Dataset existingDataset = mock(Dataset.class);
        when(datasetRepository.findByName(anyString())).thenReturn(Optional.of(existingDataset));

        // When & Then
        assertThrows(IllegalArgumentException.class, () -> {
            datasetApplicationService.createDataset(
                "Existing Dataset",
                "Test Description",
                "IMAGE",
                "图像数据集",
                "测试图像数据集",
                null,
                "test source",
                "test location",
                "testUser"
            );
        });
    }

    @Test
    void testGetDataset() {
        // Given
        Dataset dataset = mock(Dataset.class);
        when(datasetRepository.findById(anyString())).thenReturn(Optional.of(dataset));

        // When
        Dataset result = datasetApplicationService.getDataset("test-id");

        // Then
        assertNotNull(result);
        verify(datasetRepository).findById("test-id");
    }

    @Test
    void testGetDatasetNotFound() {
        // Given
        when(datasetRepository.findById(anyString())).thenReturn(Optional.empty());

        // When & Then
        assertThrows(IllegalArgumentException.class, () -> {
            datasetApplicationService.getDataset("non-existent-id");
        });
    }

    @Test
    void testGetDatasets() {
        // Given
        Dataset dataset1 = mock(Dataset.class);
        Dataset dataset2 = mock(Dataset.class);
        Page<Dataset> datasetsPage = new PageImpl<>(Arrays.asList(dataset1, dataset2));
        
        when(datasetRepository.findByCriteria(any(), any(), any(), any(), any()))
            .thenReturn(datasetsPage);

        // When
        Page<Dataset> result = datasetApplicationService.getDatasets(
            "IMAGE", 
            DatasetStatus.ACTIVE, 
            "test", 
            Arrays.asList("tag1"), 
            PageRequest.of(0, 10)
        );

        // Then
        assertNotNull(result);
        assertEquals(2, result.getContent().size());
        verify(datasetRepository).findByCriteria(any(), any(), any(), any(), any());
    }
}
