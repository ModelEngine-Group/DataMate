package com.dataengine.datamanagement.application.service;

import com.dataengine.datamanagement.domain.model.dataset.Tag;
import com.dataengine.datamanagement.infrastructure.persistence.mapper.TagMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class TagApplicationServiceTest {

    @Mock
    private TagMapper tagMapper;

    @InjectMocks
    private TagApplicationService service;

    @BeforeEach
    void setUp() {
        service = new TagApplicationService(tagMapper);
    }

    @Test
    @DisplayName("createTag: 正常创建，插入并回查返回，带UUID且使用次数为0")
    void createTag_success() {
        when(tagMapper.findByName("alpha")).thenReturn(null);
        // insert 时，将传入的 Tag 保存下来，并让 findById 返回它
        when(tagMapper.insert(any(Tag.class))).thenAnswer(invocation -> {
            Tag inserted = invocation.getArgument(0);
            assertNotNull(inserted.getId(), "ID 应该在插入前生成");
            assertEquals(0L, inserted.getUsageCount());
            when(tagMapper.findById(inserted.getId())).thenReturn(inserted);
            return 1;
        });

        Tag result = service.createTag("alpha", "#ff0000", "desc");

        assertNotNull(result);
        assertNotNull(result.getId());
        assertEquals("alpha", result.getName());
        assertEquals("#ff0000", result.getColor());
        assertEquals("desc", result.getDescription());
        assertEquals(0L, result.getUsageCount());

        verify(tagMapper).findByName("alpha");
        // 校验 insert 被调用且参数合理
        ArgumentCaptor<Tag> captor = ArgumentCaptor.forClass(Tag.class);
        verify(tagMapper).insert(captor.capture());
        Tag toInsert = captor.getValue();
        assertNotNull(toInsert.getId());
        assertEquals(0L, toInsert.getUsageCount());
        verify(tagMapper).findById(toInsert.getId());
        verifyNoMoreInteractions(tagMapper);
    }

    @Test
    @DisplayName("createTag: 名称重复时抛异常，不进行插入")
    void createTag_duplicateName() {
        when(tagMapper.findByName("dup")).thenReturn(new Tag());

        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> service.createTag("dup", "#fff", "d"));
        assertTrue(ex.getMessage().contains("already exists"));
        verify(tagMapper).findByName("dup");
        verify(tagMapper, never()).insert(any());
        verify(tagMapper, never()).findById(anyString());
        verifyNoMoreInteractions(tagMapper);
    }

    @Test
    @DisplayName("getAllTags: 按使用次数倒序返回")
    void getAllTags() {
        List<Tag> mocked = Arrays.asList(new Tag(), new Tag());
        when(tagMapper.findAllByOrderByUsageCountDesc()).thenReturn(mocked);

        List<Tag> result = service.getAllTags();
        assertSame(mocked, result);
        verify(tagMapper).findAllByOrderByUsageCountDesc();
        verifyNoMoreInteractions(tagMapper);
    }

    @Test
    @DisplayName("searchTags: keyword 为空/空白时走 getAllTags")
    void searchTags_blankKeyword() {
        List<Tag> all = Collections.singletonList(new Tag());
        when(tagMapper.findAllByOrderByUsageCountDesc()).thenReturn(all);

        assertSame(all, service.searchTags(null));
        assertSame(all, service.searchTags("   "));

        verify(tagMapper, times(2)).findAllByOrderByUsageCountDesc();
        verify(tagMapper, never()).findByKeyword(anyString());
        verifyNoMoreInteractions(tagMapper);
    }

    @Test
    @DisplayName("searchTags: keyword 正常查询")
    void searchTags_withKeyword() {
        List<Tag> hits = Arrays.asList(new Tag(), new Tag());
        when(tagMapper.findByKeyword("alpha")).thenReturn(hits);

        List<Tag> result = service.searchTags(" alpha ");
        assertSame(hits, result);
        verify(tagMapper).findByKeyword("alpha");
        verifyNoMoreInteractions(tagMapper);
    }

    @Test
    @DisplayName("getTag: 存在则返回")
    void getTag_found() {
        Tag t = new Tag();
        t.setId("id-1");
        when(tagMapper.findById("id-1")).thenReturn(t);

        Tag result = service.getTag("id-1");
        assertSame(t, result);
        verify(tagMapper).findById("id-1");
        verifyNoMoreInteractions(tagMapper);
    }

    @Test
    @DisplayName("getTag: 不存在抛异常")
    void getTag_notFound() {
        when(tagMapper.findById("not-exist")).thenReturn(null);
        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> service.getTag("not-exist"));
        assertTrue(ex.getMessage().contains("Tag not found"));
        verify(tagMapper).findById("not-exist");
        verifyNoMoreInteractions(tagMapper);
    }

    @Test
    @DisplayName("getTagByName: 存在则返回，不存在抛异常")
    void getTagByName_cases() {
        Tag t = new Tag();
        t.setName("n1");
        when(tagMapper.findByName("n1")).thenReturn(t);
        when(tagMapper.findByName("none")).thenReturn(null);

        assertSame(t, service.getTagByName("n1"));

        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class,
                () -> service.getTagByName("none"));
        assertTrue(ex.getMessage().contains("Tag not found"));

        verify(tagMapper).findByName("n1");
        verify(tagMapper).findByName("none");
        verifyNoMoreInteractions(tagMapper);
    }
}
