package com.datamate.operator.application;


import com.datamate.operator.domain.repository.CategoryRelationRepository;
import com.datamate.operator.domain.repository.CategoryRepository;
import com.datamate.operator.interfaces.dto.CategoryDto;
import com.datamate.operator.interfaces.dto.CategoryRelationDto;
import com.datamate.operator.interfaces.dto.CategoryTreeResponse;
import lombok.RequiredArgsConstructor;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class CategoryService {


    private final CategoryRepository categoryRepo;

    private final CategoryRelationRepository categoryRelationRepo;

    public List<CategoryTreeResponse> getAllCategories() {
        List<CategoryDto> allCategories = categoryRepo.findAllCategories();
        List<CategoryRelationDto> allRelations = categoryRelationRepo.findAllRelation();

        Map<String, Integer> relationMap = allRelations.stream()
                .collect(Collectors.groupingBy(
                        CategoryRelationDto::getCategoryId,
                        Collectors.collectingAndThen(Collectors.counting(), Math::toIntExact)));

        Map<String, CategoryDto> nameMap = allCategories.stream()
                .collect(Collectors.toMap(CategoryDto::getId, Function.identity()));
        Map<String, List<CategoryDto>> groupedByParentId = allCategories.stream()
                .filter(relation -> !StringUtils.equals(relation.getParentId(), "0"))
                .collect(Collectors.groupingBy(CategoryDto::getParentId));

        return groupedByParentId.entrySet().stream()
                .sorted(categoryComparator(nameMap))
                .map(entry -> {
                    String parentId = entry.getKey();
                    List<CategoryDto> group = entry.getValue();
                    CategoryTreeResponse response = new CategoryTreeResponse();
                    response.setId(parentId);
                    response.setName(nameMap.get(parentId).getName());
                    AtomicInteger totalCount = new AtomicInteger();
                    response.setCategories(group.stream().peek(category -> {
                        category.setCount(relationMap.getOrDefault(category.getId(), 0));
                        totalCount.getAndAdd(relationMap.getOrDefault(category.getId(), 0));
                    }).sorted(Comparator.comparing(CategoryDto::getCreatedAt)).toList());
                    response.setCount(totalCount.get());
                    return response;
                }).collect(Collectors.toCollection(ArrayList::new));
    }

    private Comparator<Map.Entry<String, List<CategoryDto>>> categoryComparator(Map<String, CategoryDto> categoryMap) {
        return (entry1, entry2) -> {
            LocalDateTime index1 = categoryMap.get(entry1.getKey()).getCreatedAt();
            LocalDateTime index2 = categoryMap.get(entry2.getKey()).getCreatedAt();
            return index1.compareTo(index2);
        };
    }
}
