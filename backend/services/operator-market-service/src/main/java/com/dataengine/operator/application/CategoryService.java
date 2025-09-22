package com.dataengine.operator.application;


import com.dataengine.operator.domain.modal.Category;
import com.dataengine.operator.domain.modal.RelationCategoryDTO;
import com.dataengine.operator.domain.repository.CategoryRelationRepository;
import com.dataengine.operator.domain.repository.CategoryRepository;
import com.dataengine.operator.interfaces.dto.CategoryTreeGet200ResponseInner;
import com.dataengine.operator.interfaces.dto.SubCategory;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class CategoryService {
    private final CategoryRepository categoryRepository;

    private final CategoryRelationRepository categoryRelationRepository;

    public List<CategoryTreeGet200ResponseInner> getAllCategories() {
        List<Category> allCategories = categoryRepository.findAllCategories();
        Map<Integer, Category> categories = allCategories.stream().collect(Collectors.toMap(
            Category::getId,
            obj -> obj
        ));
        List<RelationCategoryDTO> allRelations = categoryRelationRepository.findAllRelationWithCategory();
        return groupByParentIdSorted(allRelations, categories);


    }

    public static List<CategoryTreeGet200ResponseInner> groupByParentIdSorted(List<RelationCategoryDTO> relations,
                                                                              Map<Integer, Category> categories) {
        Map<Integer, List<RelationCategoryDTO>> groupedByParentId = relations.stream()
            .filter(relation -> relation.getParentId() > 0)
            .collect(Collectors.groupingBy(RelationCategoryDTO::getParentId));

        return groupedByParentId.entrySet().stream()
            .sorted(Map.Entry.comparingByKey())
            .map(entry -> {
                Integer parentId = entry.getKey();
                List<RelationCategoryDTO> group = entry.getValue();
                Map<Integer, List<RelationCategoryDTO>> collect = group.stream().collect(
                    Collectors.groupingBy(RelationCategoryDTO::getCategoryId));

                CategoryTreeGet200ResponseInner response = new CategoryTreeGet200ResponseInner();
                response.setId(parentId);
                response.setNumber(group.size());
                response.setName(categories.get(parentId).getName());
                response.setCategories(collect.entrySet().stream().map(relation -> {
                    List<RelationCategoryDTO> value = relation.getValue();
                    SubCategory category = new SubCategory();
                    category.setId(relation.getKey());
                    category.setName(value.get(0).getName());
                    category.setNumber(value.size());
                    return category;
                }).collect(Collectors.toList()));
                return response;
            })
            .collect(Collectors.toList());
    }
}
