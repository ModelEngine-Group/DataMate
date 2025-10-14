package com.dataengine.operator.application;


import com.dataengine.operator.domain.modal.Category;
import com.dataengine.operator.domain.modal.RelationCategoryDTO;
import com.dataengine.operator.infrastructure.persistence.mapper.CategoryMapper;
import com.dataengine.operator.infrastructure.persistence.mapper.CategoryRelationMapper;
import com.dataengine.operator.interfaces.dto.CategoryTreeGet200ResponseInner;
import com.dataengine.operator.interfaces.dto.SubCategory;
import lombok.RequiredArgsConstructor;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class CategoryService {
    private final CategoryMapper categoryMapper;

    private final CategoryRelationMapper categoryRelationMapper;

    public List<CategoryTreeGet200ResponseInner> getAllCategories() {
        List<Category> allCategories = categoryMapper.findAllCategories();
        Map<Integer, Category> categories = allCategories.stream().collect(Collectors.toMap(
            Category::getId,
            obj -> obj
        ));
        List<RelationCategoryDTO> allRelations = categoryRelationMapper.findFullOuterJoinNative();
        return groupByParentIdSorted(allRelations, categories);
    }

    private List<CategoryTreeGet200ResponseInner> groupByParentIdSorted(List<RelationCategoryDTO> relations,
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
                response.setCount(group.size());
                response.setName(categories.get(parentId).getName());
                response.setCategories(collect.entrySet().stream().map(relation -> {
                    List<RelationCategoryDTO> value = relation.getValue();
                    SubCategory category = new SubCategory();
                    category.setId(relation.getKey());
                    category.setName(value.get(0).getName());
                    category.setCount((int) value.stream()
                        .filter(dto -> StringUtils.isNotEmpty(dto.getOperatorId()))
                        .count());
                    category.setParentId(parentId);
                    return category;
                }).collect(Collectors.toList()));
                return response;
            })
            .collect(Collectors.toList());
    }
}
