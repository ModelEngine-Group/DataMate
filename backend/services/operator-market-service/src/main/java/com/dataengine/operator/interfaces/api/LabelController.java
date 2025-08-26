package com.dataengine.operator.interfaces.api;

import com.dataengine.operator.interfaces.dto.*;
import com.dataengine.operator.application.LabelService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RestController;
import java.util.List;

@RestController
public class LabelController implements LabelApi {
    @Autowired
    private LabelService labelService;

    @Override
    public ResponseEntity<List<LabelResponse>> labelsGet(Integer page, Integer size, String keyword) {
        return ResponseEntity.ok(labelService.getLabels(page, size, keyword));
    }

    @Override
    public ResponseEntity<Void> labelsIdPut(String id, List<UpdateLabelRequest> updateLabelRequest) {
        labelService.updateLabel(id, updateLabelRequest);
        return ResponseEntity.ok().build();
    }

    @Override
    public ResponseEntity<Void> labelsPost(LabelsPostRequest labelsPostRequest) {
        labelService.createLabels(labelsPostRequest);
        return ResponseEntity.ok().build();
    }
}


