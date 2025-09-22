package com.dataengine.operator.application;


import com.dataengine.operator.domain.modal.Category;
import com.dataengine.operator.domain.modal.RelationCategoryDTO;
import com.dataengine.operator.domain.repository.CategoryRelationRepository;
import com.dataengine.operator.domain.repository.CategoryRepository;
import com.dataengine.operator.interfaces.dto.CategoryTreeGet200ResponseInner;
import com.dataengine.operator.interfaces.dto.SubCategory;
import lombok.RequiredArgsConstructor;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Objects;
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
        List<RelationCategoryDTO> allRelations = convertToDTOList(categoryRelationRepository.findFullOuterJoinNative());
        return groupByParentIdSorted(allRelations, categories);
    }

    private List<RelationCategoryDTO> convertToDTOList(List<Object[]> results) {
        return results.stream()
            .map(this::convertToDTO)
            .filter(Objects::nonNull) // 过滤掉null值
            .collect(Collectors.toList());
    }

    private RelationCategoryDTO convertToDTO(Object[] row) {
        try {
            // 根据查询结果的列顺序解析数据
            Integer categoryId = row[0] != null ? ((Number) row[0]).intValue() : null;
            String operatorId = (String) row[1];
            String name = (String) row[2];
            Integer parentId = row[3] != null ? ((Number) row[3]).intValue() : null;

            return new RelationCategoryDTO(categoryId, operatorId, name, parentId);
        } catch (Exception e) {
            // 处理转换异常
            System.err.println("转换失败: " + Arrays.toString(row) + ", 错误: " + e.getMessage());
            return null;
        }
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
                    return category;
                }).collect(Collectors.toList()));
                return response;
            })
            .collect(Collectors.toList());
    }
}
