package com.datamate.rag.indexer.interfaces;

import com.datamate.common.interfaces.PagedResponse;
import com.datamate.common.interfaces.PagingQuery;
import com.datamate.rag.indexer.application.KnowledgeBaseService;
import com.datamate.rag.indexer.domain.model.RagChunk;
import com.datamate.rag.indexer.domain.model.RagFile;
import com.datamate.rag.indexer.interfaces.dto.*;
import io.milvus.v2.service.vector.response.SearchResp;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;


/**
 * 知识库控制器
 *
 * @author dallas
 * @since 2025-09-30
 */
@RestController
@RequiredArgsConstructor
@RequestMapping("/knowledge-base")
public class KnowledgeBaseController {
    private final KnowledgeBaseService knowledgeBaseService;

    /**
     * 创建知识库
     *
     * @param request 知识库创建请求
     * @return 知识库 ID
     */
    @PostMapping("/create")
    public String create(@RequestBody @Valid KnowledgeBaseCreateReq request) {
        return knowledgeBaseService.create(request);
    }

    /**
     * 更新知识库
     *
     * @param knowledgeBaseId 知识库 ID
     * @param request         知识库更新请求
     */
    @PutMapping("/{knowledgeBaseId}")
    public void update(@PathVariable("knowledgeBaseId") String knowledgeBaseId,
                       @RequestBody @Valid KnowledgeBaseUpdateReq request) {
        knowledgeBaseService.update(knowledgeBaseId, request);
    }

    /**
     * 删除知识库
     *
     * @param knowledgeBaseId 知识库 ID
     */
    @DeleteMapping("/{knowledgeBaseId}")
    public void delete(@PathVariable("knowledgeBaseId") String knowledgeBaseId) {
        knowledgeBaseService.delete(knowledgeBaseId);
    }

    /**
     * 获取知识库
     *
     * @param knowledgeBaseId 知识库 ID
     * @return 知识库
     */
    @GetMapping("/{knowledgeBaseId}")
    public KnowledgeBaseResp get(@PathVariable("knowledgeBaseId") String knowledgeBaseId) {
        return knowledgeBaseService.getById(knowledgeBaseId);
    }

    /**
     * 获取知识库列表
     *
     * @return 知识库列表
     */
    @PostMapping("/list")
    public PagedResponse<KnowledgeBaseResp> list(@RequestBody @Valid KnowledgeBaseQueryReq request) {
        return knowledgeBaseService.list(request);
    }

    /**
     * 添加文件到知识库
     *
     * @param knowledgeBaseId 知识库 ID
     * @param request         添加文件请求
     */
    @PostMapping("/{knowledgeBaseId}/files")
    public void addFiles(@PathVariable("knowledgeBaseId") String knowledgeBaseId,
                         @RequestBody @Valid AddFilesReq request) {
        request.setKnowledgeBaseId(knowledgeBaseId);
        knowledgeBaseService.addFiles(request);
    }

    /**
     * 获取知识库文件列表
     *
     * @param knowledgeBaseId 知识库 ID
     * @return 知识库文件列表
     */
    @GetMapping("/{knowledgeBaseId}/files")
    public PagedResponse<RagFile> listFiles(@PathVariable("knowledgeBaseId") String knowledgeBaseId,
                                            RagFileReq request) {
        return knowledgeBaseService.listFiles(knowledgeBaseId, request);
    }

    /**
     * 删除知识库文件
     *
     * @param knowledgeBaseId 知识库 ID
     * @param request         删除文件请求
     */
    @DeleteMapping("/{knowledgeBaseId}/files")
    public void deleteFile(@PathVariable("knowledgeBaseId") String knowledgeBaseId,
                           @RequestBody DeleteFilesReq request) {
        knowledgeBaseService.deleteFiles(knowledgeBaseId, request);
    }

    /**
     * 知识库文件详情
     *
     * @param knowledgeBaseId 知识库 ID
     * @param ragFileId       文件 ID
     * @return 文件详情
     */
    @GetMapping("/{knowledgeBaseId}/files/{ragFileId}")
    public PagedResponse<RagChunk> getChunks(@PathVariable("knowledgeBaseId") String knowledgeBaseId,
                                                  @PathVariable("ragFileId") String ragFileId,
                                                  PagingQuery pagingQuery) {
        return knowledgeBaseService.getChunks(knowledgeBaseId, ragFileId, pagingQuery);
    }

    /**
     * 检索知识库内容
     *
     * @param request 检索请求
     * @return 检索结果
     */
    @PostMapping("/retrieve")
    public SearchResp retrieve(@RequestBody @Valid RetrieveReq request) {
        return knowledgeBaseService.retrieve(request);
    }
}