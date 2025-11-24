package com.datamate.datamanagement.domain.model.dataset;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.apache.commons.lang3.StringUtils;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
public class FileTag {
    private Map<String, Object> values;

    private String type;

    private String id;

    private String fromName;

    public List<String> getTags() {
        List<String> tags = new ArrayList<>();
        Object tagValues = values.get(type);
        if (tagValues instanceof List) {
            for (Object tag : (List<?>) tagValues) {
                if (tag instanceof String) {
                    tags.add((String) tag);
                }
            }
        } else if (tagValues instanceof String) {
            tags.add((String) tagValues);
        }
        if(StringUtils.isNotEmpty(fromName)) {
            return tags.stream().map(tag -> fromName + " " + tag).toList();
        }
        return tags;
    }
}
