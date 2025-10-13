import React, { useState } from "react";
import "./DragDrop.css";

const PreciseDragDrop = () => {
  // 初始数据
  const [leftItems, setLeftItems] = useState([
    {
      id: 1,
      title: "需求分析",
      type: "analysis",
      color: "#4CAF50",
      priority: "high",
    },
    {
      id: 2,
      title: "UI设计",
      type: "design",
      color: "#2196F3",
      priority: "medium",
    },
    {
      id: 3,
      title: "前端开发",
      type: "development",
      color: "#FF9800",
      priority: "high",
    },
    {
      id: 4,
      title: "后端开发",
      type: "development",
      color: "#9C27B0",
      priority: "high",
    },
    {
      id: 5,
      title: "功能测试",
      type: "testing",
      color: "#3F51B5",
      priority: "medium",
    },
    {
      id: 6,
      title: "部署上线",
      type: "deployment",
      color: "#009688",
      priority: "low",
    },
  ]);

  const [rightItems, setRightItems] = useState([
    {
      id: 7,
      title: "项目启动",
      type: "planning",
      color: "#E91E63",
      priority: "high",
    },
  ]);

  const [draggingItem, setDraggingItem] = useState(null);
  const [insertPosition, setInsertPosition] = useState(null); // 'above' 或 'below'

  // 处理拖拽开始
  const handleDragStart = (e, item, source) => {
    setDraggingItem({ ...item, source });
    e.dataTransfer.effectAllowed = "move";

    setTimeout(() => {
      e.target.classList.add("dragging");
    }, 0);
  };

  // 处理拖拽结束
  const handleDragEnd = (e) => {
    setDraggingItem(null);
    setInsertPosition(null);
    e.target.classList.remove("dragging");
  };

  // 处理容器拖拽经过
  const handleContainerDragOver = (e) => {
    e.preventDefault();
  };

  // 处理容器拖拽离开
  const handleContainerDragLeave = (e) => {
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setInsertPosition(null);
    }
  };

  // 处理项目拖拽经过（用于精确插入）
  const handleItemDragOver = (e, itemId) => {
    e.preventDefault();
    e.stopPropagation();

    const rect = e.currentTarget.getBoundingClientRect();
    const mouseY = e.clientY;
    const elementMiddle = rect.top + rect.height;

    // 判断鼠标在元素的上半部分还是下半部分
    const newPosition = mouseY < elementMiddle ? "above" : "below";

    setInsertPosition(newPosition);
  };

  // 处理项目拖拽离开
  const handleItemDragLeave = (e) => {
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setInsertPosition(null);
    }
  };

  // 处理放置到右侧容器空白区域
  const handleDropToRightContainer = (e) => {
    e.preventDefault();

    if (!draggingItem) return;

    // 如果是从左侧拖拽过来的
    if (draggingItem.source === "left") {
      // 检查是否已存在
      const exists = rightItems.some((item) => item.id === draggingItem.id);
      if (!exists) {
        setRightItems((prev) => [
          ...prev,
          {
            ...draggingItem,
            source: "right",
          },
        ]);

        setLeftItems((prev) =>
          prev.filter((item) => item.id !== draggingItem.id)
        );
      }
    }

    resetDragState();
  };

  // 处理放置到右侧容器的特定位置
  const handleDropToRightItem = (e, targetItemId) => {
    e.preventDefault();
    e.stopPropagation();

    if (!draggingItem) return;

    // 从左侧拖拽到右侧的精确插入
    if (draggingItem.source === "left") {
      const targetIndex = rightItems.findIndex(
        (item) => item.id === targetItemId
      );

      if (targetIndex !== -1) {
        const insertIndex =
          insertPosition === "above" ? targetIndex : targetIndex + 1;

        // 检查是否已存在
        const exists = rightItems.some((item) => item.id === draggingItem.id);
        if (!exists) {
          const newRightItems = [...rightItems];
          newRightItems.splice(insertIndex, 0, {
            ...draggingItem,
            source: "right",
          });

          setRightItems(newRightItems);
          setLeftItems((prev) =>
            prev.filter((item) => item.id !== draggingItem.id)
          );
        }
      }
    }
    // 右侧容器内的重新排序
    else if (draggingItem.source === "right") {
      const draggedIndex = rightItems.findIndex(
        (item) => item.id === draggingItem.id
      );
      const targetIndex = rightItems.findIndex(
        (item) => item.id === targetItemId
      );

      if (
        draggedIndex !== -1 &&
        targetIndex !== -1 &&
        draggedIndex !== targetIndex
      ) {
        const newItems = [...rightItems];
        const [draggedItem] = newItems.splice(draggedIndex, 1);

        // 计算正确的插入位置
        let insertIndex =
          insertPosition === "above" ? targetIndex : targetIndex + 1;
        if (draggedIndex < insertIndex) {
          insertIndex--; // 调整插入位置，因为已经移除了原元素
        }

        newItems.splice(insertIndex, 0, draggedItem);
        setRightItems(newItems);
      }
    }

    resetDragState();
  };

  // 处理拖拽回左侧容器
  const handleDropToLeft = (e) => {
    e.preventDefault();

    if (!draggingItem || draggingItem.source !== "right") return;

    setRightItems((prev) => prev.filter((item) => item.id !== draggingItem.id));
    setLeftItems((prev) => [
      ...prev,
      {
        ...draggingItem,
        source: "left",
      },
    ]);

    resetDragState();
  };

  // 重置拖拽状态
  const resetDragState = () => {
    setDraggingItem(null);
    setInsertPosition(null);
  };

  // 清空右侧容器
  const clearRightContainer = () => {
    setLeftItems((prev) => [
      ...prev,
      ...rightItems.map((item) => ({
        ...item,
        source: "left",
      })),
    ]);
    setRightItems([]);
  };

  // 获取类型图标
  const getTypeIcon = (type) => {
    switch (type) {
      case "analysis":
        return "📊";
      case "design":
        return "🎨";
      case "development":
        return "💻";
      case "testing":
        return "🧪";
      case "deployment":
        return "🚀";
      case "planning":
        return "📋";
      default:
        return "📌";
    }
  };

  // 获取优先级标签
  const getPriorityLabel = (priority) => {
    switch (priority) {
      case "high":
        return { label: "高优先级", class: "priority-high" };
      case "medium":
        return { label: "中优先级", class: "priority-medium" };
      case "low":
        return { label: "低优先级", class: "priority-low" };
      default:
        return { label: "普通", class: "priority-medium" };
    }
  };

  return (
    <div className="precise-drag-drop">
      <div className="header">
        <h1>精确位置拖拽排序</h1>
        <p>拖拽时悬停在项目上方或下方可选择精确插入位置</p>
      </div>

      <div className="containers">
        {/* 左侧容器 - 待办事项 */}
        <div
          className={`container left-container `}
          onDragOver={(e) => handleContainerDragOver(e, "left")}
          onDragLeave={handleContainerDragLeave}
          onDrop={handleDropToLeft}
        >
          <div className="container-header">
            <h2>📋 待办事项</h2>
            <span className="count">{leftItems.length} 项</span>
          </div>
          <div className="items-list">
            {leftItems.map((item) => (
              <div
                key={item.id}
                className="item"
                draggable
                onDragStart={(e) => handleDragStart(e, item, "left")}
                onDragEnd={handleDragEnd}
                style={{ "--item-color": item.color }}
              >
                <div className="item-content">
                  <span className="item-icon">{getTypeIcon(item.type)}</span>
                  <div className="item-info">
                    <span className="item-title">{item.title}</span>
                    <span
                      className={`priority-tag ${
                        getPriorityLabel(item.priority).class
                      }`}
                    >
                      {getPriorityLabel(item.priority).label}
                    </span>
                  </div>
                </div>
                <div className="item-type">{item.type}</div>
              </div>
            ))}
            {leftItems.length === 0 && (
              <div className="empty-state">
                <p>🎉 所有任务已完成！</p>
                <span>从右侧拖拽项目回来重新安排</span>
              </div>
            )}
          </div>
        </div>

        {/* 右侧容器 - 进行中的任务 */}
        <div
          className={`container right-container`}
          onDragOver={(e) => handleContainerDragOver(e, "right")}
          onDragLeave={handleContainerDragLeave}
          onDrop={handleDropToRightContainer}
        >
          <div className="container-header">
            <h2>🚀 进行中的任务</h2>
            <div className="header-actions">
              <span className="count">{rightItems.length} 项</span>
              {rightItems.length > 0 && (
                <button className="clear-btn" onClick={clearRightContainer}>
                  清空所有
                </button>
              )}
            </div>
          </div>
          <div className="items-list">
            {rightItems.length === 0 ? (
              <div className="empty-state">
                <p>📥 暂无进行中的任务</p>
                <span>从左侧拖拽项目过来开始工作</span>
              </div>
            ) : (
              rightItems.map((item, index) => (
                <div
                  key={item.id}
                  className={`item `}
                  draggable
                  onDragStart={(e) => handleDragStart(e, item, "right")}
                  onDragEnd={handleDragEnd}
                  onDragOver={(e) => handleItemDragOver(e, item.id)}
                  onDragLeave={handleItemDragLeave}
                  onDrop={(e) => handleDropToRightItem(e, item.id)}
                  style={{ "--item-color": item.color }}
                >
                  <div className="item-content">
                    <span className="item-index">{index + 1}</span>
                    <span className="item-icon">{getTypeIcon(item.type)}</span>
                    <div className="item-info">
                      <span className="item-title">{item.title}</span>
                      <span
                        className={`priority-tag ${
                          getPriorityLabel(item.priority).class
                        }`}
                      >
                        {getPriorityLabel(item.priority).label}
                      </span>
                    </div>
                  </div>
                  <div className="item-actions">
                    <span className="drag-handle">⋮⋮</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="instructions">
        <h3>🎯 操作指南</h3>
        <div className="instruction-grid">
          <div className="instruction">
            <span className="icon">🎯</span>
            <div>
              <strong>精确插入</strong>
              <p>拖拽时悬停在项目上方或下方选择插入位置</p>
            </div>
          </div>
          <div className="instruction">
            <span className="icon">🔄</span>
            <div>
              <strong>重新排序</strong>
              <p>在右侧容器内拖拽调整任务顺序</p>
            </div>
          </div>
          <div className="instruction">
            <span className="icon">📤</span>
            <div>
              <strong>移回待办</strong>
              <p>从右侧拖拽任务回左侧容器</p>
            </div>
          </div>
          <div className="instruction">
            <span className="icon">🧹</span>
            <div>
              <strong>批量操作</strong>
              <p>使用"清空所有"按钮快速重置</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PreciseDragDrop;
