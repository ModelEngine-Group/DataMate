import React, { useState } from "react";
import { OperatorI } from "../../cleansing.model";

export function useDragOperators({
  operators,
  setOperators,
}: {
  operators: OperatorI[];
  setOperators: (operators: OperatorI[]) => void;
}) {
  const [draggingItem, setDraggingItem] = useState<OperatorI | null>(null);
  const [draggingSource, setDraggingSource] = useState<
    "library" | "sort" | null
  >(null);
  const [insertPosition, setInsertPosition] = useState<
    "above" | "below" | null
  >(null);

  // 处理拖拽开始
  const handleDragStart = (
    e: React.DragEvent,
    item: OperatorI,
    source: "library" | "sort"
  ) => {
    setDraggingItem({
      ...item,
      originalId: item.id,
    });
    setDraggingSource(source);
    e.dataTransfer.effectAllowed = "move";
  };

  // 处理拖拽结束
  const handleDragEnd = () => {
    setDraggingItem(null);
    setInsertPosition(null);
  };

  // 处理容器拖拽经过
  const handleContainerDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  // 处理容器拖拽离开
  const handleContainerDragLeave = (e: React.DragEvent) => {
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setInsertPosition(null);
    }
  };

  // 处理项目拖拽经过
  const handleItemDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const rect = e.currentTarget.getBoundingClientRect();
    const mouseY = e.clientY;
    const elementMiddle = rect.top + rect.height / 2;

    // 判断鼠标在元素的上半部分还是下半部分
    const newPosition = mouseY < elementMiddle ? "above" : "below";

    setInsertPosition(newPosition);
  };

  // 处理项目拖拽离开
  const handleItemDragLeave = (e: React.DragEvent) => {
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setInsertPosition(null);
    }
  };

  // 处理放置到空白区域
  const handleDropToContainer = (e: React.DragEvent) => {
    e.preventDefault();

    if (!draggingItem) return;

    // 如果是从算子库拖拽过来的
    if (draggingSource === "library") {
      // 检查是否已存在
      const exists = operators.some((item) => item.id === draggingItem.id);
      if (!exists) {
        setOperators([...operators, draggingItem]);
      }
    }

    resetDragState();
  };

  // 处理放置到特定位置
  const handleItemDrop = (e: React.DragEvent, targetIndex: number) => {
    e.preventDefault();
    e.stopPropagation();

    if (!draggingItem) return;

    // 从左侧拖拽到右侧的精确插入
    if (draggingSource === "library") {
      if (targetIndex !== -1) {
        const insertIndex =
          insertPosition === "above" ? targetIndex : targetIndex + 1;

        // 检查是否已存在
        const exists = operators.some((item) => item.id === draggingItem.id);
        if (!exists) {
          const newRightItems = [...operators];
          newRightItems.splice(insertIndex, 0, draggingItem);

          setOperators(newRightItems);
        }
      }
    }
    // 右侧容器内的重新排序
    else if (draggingSource === "sort") {
      const draggedIndex = operators.findIndex(
        (item) => item.id === draggingItem.id
      );
      if (
        draggedIndex !== -1 &&
        targetIndex !== -1 &&
        draggedIndex !== targetIndex
      ) {
        const newItems = [...operators];
        const [draggedItem] = newItems.splice(draggedIndex, 1);

        // 计算正确的插入位置
        let insertIndex =
          insertPosition === "above" ? targetIndex : targetIndex + 1;
        if (draggedIndex < insertIndex) {
          insertIndex--; // 调整插入位置，因为已经移除了原元素
        }

        newItems.splice(insertIndex, 0, draggedItem);
        setOperators(newItems);
      }
    }

    resetDragState();
  };

  // 重置拖拽状态
  const resetDragState = () => {
    setDraggingItem(null);
    setInsertPosition(null);
  };

  return {
    handleDragStart,
    handleDragEnd,
    handleContainerDragOver,
    handleContainerDragLeave,
    handleItemDragOver,
    handleItemDragLeave,
    handleItemDrop,
    handleDropToContainer,
  };
}
