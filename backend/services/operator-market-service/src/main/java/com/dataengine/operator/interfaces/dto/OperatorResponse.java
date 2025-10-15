package com.dataengine.operator.interfaces.dto;

import lombok.Getter;
import lombok.Setter;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDateTime;
import java.util.List;

/**
 * OperatorResponse
 */

@Getter
@Setter
public class OperatorResponse {
  private String id;

  private String name;

  private String description;

  private String version;

  private String inputs;

  private String outputs;

  private List<Integer> categories;

  private String runtime;

  private String settings;

  private Boolean isStar;

  @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
  private LocalDateTime createdAt;

  @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
  private LocalDateTime updatedAt;
}

