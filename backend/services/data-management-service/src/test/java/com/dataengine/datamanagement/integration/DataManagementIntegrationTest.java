package com.dataengine.datamanagement.integration;

import com.dataengine.datamanagement.application.service.DatasetApplicationService;
import com.dataengine.datamanagement.application.service.TagApplicationService;
import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import com.dataengine.datamanagement.domain.model.dataset.StatusConstants;
import com.dataengine.datamanagement.domain.model.dataset.Tag;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.DatasetFileMapper;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.DatasetMapper;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.TagMapper;
import com.dataengine.datamanagement.interfaces.dto.CreateDatasetRequest;
import com.dataengine.datamanagement.interfaces.dto.DatasetPagingQuery;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;

import java.time.LocalDateTime;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * 数据管理服务集成测试
 * 测试各个组件之间的协作和数据流转
 */
@ExtendWith(MockitoExtension.class)
class DataManagementIntegrationTest {

    @Mock
    private DatasetMapper datasetMapper;

    @Mock
    private TagMapper tagMapper;

    @Mock
    private DatasetFileMapper datasetFileMapper;

    private DatasetApplicationService datasetService;
    private TagApplicationService tagService;

    @BeforeEach
    void setUp() {
        tagService = new TagApplicationService(tagMapper);
        datasetService = new DatasetApplicationService(datasetMapper, tagMapper, datasetFileMapper);
    }

    @Test
    @DisplayName("完整数据集工作流: 创建标签 -> 创建数据集 -> 查询统计")
    void completeDatasetWorkflow() {
        // === 阶段1: 创建标签 ===
        String tagName = "machine-learning";
        String tagColor = "#FF5722";
        String tagDesc = "机器学习相关数据集";

        Tag createdTag = new Tag();
        createdTag.setId("tag-ml-001");
        createdTag.setName(tagName);
        createdTag.setColor(tagColor);
        createdTag.setDescription(tagDesc);
        createdTag.setUsageCount(0L);

        when(tagMapper.findByName(tagName)).thenReturn(null);
        when(tagMapper.insert(any(Tag.class))).thenReturn(1);
        when(tagMapper.findById(anyString())).thenReturn(createdTag);

        Tag tag = tagService.createTag(tagName, tagColor, tagDesc);
        assertNotNull(tag);
        assertEquals(tagName, tag.getName());

        // === 阶段2: 创建使用标签的数据集 ===
        String datasetName = "MNIST图像数据集";
        String datasetDesc = "手写数字识别数据集";
        String datasetType = "IMAGE";
        List<String> tagNames = Arrays.asList(tagName);

        Dataset createdDataset = new Dataset();
        createdDataset.setId("dataset-mnist-001");
        createdDataset.setName(datasetName);
        createdDataset.setDescription(datasetDesc);
        createdDataset.setDatasetType(datasetType);
        createdDataset.setStatus(StatusConstants.DatasetStatuses.ACTIVE);
        createdDataset.setCreatedAt(LocalDateTime.now());
        createdDataset.setFileCount(1000L);
        createdDataset.setSizeBytes(50 * 1024 * 1024L); // 50MB

        when(datasetMapper.findByName(datasetName)).thenReturn(null);
        when(datasetMapper.insert(any(Dataset.class))).thenReturn(1);
        when(datasetMapper.findById(anyString())).thenReturn(createdDataset);
        when(tagMapper.findByName(tagName)).thenReturn(createdTag);
        when(tagMapper.updateUsageCount(eq(createdTag.getId()), eq(1L))).thenReturn(1);
        when(tagMapper.insertDatasetTag(anyString(), eq(createdTag.getId()))).thenReturn(1);

        Dataset dataset = datasetService.createDataset(new CreateDatasetRequest(
            datasetName, datasetDesc, datasetType,tagNames, "1L", "/data/mnist")
        );

        assertNotNull(dataset);
        assertEquals(datasetName, dataset.getName());
        verify(tagMapper).updateUsageCount(eq(createdTag.getId()), eq(1L));
        verify(tagMapper).insertDatasetTag(anyString(), eq(createdTag.getId()));

        // === 阶段3: 查询数据集统计信息 ===
        when(datasetMapper.findById(anyString())).thenReturn(createdDataset);
        when(datasetFileMapper.countByDatasetId(anyString())).thenReturn(1000L);
        when(datasetFileMapper.countCompletedByDatasetId(anyString())).thenReturn(950L);
        when(datasetFileMapper.sumSizeByDatasetId(anyString())).thenReturn(50 * 1024 * 1024L);
        when(datasetFileMapper.findAllByDatasetId(anyString())).thenReturn(Collections.emptyList());

        Map<String, Object> stats = datasetService.getDatasetStatistics(dataset.getId());

        assertEquals(1000, stats.get("totalFiles"));
        assertEquals(950, stats.get("completedFiles"));
        assertEquals(95.0f, stats.get("completionRate"));
        assertEquals(50 * 1024 * 1024L, stats.get("totalSize"));

        // === 阶段4: 搜索数据集 ===
        List<Dataset> searchResult = Arrays.asList(createdDataset);
        List<Tag> datasetTags = Arrays.asList(createdTag);

        when(datasetMapper.findByCriteria(eq("IMAGE"), isNull(), eq("MNIST"),
                eq(Arrays.asList(tagName)), any())).thenReturn(searchResult);
        when(datasetMapper.countByCriteria(eq("IMAGE"), isNull(), eq("MNIST"),
                eq(Arrays.asList(tagName)))).thenReturn(1L);
        when(tagMapper.findByDatasetId(anyString())).thenReturn(datasetTags);

        Page<Dataset> searchResults = datasetService.getDatasets(new DatasetPagingQuery("IMAGE", null, "MNIST", tagName));

        assertEquals(1, searchResults.getContent().size());
        assertEquals(1L, searchResults.getTotalElements());

        Dataset foundDataset = searchResults.getContent().get(0);
        assertEquals(datasetName, foundDataset.getName());
    }

    @Test
    @DisplayName("标签使用计数工作流: 创建标签 -> 多个数据集使用 -> 验证使用次数")
    void tagUsageCountWorkflow() {
        // 创建标签
        Tag nlpTag = new Tag();
        nlpTag.setId("tag-nlp-001");
        nlpTag.setName("nlp");
        nlpTag.setUsageCount(0L);

        when(tagMapper.findByName("nlp")).thenReturn(null).thenReturn(nlpTag).thenReturn(nlpTag);
        when(tagMapper.insert(any(Tag.class))).thenReturn(1);
        when(tagMapper.findById(anyString())).thenReturn(nlpTag);

        Tag tag = tagService.createTag("nlp", "#2196F3", "自然语言处理");

        // 第一个数据集使用该标签
        Dataset dataset1 = new Dataset();
        dataset1.setId("dataset-text-001");
        dataset1.setName("文本分类数据集");

        when(datasetMapper.findByName("文本分类数据集")).thenReturn(null);
        when(datasetMapper.insert(any(Dataset.class))).thenReturn(1);
        when(datasetMapper.findById(anyString())).thenReturn(dataset1);
        when(tagMapper.updateUsageCount(eq(nlpTag.getId()), eq(1L))).thenReturn(1);
        when(tagMapper.insertDatasetTag(anyString(), eq(nlpTag.getId()))).thenReturn(1);

        datasetService.createDataset(new CreateDatasetRequest(
            "文本分类数据集", "情感分析数据", "TEXT",
            Arrays.asList("nlp"), "2L", "/data/text")
        );

        // 第二个数据集使用该标签
        Dataset dataset2 = new Dataset();
        dataset2.setId("dataset-text-002");
        dataset2.setName("问答数据集");

        nlpTag.setUsageCount(1L); // 模拟使用次数更新
        when(datasetMapper.findByName("问答数据集")).thenReturn(null);
        when(datasetMapper.findById(anyString())).thenReturn(dataset2);
        when(tagMapper.updateUsageCount(eq(nlpTag.getId()), eq(2L))).thenReturn(1);
        when(tagMapper.insertDatasetTag(anyString(), eq(nlpTag.getId()))).thenReturn(1);
        datasetService.createDataset(new CreateDatasetRequest(
            "问答数据集", "机器阅读理解", "TEXT",
            Arrays.asList("nlp"), "3L", "/data/qa"
        ));

        // 验证标签使用次数更新
        verify(tagMapper).updateUsageCount(eq(nlpTag.getId()), eq(1L));
        verify(tagMapper).updateUsageCount(eq(nlpTag.getId()), eq(2L));
    }

    @Test
    @DisplayName("数据集更新工作流: 创建 -> 更新标签 -> 更新状态")
    void datasetUpdateWorkflow() {
        // 创建初始数据集
        Dataset originalDataset = new Dataset();
        originalDataset.setId("dataset-update-001");
        originalDataset.setName("初始数据集");
        originalDataset.setDescription("初始描述");
        originalDataset.setStatus(StatusConstants.DatasetStatuses.DRAFT);

        Tag oldTag = new Tag();
        oldTag.setId("tag-old");
        oldTag.setName("old-tag");
        oldTag.setUsageCount(5L);

        Tag newTag = new Tag();
        newTag.setId("tag-new");
        newTag.setName("new-tag");
        newTag.setUsageCount(0L);

        when(datasetMapper.findByName("初始数据集")).thenReturn(null);
        when(datasetMapper.insert(any(Dataset.class))).thenAnswer(invocation -> {
            Dataset inserted = invocation.getArgument(0);
            // 模拟数据库插入后返回带ID的对象
            inserted.setId("dataset-update-001");
            return 1;
        });
        when(datasetMapper.findById(anyString())).thenReturn(originalDataset);
        when(tagMapper.findByName("old-tag")).thenReturn(oldTag);
        when(tagMapper.updateUsageCount(eq(oldTag.getId()), eq(6L))).thenReturn(1);
        when(tagMapper.insertDatasetTag(anyString(), eq(oldTag.getId()))).thenReturn(1);

        // 重置部分mock以准备更新操作
        reset(tagMapper);
        when(tagMapper.deleteDatasetTagsByDatasetId("dataset-update-001")).thenReturn(1);
        when(tagMapper.findByName("new-tag")).thenReturn(newTag);
        when(tagMapper.updateUsageCount(eq(newTag.getId()), eq(1L))).thenReturn(1);
        when(tagMapper.insertDatasetTag(eq("dataset-update-001"), eq(newTag.getId()))).thenReturn(1);

        // 更新数据集 - 更改标签和状态
        Dataset updatedDataset = new Dataset();
        updatedDataset.setId("dataset-update-001");
        updatedDataset.setName("更新后数据集");
        updatedDataset.setDescription("更新后描述");
        updatedDataset.setStatus(StatusConstants.DatasetStatuses.ACTIVE);

        when(datasetMapper.update(any(Dataset.class))).thenReturn(1);
        // 第二次调用findById时返回更新后的数据集
        when(datasetMapper.findById("dataset-update-001")).thenReturn(originalDataset, updatedDataset);

        Dataset updated = datasetService.updateDataset(
            "dataset-update-001", "更新后数据集", "更新后描述",
            Arrays.asList("new-tag"), StatusConstants.DatasetStatuses.ACTIVE
        );

        assertNotNull(updated);
        verify(tagMapper).deleteDatasetTagsByDatasetId("dataset-update-001");
        verify(tagMapper).updateUsageCount(eq(newTag.getId()), eq(1L));
        verify(datasetMapper).update(any(Dataset.class));
    }

    @Test
    @DisplayName("标签搜索工作流: 创建多个标签 -> 搜索验证")
    void tagSearchWorkflow() {
        // 创建多个标签
        List<Tag> allTags = Arrays.asList(
            createTestTag("tag-1", "machine-learning", "机器学习", 10L),
            createTestTag("tag-2", "deep-learning", "深度学习", 8L),
            createTestTag("tag-3", "computer-vision", "计算机视觉", 5L),
            createTestTag("tag-4", "natural-language", "自然语言处理", 3L)
        );

        List<Tag> searchResults = Arrays.asList(
            createTestTag("tag-1", "machine-learning", "机器学习", 10L),
            createTestTag("tag-2", "deep-learning", "深度学习", 8L)
        );

        // 搜索包含"learning"的标签
        when(tagMapper.findByKeyword("learning")).thenReturn(searchResults);
        List<Tag> found = tagService.searchTags("learning");

        assertEquals(2, found.size());
        assertTrue(found.stream().anyMatch(t -> t.getName().equals("machine-learning")));
        assertTrue(found.stream().anyMatch(t -> t.getName().equals("deep-learning")));

        // 获取所有标签
        when(tagMapper.findAllByOrderByUsageCountDesc()).thenReturn(allTags);
        List<Tag> all = tagService.getAllTags();

        assertEquals(4, all.size());
        verify(tagMapper).findByKeyword("learning");
        verify(tagMapper).findAllByOrderByUsageCountDesc();
    }

    @Test
    @DisplayName("数据集删除工作流: 删除数据集 -> 清理关联关系")
    void datasetDeletionWorkflow() {
        Dataset datasetToDelete = new Dataset();
        datasetToDelete.setId("dataset-delete-001");
        datasetToDelete.setName("待删除数据集");

        when(datasetMapper.findById("dataset-delete-001")).thenReturn(datasetToDelete);
        when(tagMapper.deleteDatasetTagsByDatasetId("dataset-delete-001")).thenReturn(2);
        when(datasetMapper.deleteById("dataset-delete-001")).thenReturn(1);

        assertDoesNotThrow(() -> datasetService.deleteDataset("dataset-delete-001"));

        verify(datasetMapper).findById("dataset-delete-001");
        verify(tagMapper).deleteDatasetTagsByDatasetId("dataset-delete-001");
        verify(datasetMapper).deleteById("dataset-delete-001");
    }

    @Test
    @DisplayName("错误处理工作流: 重复创建 -> 异常处理")
    void errorHandlingWorkflow() {
        // 标签重复创建
        Tag existingTag = new Tag();
        existingTag.setName("existing-tag");
        when(tagMapper.findByName("existing-tag")).thenReturn(existingTag);

        IllegalArgumentException tagException = assertThrows(IllegalArgumentException.class,
            () -> tagService.createTag("existing-tag", "#fff", "desc"));
        assertTrue(tagException.getMessage().contains("already exists"));

        // 数据集重复创建
        Dataset existingDataset = new Dataset();
        existingDataset.setName("existing-dataset");
        when(datasetMapper.findByName("existing-dataset")).thenReturn(existingDataset);

        IllegalArgumentException datasetException = assertThrows(IllegalArgumentException.class,
            () -> datasetService.createDataset(new CreateDatasetRequest("existing-dataset", "desc", "TEXT",
                null, "1L", "/path")));
        assertTrue(datasetException.getMessage().contains("already exists"));

        // 获取不存在的资源
        when(datasetMapper.findById("not-exist")).thenReturn(null);
        IllegalArgumentException notFoundException = assertThrows(IllegalArgumentException.class,
            () -> datasetService.getDataset("not-exist"));
        assertTrue(notFoundException.getMessage().contains("not found"));
    }

    private Tag createTestTag(String id, String name, String description, Long usageCount) {
        Tag tag = new Tag();
        tag.setId(id);
        tag.setName(name);
        tag.setDescription(description);
        tag.setUsageCount(usageCount);
        return tag;
    }
}
