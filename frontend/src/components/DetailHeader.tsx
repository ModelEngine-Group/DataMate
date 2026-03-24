import React, { useLayoutEffect, useEffect, useRef, useState, useCallback, useMemo } from "react";
import { Database } from "lucide-react";
import { Card, Button, Tag, Tooltip, Modal } from "antd";
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
  confirm?: {
    title: string;
    description?: string;
    cancelText?: string;
    okText?: string;
    okType?: "default" | "primary" | "danger";
    onConfirm?: () => void;
  };
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
  titleExtra?: React.ReactNode;
}

// 标签单行渲染组件
const TagsInline = ({ tags }: { tags: Array<{ id: number; name: string; color: string } | string> }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const tagsAreaRef = useRef<HTMLDivElement>(null);
  const [visibleTags, setVisibleTags] = useState<typeof tags>([]);
  const [hiddenCount, setHiddenCount] = useState(0);
  const [initialized, setInitialized] = useState(false);

  const calculateVisibleTags = useCallback(() => {
    if (!tags || tags.length === 0) {
      setVisibleTags([]);
      setHiddenCount(0);
      return;
    }

    if (!containerRef.current) return;

    // 创建测量容器
    const measureContainer = document.createElement("div");
    measureContainer.style.position = "absolute";
    measureContainer.style.visibility = "hidden";
    measureContainer.style.pointerEvents = "none";
    measureContainer.style.display = "inline-flex";
    measureContainer.style.alignItems = "center";
    measureContainer.style.gap = "4px";
    measureContainer.style.whiteSpace = "nowrap";
    measureContainer.style.zIndex = "-1";
    document.body.appendChild(measureContainer);

    // 测量 "+n" 标签
    const plusTag = document.createElement("span");
    plusTag.className = "ant-tag ant-tag-default";
    plusTag.textContent = "+99";
    measureContainer.appendChild(plusTag);
    const plusWidth = plusTag.offsetWidth;

    // 总容器宽度
    const totalWidth = 450;
    // 预留"+n"标签的完整空间（使用更保守的估计）
    // "+n"标签的实际宽度 ≈ 35-50px，预留 60px 确保安全
    const availableWidth = totalWidth - 60;

    // 先计算所有标签的总宽度
    let tagsTotalWidth = 0;
    tags.forEach((tag) => {
      const tagEl = document.createElement("span");
      tagEl.className = "ant-tag ant-tag-default";
      const tagName = typeof tag === "string" ? tag : tag.name;
      tagEl.textContent = tagName;
      measureContainer.appendChild(tagEl);
      tagsTotalWidth = measureContainer.offsetWidth;
    });

    // 如果所有标签都能放下，直接显示全部
    if (tagsTotalWidth <= availableWidth) {
      setVisibleTags(tags);
      setHiddenCount(0);
      if (measureContainer.parentNode) {
        measureContainer.parentNode.removeChild(measureContainer);
      }
      return;
    }

    // 如果放不下，需要计算可见标签数量
    while (measureContainer.firstChild) {
      measureContainer.removeChild(measureContainer.firstChild);
    }

    let visibleCount = 0;

    tags.forEach((tag, index) => {
      const tagEl = document.createElement("span");
      tagEl.className = "ant-tag ant-tag-default";
      const tagName = typeof tag === "string" ? tag : tag.name;
      tagEl.textContent = tagName;
      measureContainer.appendChild(tagEl);

      const currentWidth = measureContainer.offsetWidth;

      if (currentWidth <= availableWidth) {
        visibleCount++;
      } else {
        measureContainer.removeChild(tagEl);
        return false;
      }
      return true;
    });

    if (measureContainer.parentNode) {
      measureContainer.parentNode.removeChild(measureContainer);
    }

    setVisibleTags(tags.slice(0, visibleCount));
    setHiddenCount(tags.length - visibleCount);
  }, [tags]);

  useLayoutEffect(() => {
    calculateVisibleTags();
    setInitialized(true);
  }, [calculateVisibleTags]);

  useLayoutEffect(() => {
    const handleResize = () => calculateVisibleTags();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [calculateVisibleTags]);

  if (!tags || tags.length === 0) return null;

  const displayTags = initialized ? visibleTags : tags;

  // 获取隐藏的标签名称
  const hiddenTagNames = useMemo(() => {
    if (!tags || hiddenCount === 0) return [];
    const visibleSet = new Set(visibleTags.map(t => typeof t === 'string' ? t : t.name));
    return tags.filter(t => {
      const name = typeof t === 'string' ? t : t.name;
      return !visibleSet.has(name);
    }).map(t => typeof t === 'string' ? t : t.name);
  }, [tags, visibleTags, hiddenCount]);

  return (
    <div ref={containerRef} className="inline-flex items-center" style={{ whiteSpace: "nowrap", maxWidth: 450 }}>
      <div
        ref={tagsAreaRef}
        className="inline-flex items-center gap-1 flex-1"
        style={{ overflow: "hidden", minWidth: 0 }}
      >
        {displayTags.map((tag, index) => {
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
      </div>
      {initialized && hiddenCount > 0 && (
        <Popover
          content={
            <div className="max-w-xs">
              <div className="flex flex-wrap gap-1">
                {hiddenTagNames.map((name, i) => (
                  <Tag
                    key={i}
                    className="bg-gray-100 border-gray-300 text-gray-600"
                  >
                    {name}
                  </Tag>
                ))}
              </div>
            </div>
          }
          title="更多标签"
          trigger="hover"
          placement="topLeft"
        >
          <Tag className="cursor-pointer bg-gray-100 border-gray-300 text-gray-600 hover:bg-gray-200 shrink-0 ml-1">
            +{hiddenCount}
          </Tag>
        </Popover>
      )}
    </div>
  );
};

function DetailHeader<T>({
  data = {} as T,
  statistics,
  operations,
  tagConfig,
  titleExtra,
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
              {titleExtra}
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
              {statistics.map((stat: StatisticItem, index: number) => (
                <div key={stat.label || index} className="flex items-center gap-1 shrink-0">
                  {stat.icon}
                  <span>{stat.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {operations.map((op: OperationItem) => {
            if (op.isDropdown) {
              return (
                <ActionDropdown
                  key={op.key}
                  actions={op?.items}
                  onAction={op?.onMenuClick}
                />
              );
            }
            if (op.confirm) {
              const showConfirmModal = () => {
                Modal.confirm({
                  title: op.confirm?.title,
                  content: op.confirm?.description,
                  okText: op.confirm?.okText,
                  okType: op.danger ? "danger" : "primary",
                  cancelText: op.confirm?.cancelText,
                  centered: true,
                  onOk: () => {
                    if (op.onClick) {
                      op.onClick();
                    } else {
                      op?.confirm?.onConfirm?.();
                    }
                  },
                });
              };
              return (
                <Tooltip key={op.key} title={op.label}>
                  <Button
                    icon={op.icon}
                    danger={op.danger}
                    onClick={showConfirmModal}
                  />
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
