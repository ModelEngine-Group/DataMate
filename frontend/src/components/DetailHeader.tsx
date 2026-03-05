import React, { useEffect, useRef, useState } from "react";
import { Database } from "lucide-react";
import { Card, Button, Tag, Tooltip, Popconfirm } from "antd";
import type { ItemType } from "antd/es/menu/interface";
import AddTagPopover from "./AddTagPopover";
import ActionDropdown from "./ActionDropdown";

interface StatisticItem {
  icon: React.ReactNode;
  label: string;
  value: string | number;
}

interface OperationItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  isDropdown?: boolean;
  items?: ItemType[];
  onMenuClick?: (key: string) => void;
  onClick?: () => void;
  danger?: boolean;
}

interface TagConfig {
  showAdd: boolean;
  tags: Array<{ id: number; name: string; color: string } | string>;
  onFetchTags?: () => Promise<{
    data: { id: number; name: string; color: string }[];
  }>;
  onAddTag?: (tag: string) => void;
  onCreateAndTag?: (tagName: string) => void;
}
interface DetailHeaderProps<T> {
  data: T;
  statistics: StatisticItem[];
  operations: OperationItem[];
  tagConfig?: TagConfig;
}

// 标签单行渲染组件
const TagsInline = ({ tags }: { tags: Array<{ id: number; name: string; color: string } | string> }) => {
  const [visibleTags, setVisibleTags] = useState<any[]>([]);
  const [hiddenCount, setHiddenCount] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!tags || tags.length === 0) return;

    const calculateVisibleTags = () => {
      if (!containerRef.current) return;

      const container = containerRef.current;

      // 创建一个隐藏的测量容器
      const measureContainer = document.createElement("div");
      measureContainer.style.position = "absolute";
      measureContainer.style.visibility = "hidden";
      measureContainer.style.pointerEvents = "none";
      measureContainer.style.top = "0";
      measureContainer.style.left = "0";
      measureContainer.style.display = "inline-flex";
      measureContainer.style.alignItems = "center";
      measureContainer.style.gap = "4px";
      measureContainer.style.whiteSpace = "nowrap";
      measureContainer.style.flexWrap = "nowrap";
      measureContainer.style.zIndex = "-1";

      // 创建 "+n" 标签来测量
      const plusTag = document.createElement("span");
      plusTag.className = "ant-tag ant-tag-default cursor-pointer bg-gray-100 border-gray-300 text-gray-600 hover:bg-gray-200";
      plusTag.textContent = "+99";
      measureContainer.appendChild(plusTag);
      const plusWidth = plusTag.offsetWidth;

      // 暂时插入到 DOM 中测量
      if (container.parentElement) {
        container.parentElement.style.position = "relative";
        container.parentElement.appendChild(measureContainer);

        const containerWidth = container.offsetWidth;
        const availableWidth = containerWidth - 8; // 安全边距

        let visibleCount = 0;

        tags.forEach((tag, index) => {
          const tagEl = document.createElement("span");
          tagEl.className = "ant-tag ant-tag-default shrink-0";
          const tagName = typeof tag === "string" ? tag : tag.name;
          const tagColor = typeof tag === "string" ? undefined : tag.color;
          if (tagColor) tagEl.style.color = tagColor;
          tagEl.textContent = tagName;
          measureContainer.appendChild(tagEl);

          // 测量当前容器宽度
          const currentWidth = measureContainer.offsetWidth;
          const needsPlus = index < tags.length - 1;
          const targetWidth = availableWidth - (needsPlus ? plusWidth : 0);

          if (currentWidth <= targetWidth) {
            visibleCount++;
          } else {
            // 移除这个标签，因为它放不下
            measureContainer.removeChild(tagEl);
            return false; // 停止循环
          }

          return true;
        });

        // 移除测量容器
        container.parentElement.removeChild(measureContainer);

        setVisibleTags(tags.slice(0, visibleCount));
        setHiddenCount(tags.length - visibleCount);
      }
    };

    const timer = setTimeout(calculateVisibleTags, 0);
    const handleResize = () => calculateVisibleTags();

    window.addEventListener("resize", handleResize);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("resize", handleResize);
    };
  }, [tags]);

  if (!tags || tags.length === 0) return null;

  return (
    <div
      ref={containerRef}
      className="inline-flex items-center gap-1 overflow-hidden"
      style={{ whiteSpace: "nowrap", flexWrap: "nowrap" } }
    >
      {visibleTags.map((tag, index) => {
        const tagName = typeof tag === "string" ? tag : tag.name;
        const tagColor = typeof tag === "string" ? undefined : tag.color;
        return (
          <Tag
            key={`${typeof tag === "string" ? tag : tag.id}-${index}`}
            color={tagColor}
            className="shrink-0"
          >
            {tagName}
          </Tag>
        );
      })}
      {hiddenCount > 0 && (
        <Tooltip title={`还有 ${hiddenCount} 个标签`}>
          <Tag className="cursor-pointer bg-gray-100 border-gray-300 text-gray-600 hover:bg-gray-200 shrink-0">
            +{hiddenCount}
          </Tag>
        </Tooltip>
      )}
    </div>
  );
};

function DetailHeader<T>({
  data = {} as T,
  statistics,
  operations,
  tagConfig,
}: DetailHeaderProps<T>): React.ReactNode {
  return (
    <Card>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4 flex-1">
          <div
            className={`w-16 h-16 text-white rounded-lg flex items-center justify-center shadow-lg ${
              (data as any)?.iconColor
                ? ""
                : "bg-gradient-to-br from-sky-300 to-blue-500 text-white"
            }`}
            style={(data as any)?.iconColor ? { backgroundColor: (data as any).iconColor } : undefined}
          >
            {(data as any)?.icon ? (
              <div className="w-[2.8rem] h-[2.8rem] text-gray-50 flex items-center justify-center">{(data as any).icon}</div>
            ) : (
              <Database className="w-8 h-8 text-white" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-lg font-bold text-gray-900 truncate">{(data as any)?.name}</h1>
              {(data as any)?.status && (
                <Tag color={(data as any).status?.color} className="shrink-0">
                  <div className="flex items-center gap-2 text-xs">
                   {(data as any).status?.icon && <span>{(data as any).status?.icon}</span>}
                    <span>{(data as any).status?.label}</span>
                  </div>
                </Tag>
              )}
            </div>
            <div className="flex items-center gap-1 mb-2 overflow-hidden flex-nowrap">
              {(data as any)?.tags && (data as any)?.tags?.length > 0 && (
                <TagsInline tags={(data as any)?.tags || []} />
              )}
              {tagConfig?.showAdd && (
                <AddTagPopover
                  tags={tagConfig.tags}
                  onFetchTags={tagConfig.onFetchTags}
                  onAddTag={tagConfig.onAddTag}
                  onCreateAndTag={tagConfig.onCreateAndTag}
                />
              )}
            </div>
            <p className="text-gray-700 mb-4 line-clamp-2">{(data as any)?.description}</p>
            <div className="flex items-center gap-6 text-sm">
              {statistics.map((stat: any) => (
                <div key={stat.key} className="flex items-center gap-1 shrink-0">
                  {stat.icon}
                  <span>{stat.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {operations.map((op: any) => {
            if (op.isDropdown) {
              return (
                <ActionDropdown
                  actions={op?.items}
                  onAction={op?.onMenuClick}
                />
              );
            }
            if (op.confirm) {
              return (
                <Tooltip key={op.key} title={op.label}>
                  <Popconfirm
                    key={op.key}
                    {...op.confirm}
                    onConfirm={() => {
                      if (op.onClick) {
                        op.onClick()
                      } else {
                        op?.confirm?.onConfirm?.();
                      }
                    }}
                    okType={op.danger ? "danger" : "primary"}
                    overlayStyle={{ zIndex: 9999 }}
                  >
                    <Button icon={op.icon} danger={op.danger} />
                  </Popconfirm>
                </Tooltip>
              );
            }
            return (
              <Tooltip key={op.key} title={op.label}>
                <Button
                  icon={op.icon}
                  danger={op.danger}
                  onClick={op.onClick}
                />
              </Tooltip>
            );
          })}
        </div>
      </div>
    </Card>
  );
}

export default DetailHeader;
