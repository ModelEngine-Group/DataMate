package com.dataengine.cleaning.interfaces.api;

import com.dataengine.cleaning.application.service.CleaningTemplateService;

import com.dataengine.cleaning.interfaces.dto.CleaningTemplate;
import com.dataengine.cleaning.interfaces.dto.CreateCleaningTemplateRequest;
import com.dataengine.cleaning.interfaces.dto.UpdateCleaningTemplateRequest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
public class CleaningTemplateController implements CleaningTemplateApi {

    @Autowired
    private CleaningTemplateService cleaningTemplateService;

    @Override
    public ResponseEntity<List<CleaningTemplate>> cleaningTemplatesGet() {
        return ResponseEntity.ok(cleaningTemplateService.getTemplates());
    }

    @Override
    public ResponseEntity<CleaningTemplate> cleaningTemplatesPost(CreateCleaningTemplateRequest request) {
        return ResponseEntity.ok(cleaningTemplateService.createTemplate(request));
    }

    @Override
    public ResponseEntity<CleaningTemplate> cleaningTemplatesTemplateIdGet(String templateId) {
        return ResponseEntity.ok(cleaningTemplateService.getTemplate(templateId));
    }

    @Override
    public ResponseEntity<CleaningTemplate> cleaningTemplatesTemplateIdPut(String templateId,
                                                                           UpdateCleaningTemplateRequest request) {
        return ResponseEntity.ok(cleaningTemplateService.updateTemplate(templateId, request));
    }

    @Override
    public ResponseEntity<Void> cleaningTemplatesTemplateIdDelete(String templateId) {
        cleaningTemplateService.deleteTemplate(templateId);
        return ResponseEntity.noContent().build();
    }
}
