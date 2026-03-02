package com.datamate.rag.indexer.infrastructure.event;

import com.datamate.common.setting.domain.entity.ModelConfig;
import com.datamate.common.setting.domain.entity.ModelType;
import com.datamate.common.setting.domain.repository.ModelConfigRepository;
import com.datamate.common.setting.infrastructure.client.ModelClient;
import com.datamate.common.setting.infrastructure.client.MultimodalEmbeddingClient;
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
import java.util.Set;
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
    
    private static final Set<String> IMAGE_EXTENSIONS = Set.of(
            "jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "tiff", "tif"
    );

    private final MilvusService milvusService;

    private final RagFileRepository ragFileRepository;

    private final DatasetFileRepository datasetFileRepository;

    private final ModelConfigRepository modelConfigRepository;

    private final GraphRagClient graphRagClient;

    private final ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();

    @Async
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void processAfterCommit(DataInsertedEvent event) {
        List<RagFile> ragFiles = ragFileRepository.findNotSuccessByKnowledgeBaseId(event.knowledgeBase().getId());
        if (RagType.GRAPH.equals(event.knowledgeBase().getType())){
            log.info("Knowledge base {} is of type GRAPH. Skipping RAG ETL processing.", event.knowledgeBase().getName());
            graphRagClient.startGraphRagTask(event.knowledgeBase().getId(), event.knowledgeBase().getCreatedBy());
            return;
        }

        ragFiles.forEach(ragFile -> {
                    try {
                        SEMAPHORE.acquire();
                        executor.submit(() -> {
                            try {
                                ragFile.setStatus(FileStatus.PROCESSING);
                                ragFileRepository.updateById(ragFile);
                                processRagFile(ragFile, event);
                                ragFile.setStatus(FileStatus.PROCESSED);
                                ragFileRepository.updateById(ragFile);
                            } catch (Throwable e) {
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
        ModelConfig model = modelConfigRepository.getById(event.knowledgeBase().getEmbeddingModel());
        boolean isImageFile = isImageFile(file.getFileType());
        boolean isMultimodalModel = model.getType() == ModelType.MULTIMODAL_EMBEDDING;

        if (isImageFile && isMultimodalModel) {
            processImageFileWithMultimodal(ragFile, file, model, event);
        } else if (isImageFile) {
            log.warn("Image file {} cannot be processed with non-multimodal embedding model. Skipping.", file.getFileName());
            ragFile.setStatus(FileStatus.PROCESS_FAILED);
            ragFile.setErrMsg("图片文件需要多模态嵌入模型支持");
            ragFileRepository.updateById(ragFile);
        } else {
            processTextFile(ragFile, file, model, event);
        }
    }

    private void processImageFileWithMultimodal(RagFile ragFile, DatasetFile file, ModelConfig model, DataInsertedEvent event) {
        MultimodalEmbeddingClient client = new MultimodalEmbeddingClient(
                model.getBaseUrl(),
                model.getApiKey(),
                model.getModelName()
        );

        float[] embeddingVector = client.embedImage(file.getFilePath(), "");
        Embedding embedding = Embedding.from(embeddingVector);

        if (!milvusService.hasCollection(event.knowledgeBase().getName())) {
            milvusService.createCollection(event.knowledgeBase().getName(), embeddingVector.length);
        }

        TextSegment segment = TextSegment.from(
                "[图片文件: " + file.getFileName() + "]",
                new dev.langchain4j.data.document.Metadata()
                        .put("rag_file_id", ragFile.getId())
                        .put("original_file_id", ragFile.getFileId())
                        .put("dataset_id", file.getDatasetId())
                        .put("file_type", file.getFileType())
                        .put("is_image", "true")
                        .put("file_name", file.getFileName())
        );

        ragFile.setChunkCount(1);
        ragFileRepository.updateById(ragFile);

        milvusService.addAll(event.knowledgeBase().getName(), List.of(segment), List.of(embedding));
        log.info("Successfully processed image file {} with multimodal embedding", file.getFileName());
    }

    private void processTextFile(RagFile ragFile, DatasetFile file, ModelConfig model, DataInsertedEvent event) {
        DocumentParser parser = documentParser(file.getFileType());
        Document document = FileSystemDocumentLoader.loadDocument(file.getFilePath(), parser);
        if (Arrays.asList("html", "htm").contains(file.getFileType().toLowerCase())) {
            document = new HtmlToTextDocumentTransformer().transform(document);
        }
        document.metadata().put("rag_file_id", ragFile.getId());
        document.metadata().put("original_file_id", ragFile.getFileId());
        DocumentSplitter splitter = documentSplitter(event.addFilesReq());
        List<TextSegment> split = splitter.split(document);

        ragFile.setChunkCount(split.size());
        ragFileRepository.updateById(ragFile);

        EmbeddingModel embeddingModel = ModelClient.invokeEmbeddingModel(model);

        if (!milvusService.hasCollection(event.knowledgeBase().getName())) {
            milvusService.createCollection(event.knowledgeBase().getName(), embeddingModel.dimension());
        }

        Lists.partition(split, 20).forEach(partition -> {
            List<Embedding> embeddings = embeddingModel.embedAll(partition).content();
            milvusService.addAll(event.knowledgeBase().getName(), partition, embeddings);
        });
    }

    private boolean isImageFile(String fileType) {
        if (fileType == null) return false;
        return IMAGE_EXTENSIONS.contains(fileType.toLowerCase());
    }

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