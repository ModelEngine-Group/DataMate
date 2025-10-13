package com.dataengine.datamanagement.application.service;

import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import com.dataengine.datamanagement.domain.model.dataset.StatusConstants;
import com.dataengine.datamanagement.domain.model.dataset.Tag;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.DatasetFileMapper;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.DatasetMapper;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.TagMapper;
import com.dataengine.datamanagement.interfaces.dto.CreateDatasetRequest;
import com.dataengine.datamanagement.interfaces.dto.DatasetPagingQuery;
import org.apache.ibatis.session.RowBounds;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;

import java.time.LocalDateTime;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class DatasetApplicationServiceTest {

    @Mock
    private DatasetMapper datasetMapper;

    @Mock
    private TagMapper tagMapper;

    @Mock
    private DatasetFileMapper datasetFileMapper;

    @InjectMocks
    private DatasetApplicationService service;

    private Dataset sampleDataset;
    private Tag sampleTag;

    @BeforeEach
    void setUp() {
        service = new DatasetApplicationService(datasetMapper, tagMapper, datasetFileMapper);

        sampleDataset = new Dataset();
        sampleDataset.setId("dataset-id-1");
        sampleDataset.setName("Sample Dataset");
        sampleDataset.setDescription("Test dataset");
        sampleDataset.setDatasetType("CSV");
        sampleDataset.setStatus(StatusConstants.DatasetStatuses.ACTIVE);
        sampleDataset.setCreatedAt(LocalDateTime.now());
        sampleDataset.setUpdatedAt(LocalDateTime.now());

        sampleTag = new Tag();
        sampleTag.setId("tag-id-1");
        sampleTag.setName("test-tag");
        sampleTag.setUsageCount(1L);
    }

    @Test
    @DisplayName("createDataset: 正常创建数据集，带标签")
    void createDataset_success_withTags() {
        // Given
        List<String> tagNames = Arrays.asList("tag1", "tag2");
        when(datasetMapper.findByName("New Dataset")).thenReturn(null);
        when(tagMapper.findByName("tag1")).thenReturn(null);
        when(tagMapper.findByName("tag2")).thenReturn(sampleTag);

        when(datasetMapper.insert(any(Dataset.class))).thenReturn(1);
        when(datasetMapper.findById(anyString())).thenReturn(sampleDataset);
        when(tagMapper.insert(any(Tag.class))).thenReturn(1);

        // When
        Dataset result = service.createDataset(new CreateDatasetRequest("New Dataset", "Description", "CSV",
                tagNames, "1", "/path"));

        // Then
        assertNotNull(result);
        verify(datasetMapper).findByName("New Dataset");

        ArgumentCaptor<Dataset> datasetCaptor = ArgumentCaptor.forClass(Dataset.class);
        verify(datasetMapper).insert(datasetCaptor.capture());
        Dataset inserted = datasetCaptor.getValue();
        assertNotNull(inserted.getId());
        assertEquals("New Dataset", inserted.getName());
        assertEquals(StatusConstants.DatasetStatuses.ACTIVE, inserted.getStatus());

        verify(tagMapper).insert(any(Tag.class)); // tag1 创建
        verify(tagMapper).updateUsageCount(eq(sampleTag.getId()), eq(2L)); // tag2 使用次数+1
        verify(tagMapper, times(2)).insertDatasetTag(anyString(), anyString());
        verify(datasetMapper).findById(anyString());
    }

    @Test
    @DisplayName("createDataset: 名称重复时抛异常")
    void createDataset_duplicateName() {
        when(datasetMapper.findByName("Duplicate")).thenReturn(sampleDataset);

        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> service.createDataset(new CreateDatasetRequest("Duplicate", "desc", "CSV", null, "1L", "/path")));

        assertTrue(ex.getMessage().contains("already exists"));
        verify(datasetMapper).findByName("Duplicate");
        verify(datasetMapper, never()).insert(any());
    }

    @Test
    @DisplayName("createDataset: 无标签创建")
    void createDataset_withoutTags() {
        when(datasetMapper.findByName("No Tags Dataset")).thenReturn(null);
        when(datasetMapper.insert(any(Dataset.class))).thenReturn(1);
        when(datasetMapper.findById(anyString())).thenReturn(sampleDataset);

        Dataset result = service.createDataset(new CreateDatasetRequest("No Tags Dataset", "desc", "CSV",
                null, "1L", "/path"));

        assertNotNull(result);
        verify(tagMapper, never()).insertDatasetTag(anyString(), anyString());
        verify(datasetMapper).insert(any(Dataset.class));
    }

    @Test
    @DisplayName("updateDataset: 数据集不存在时抛异常")
    void updateDataset_notFound() {
        when(datasetMapper.findById("not-exist")).thenReturn(null);

        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> service.updateDataset("not-exist", "name", "desc", null, "active"));

        assertTrue(ex.getMessage().contains("Dataset not found"));
        verify(datasetMapper).findById("not-exist");
        verify(datasetMapper, never()).update(any());
    }

    @Test
    @DisplayName("updateDataset: 标签参数为null时保持原有标签")
    void updateDataset_keepExistingTags() {
        List<Tag> existingTags = Arrays.asList(sampleTag);
        when(datasetMapper.findById("dataset-id-1")).thenReturn(sampleDataset);
        when(tagMapper.findByDatasetId("dataset-id-1")).thenReturn(existingTags);
        when(datasetMapper.update(any(Dataset.class))).thenReturn(1);
        when(datasetMapper.findById("dataset-id-1")).thenReturn(sampleDataset);

        Dataset result = service.updateDataset("dataset-id-1", "Updated Name", null, null, null);

        assertNotNull(result);
        verify(tagMapper, never()).deleteDatasetTagsByDatasetId(anyString());
        verify(tagMapper).findByDatasetId("dataset-id-1");
        verify(datasetMapper).update(any(Dataset.class));
    }

    @Test
    @DisplayName("deleteDataset: 正常删除数据集")
    void deleteDataset_success() {
        when(datasetMapper.findById("dataset-id-1")).thenReturn(sampleDataset);
        when(tagMapper.deleteDatasetTagsByDatasetId("dataset-id-1")).thenReturn(1);
        when(datasetMapper.deleteById("dataset-id-1")).thenReturn(1);

        assertDoesNotThrow(() -> service.deleteDataset("dataset-id-1"));

        verify(datasetMapper).findById("dataset-id-1");
        verify(tagMapper).deleteDatasetTagsByDatasetId("dataset-id-1");
        verify(datasetMapper).deleteById("dataset-id-1");
    }

    @Test
    @DisplayName("deleteDataset: 数据集不存在时抛异常")
    void deleteDataset_notFound() {
        when(datasetMapper.findById("not-exist")).thenReturn(null);

        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> service.deleteDataset("not-exist"));

        assertTrue(ex.getMessage().contains("Dataset not found"));
        verify(datasetMapper).findById("not-exist");
        verify(datasetMapper, never()).deleteById(anyString());
    }

    @Test
    @DisplayName("getDataset: 正常获取数据集详情")
    void getDataset_success() {
        List<Tag> tags = Arrays.asList(sampleTag);
        when(datasetMapper.findById("dataset-id-1")).thenReturn(sampleDataset);
        when(tagMapper.findByDatasetId("dataset-id-1")).thenReturn(tags);

        Dataset result = service.getDataset("dataset-id-1");

        assertNotNull(result);
        assertSame(sampleDataset, result);
        verify(datasetMapper).findById("dataset-id-1");
        verify(tagMapper).findByDatasetId("dataset-id-1");
    }

    @Test
    @DisplayName("getDataset: 数据集不存在时抛异常")
    void getDataset_notFound() {
        when(datasetMapper.findById("not-exist")).thenReturn(null);

        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> service.getDataset("not-exist"));

        assertTrue(ex.getMessage().contains("Dataset not found"));
        verify(datasetMapper).findById("not-exist");
    }

    @Test
    @DisplayName("getDatasets: 分页查询数据集")
    void getDatasets_pagination() {
        List<Dataset> datasets = Arrays.asList(sampleDataset);
        List<Tag> tags = Arrays.asList(sampleTag);

        when(datasetMapper.findByCriteria(eq("CSV"), eq("ACTIVE"), eq("test"),
                eq(Arrays.asList("tag1")), any(RowBounds.class))).thenReturn(datasets);
        when(datasetMapper.countByCriteria("CSV", "ACTIVE", "test", Arrays.asList("tag1"))).thenReturn(1L);
        when(tagMapper.findByDatasetId("dataset-id-1")).thenReturn(tags);

        Page<Dataset> result = service.getDatasets(new DatasetPagingQuery("CSV", "ACTIVE", "test", "tag1"));

        assertNotNull(result);
        assertEquals(1, result.getContent().size());
        assertEquals(1L, result.getTotalElements());
        verify(datasetMapper).findByCriteria(eq("CSV"), eq("ACTIVE"), eq("test"),
                eq(Arrays.asList("tag1")), any(RowBounds.class));
        verify(datasetMapper).countByCriteria("CSV", "ACTIVE", "test", Arrays.asList("tag1"));
        verify(tagMapper).findByDatasetId("dataset-id-1");
    }

    @Test
    @DisplayName("getDatasets: 空结果集")
    void getDatasets_emptyResult() {
        when(datasetMapper.findByCriteria(isNull(), isNull(), isNull(),
                isNull(), any(RowBounds.class))).thenReturn(Collections.emptyList());
        when(datasetMapper.countByCriteria(null, null, null, null)).thenReturn(0L);

        Page<Dataset> result = service.getDatasets(new DatasetPagingQuery());

        assertNotNull(result);
        assertTrue(result.getContent().isEmpty());
        assertEquals(0L, result.getTotalElements());
        verify(tagMapper, never()).findByDatasetId(anyString());
    }

    @Test
    @DisplayName("getDatasetStatistics: 正常获取统计信息")
    void getDatasetStatistics_success() {
        when(datasetMapper.findById("dataset-id-1")).thenReturn(sampleDataset);
        when(datasetFileMapper.countByDatasetId("dataset-id-1")).thenReturn(10L);
        when(datasetFileMapper.countCompletedByDatasetId("dataset-id-1")).thenReturn(8L);
        when(datasetFileMapper.sumSizeByDatasetId("dataset-id-1")).thenReturn(1024L);
        when(datasetFileMapper.findAllByDatasetId("dataset-id-1")).thenReturn(Collections.emptyList());

        Map<String, Object> result = service.getDatasetStatistics("dataset-id-1");

        assertNotNull(result);
        assertEquals(10, result.get("totalFiles"));
        assertEquals(8, result.get("completedFiles"));
        assertEquals(1024L, result.get("totalSize"));
        assertEquals(80.0f, result.get("completionRate"));
        assertNotNull(result.get("fileTypeDistribution"));
        assertNotNull(result.get("statusDistribution"));

        verify(datasetMapper).findById("dataset-id-1");
        verify(datasetFileMapper).countByDatasetId("dataset-id-1");
        verify(datasetFileMapper).countCompletedByDatasetId("dataset-id-1");
        verify(datasetFileMapper).sumSizeByDatasetId("dataset-id-1");
        verify(datasetFileMapper).findAllByDatasetId("dataset-id-1");
    }

    @Test
    @DisplayName("getDatasetStatistics: 数据集不存在时抛异常")
    void getDatasetStatistics_notFound() {
        when(datasetMapper.findById("not-exist")).thenReturn(null);

        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> service.getDatasetStatistics("not-exist"));

        assertTrue(ex.getMessage().contains("Dataset not found"));
        verify(datasetMapper).findById("not-exist");
        verify(datasetFileMapper, never()).countByDatasetId(anyString());
    }

    @Test
    @DisplayName("getDatasetStatistics: 零文件情况下完成率为0")
    void getDatasetStatistics_zeroFiles() {
        when(datasetMapper.findById("dataset-id-1")).thenReturn(sampleDataset);
        when(datasetFileMapper.countByDatasetId("dataset-id-1")).thenReturn(0L);
        when(datasetFileMapper.countCompletedByDatasetId("dataset-id-1")).thenReturn(0L);
        when(datasetFileMapper.sumSizeByDatasetId("dataset-id-1")).thenReturn(0L);
        when(datasetFileMapper.findAllByDatasetId("dataset-id-1")).thenReturn(Collections.emptyList());

        Map<String, Object> result = service.getDatasetStatistics("dataset-id-1");

        assertEquals(0, result.get("totalFiles"));
        assertEquals(0, result.get("completedFiles"));
        assertEquals(0.0f, result.get("completionRate"));
    }

    @Test
    @DisplayName("processTagNames: 处理混合标签（已存在和新建）")
    void processTagNames_mixedTags() {
        // 这个方法是private的，通过createDataset间接测试
        when(datasetMapper.findByName("Test Dataset")).thenReturn(null);
        when(tagMapper.findByName("existing")).thenReturn(sampleTag);
        when(tagMapper.findByName("new")).thenReturn(null);
        when(datasetMapper.insert(any(Dataset.class))).thenReturn(1);
        when(datasetMapper.findById(anyString())).thenReturn(sampleDataset);
        when(tagMapper.insert(any(Tag.class))).thenReturn(1);

        List<String> tagNames = Arrays.asList("existing", "new");
        service.createDataset(new CreateDatasetRequest("Test Dataset", "desc", "CSV", tagNames, "1L", "/path"));

        verify(tagMapper).findByName("existing");
        verify(tagMapper).findByName("new");
        verify(tagMapper).insert(any(Tag.class)); // 新标签
        verify(tagMapper).updateUsageCount(eq(sampleTag.getId()), eq(2L)); // 已存在标签使用次数+1
        verify(tagMapper, times(2)).insertDatasetTag(anyString(), anyString());
    }
}
