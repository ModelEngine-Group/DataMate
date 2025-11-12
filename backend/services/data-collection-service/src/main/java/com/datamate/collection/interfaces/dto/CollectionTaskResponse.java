package com.datamate.collection.interfaces.dto;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

import com.datamate.collection.common.enums.TaskStatus;
import com.datamate.collection.common.enums.SyncMode;
import com.datamate.datamanagement.interfaces.dto.DatasetResponse;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.format.annotation.DateTimeFormat;
import jakarta.validation.Valid;

/**
 * CollectionTaskResponse
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class CollectionTaskResponse {

  private String id;

  private String name;

  private String description;

  private String targetPath;

  private Map<String, Object> config = new HashMap<>();

  private TaskStatus status;

  private SyncMode syncMode;

  private String scheduleExpression;

  private String lastExecutionId;

  @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
  private LocalDateTime createdAt;

  @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
  private LocalDateTime updatedAt;

  private DatasetResponse dataset;
}

