package com.datamate.operator.application;

import com.datamate.operator.interfaces.dto.LabelDto;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Collections;

@Service
public class LabelService {
    public List<LabelDto> getLabels(Integer page, Integer size, String keyword) {
        // TODO: 查询标签列表
        return Collections.emptyList();
    }
    public void updateLabel(String id, List<LabelDto> updateLabelDtoRequest) {
        // TODO: 更新标签
    }
    public void createLabels(LabelDto labelsPostRequest) {
        // TODO: 批量创建标签
    }
}

