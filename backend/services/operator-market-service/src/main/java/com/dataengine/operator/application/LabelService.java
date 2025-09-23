package com.dataengine.operator.application;

import com.dataengine.operator.interfaces.dto.*;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Collections;

@Service
public class LabelService {
    public List<LabelResponse> getLabels(Integer page, Integer size, String keyword) {
        // TODO: 查询标签列表
        return Collections.emptyList();
    }
    public void updateLabel(String id, List<UpdateLabelRequest> updateLabelRequest) {
        // TODO: 更新标签
    }
    public Object createLabels(LabelsPostRequest labelsPostRequest) {
        // TODO: 批量创建标签
        return null;
    }
}

