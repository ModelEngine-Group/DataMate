package com.datamate.operator.interfaces.dto;

import lombok.Getter;
import lombok.Setter;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDateTime;
import java.util.List;

/**
 * OperatorDto
 */

@Getter
@Setter
public class OperatorDto {
  private String id;

  private String name;

  private String description;

  private String version;

  private String inputs;

  private String outputs;

  private List<Integer> categories;

  private String runtime;

  private String settings;

  private String fileName;

  private Boolean isStar;

  @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
  private LocalDateTime createdAt;

  @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
  private LocalDateTime updatedAt;
}

