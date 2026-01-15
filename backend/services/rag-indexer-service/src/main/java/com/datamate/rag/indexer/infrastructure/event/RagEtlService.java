package com.datamate.rag.indexer.infrastructure.event;

import com.datamate.common.setting.domain.entity.ModelConfig;
import com.datamate.common.setting.domain.repository.ModelConfigRepository;
import com.datamate.common.setting.infrastructure.client.ModelClient;
import com.datamate.datamanagement.domain.model.dataset.DatasetFile;
import com.datamate.datamanagement.infrastructure.persistence.repository.DatasetFileRepository;
import com.datamate.rag.indexer.domain.model.FileStatus;
import com.datamate.rag.indexer.domain.model.RagFile;
import com.datamate.rag.indexer.domain.repository.RagFileRepository;
import com.datamate.rag.indexer.infrastructure.client.GraphRagClient;
import com.datamate.rag.indexer.infrastructure.milvus.MilvusService;
import com.datamate.rag.indexer.interfaces.dto.AddFilesReq;
import com.datamate.rag.indexer.interfaces.dto.RagType;
import com.google.common.collect.Lists;
import dev.langchain4j.data.document.Document;
import dev.langchain4j.data.document.DocumentParser;
import dev.langchain4j.data.document.DocumentSplitter;
import dev.langchain4j.data.document.loader.FileSystemDocumentLoader;
import dev.langchain4j.data.document.parser.TextDocumentParser;
import dev.langchain4j.data.document.parser.apache.pdfbox.ApachePdfBoxDocumentParser;
import dev.langchain4j.data.document.parser.apache.poi.ApachePoiDocumentParser;
import dev.langchain4j.data.document.parser.apache.tika.ApacheTikaDocumentParser;
import dev.langchain4j.data.document.parser.markdown.MarkdownDocumentParser;
import dev.langchain4j.data.document.splitter.*;
import dev.langchain4j.data.document.transformer.jsoup.HtmlToTextDocumentTransformer;
import dev.langchain4j.data.embedding.Embedding;
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;

import java.util.Arrays;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;

/**
 * RAG ETL服务
 *
 * @author dallas
 * @since 2025-10-29
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RagEtlService {
    private static final Semaphore SEMAPHORE = new Semaphore(10);

    private final MilvusService milvusService;

    private final RagFileRepository ragFileRepository;

    private final DatasetFileRepository datasetFileRepository;

    private final ModelConfigRepository modelConfigRepository;

    private final GraphRagClient graphRagClient;

    private final ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();

    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void processAfterCommit(DataInsertedEvent event) {
        // 执行 RAG 处理流水线
        List<RagFile> ragFiles = ragFileRepository.findNotSuccessByKnowledgeBaseId(event.knowledgeBase().getId());
        if (RagType.GRAPH.equals(event.knowledgeBase().getType())){
            log.info("Knowledge base {} is of type GRAPH. Skipping RAG ETL processing.", event.knowledgeBase().getName());
            graphRagClient.startGraphRagTask(event.knowledgeBase().getId());
            return;
        }

        ragFiles.forEach(ragFile -> {
                    try {
                        SEMAPHORE.acquire();
                        executor.submit(() -> {
                            try {
                                // 执行 RAG 处理流水线
                                ragFile.setStatus(FileStatus.PROCESSING);
                                ragFileRepository.updateById(ragFile);
                                processRagFile(ragFile, event);
                                // 更新文件状态为已处理
                                ragFile.setStatus(FileStatus.PROCESSED);
                                ragFileRepository.updateById(ragFile);
                            } catch (Throwable e) {
                                // 处理异常
                                log.error("Error processing RAG file: {}", ragFile.getFileId(), e);
                                ragFile.setStatus(FileStatus.PROCESS_FAILED);
                                ragFile.setErrMsg(e.getMessage());
                                ragFileRepository.updateById(ragFile);
                            } finally {
                                SEMAPHORE.release();
                            }
                        });
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    }
                }
        );
    }

    private void processRagFile(RagFile ragFile, DataInsertedEvent event) {
        DatasetFile file = datasetFileRepository.getById(ragFile.getFileId());
        // 使用文档解析器解析文档
        DocumentParser parser = documentParser(file.getFileType());
        // 从文件系统读取文档
        Document document = FileSystemDocumentLoader.loadDocument(file.getFilePath(), parser);
        // 对html文档进行转换
        if (Arrays.asList("html", "htm").contains(file.getFileType().toLowerCase())) {
            document = new HtmlToTextDocumentTransformer().transform(document);
        }
        document.metadata().put("rag_file_id", ragFile.getId());
        document.metadata().put("original_file_id", ragFile.getFileId());
        // 使用文档分块器对文档进行分块
        DocumentSplitter splitter = documentSplitter(event.addFilesReq());
        List<TextSegment> split = splitter.split(document);

        // 更新分块数量
        ragFile.setChunkCount(split.size());
        ragFileRepository.updateById(ragFile);

        // 调用模型客户端获取嵌入模型
        ModelConfig model = modelConfigRepository.getById(event.knowledgeBase().getEmbeddingModel());
        EmbeddingModel embeddingModel = ModelClient.invokeEmbeddingModel(model);
        // 调用嵌入模型获取嵌入向量

        if (!milvusService.hasCollection(event.knowledgeBase().getName())) {
            milvusService.createCollection(event.knowledgeBase().getName(), embeddingModel.dimension());
        }

        Lists.partition(split, 20).forEach(partition -> {
            List<Embedding> embeddings = embeddingModel.embedAll(partition).content();
            milvusService.addAll(event.knowledgeBase().getName(),partition, embeddings);
        });
    }

    /**
     * 根据文件类型返回对应的文档解析器
     *x
     * @param fileType 文件类型
     * @return 文档解析器
     */
    public DocumentParser documentParser(String fileType) {
        fileType = fileType.toLowerCase();
        return switch (fileType) {
            case "txt", "html", "htm" -> new TextDocumentParser();
            case "md" -> new MarkdownDocumentParser();
            case "pdf" -> new ApachePdfBoxDocumentParser();
            case "doc", "docx", "xls", "xlsx", "ppt", "pptx" -> new ApachePoiDocumentParser();
            default -> new ApacheTikaDocumentParser();
        };
    }

    public DocumentSplitter documentSplitter(AddFilesReq req) {
        return switch (req.getProcessType()) {
            case PARAGRAPH_CHUNK -> new DocumentByParagraphSplitter(req.getChunkSize(), req.getOverlapSize());
            case SENTENCE_CHUNK -> new DocumentBySentenceSplitter(req.getChunkSize(), req.getOverlapSize());
            case LENGTH_CHUNK -> new DocumentByCharacterSplitter(req.getChunkSize(), req.getOverlapSize());
            case DEFAULT_CHUNK -> new DocumentByWordSplitter(req.getChunkSize(), req.getOverlapSize());
            case CUSTOM_SEPARATOR_CHUNK ->
                    new DocumentByRegexSplitter(req.getDelimiter(), "", req.getChunkSize(), req.getOverlapSize());
        };
    }
}