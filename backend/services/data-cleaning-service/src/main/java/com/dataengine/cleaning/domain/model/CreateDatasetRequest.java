package com.dataengine.cleaning.domain.model;

import jakarta.validation.Valid;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;


@Getter
@Setter
@NoArgsConstructor
public class CreateDatasetRequest {

    private String name;

    private String description;

    private String type;

    @Valid
    private List<String> tags;

    private String dataSource;
}
