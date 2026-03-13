import React, { useState, useEffect, useRef } from "react";
import { Tag, Pagination, Tooltip, Empty, Popover, Spin } from "antd";
import { ClockCircleOutlined, StarFilled, StarOutlined } from "@ant-design/icons";
import type { ItemType } from "antd/es/menu/interface";
import { formatDateTime } from "@/utils/unit";
import ActionDropdown from "./ActionDropdown";
import { Database } from "lucide-react";

interface BadgeItem {
  name: string;
  label: string;
  color?: string;
  background?: string;
}

interface BaseCardDataType {
  id: string | number;
  name: string;
  type: string;
  icon?: React.JSX.Element;
  iconColor?: string;
  status: {
    label: string;
    icon?: React.JSX.Element;
    color?: string;
  } | null;
  description: string;
  tags?: Array<string | BadgeItem>;
  statistics?: { label: string; value: string | number }[];
  updatedAt?: string;
}

interface CardViewProps<T> {
  data: T[];
  pagination: {
    [key: string]: any;
    current: number;
    pageSize: number;
    total: number;
  };
  operations:
    | {
        key: string;
        label: string;
        danger?: boolean;
        disabled?: boolean;
        icon?: React.JSX.Element;
        confirm?: {
          title: string;
          description?: string;
          okText?: string;
          cancelText?: string;
          okType?: "default" | "primary" | "danger";
        };
        onClick?: (item: T) => void;
      }[]
    | ((item: T) => ItemType[]);
  loading?: boolean;
  onView?: (item: T) => void;
  onFavorite?: (item: T) => void;
  isFavorite?: (item: T) => boolean;
}

// 标签渲染组件
const TagsRenderer = ({ tags }: { tags?: Array<string | BadgeItem> }) => {
  const [visibleTags, setVisibleTags] = useState<any[]>(tags || []);
  const [hiddenTags, setHiddenTags] = useState<any[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const isInitializedRef = useRef(false);
  const prevTagsRef = useRef<typeof tags>();

  useEffect(() => {
    if (!tags || tags.length === 0) {
      setVisibleTags([]);
      setHiddenTags([]);
      return;
    }

    const calculateVisibleTags = () => {
      if (!containerRef.current) return;

      const container = containerRef.current;
      const containerRect = container.getBoundingClientRect();

      // 获取所有标签元素
      const tagElements = Array.from(container.querySelectorAll(':scope > .ant-tag'));
      const plusTagElement = tagElements.find(el => el.textContent?.startsWith('+'));
      const regularTags = tagElements.filter(el => !el.textContent?.startsWith('+'));

      // 动态测量 "+n" 标签宽度
      let plusWidth = 0;
      if (plusTagElement) {
        plusWidth = plusTagElement.offsetWidth;
      } else {
        // 如果 "+n" 标签不存在，创建一个临时元素来测量
        const tempPlus = document.createElement('span');
        tempPlus.className = 'ant-tag ant-tag-default cursor-pointer bg-gray-100 border-gray-300 text-gray-600 hover:bg-gray-200';
        tempPlus.textContent = '+99';
        tempPlus.style.position = 'absolute';
        tempPlus.style.visibility = 'hidden';
        container.appendChild(tempPlus);
        plusWidth = tempPlus.offsetWidth;
        container.removeChild(tempPlus);
      }

      // 检查每个标签是否超出
      let visibleCount = 0;
      const containerRight = containerRect.right;
      const gap = 4; // gap-1 的宽度

      regularTags.forEach((tagEl, index) => {
        const tagRect = tagEl.getBoundingClientRect();
        const tagRight = tagRect.right;
        const remainingTags = tags.length - index - 1;
        const needsPlusTag = remainingTags > 0;

        // 精确计算：当前标签右边 + gap + (需要 "+n" 的话就加上 "+n" 宽度)
        const totalWidthNeeded = tagRight + (needsPlusTag ? gap + plusWidth : 0);

        if (totalWidthNeeded <= containerRight - 5) {
          visibleCount++;
        } else {
          return false;
        }
      });

      setVisibleTags(tags.slice(0, visibleCount));
      setHiddenTags(tags.slice(visibleCount));
    };

    // 多次尝试计算，确保 DOM 渲染完成
    const timers = [
      setTimeout(calculateVisibleTags, 0),
      setTimeout(calculateVisibleTags, 50),
      setTimeout(calculateVisibleTags, 100),
    ];

    const handleResize = () => {
      calculateVisibleTags();
    };

    window.addEventListener("resize", handleResize);

    return () => {
      timers.forEach(t => clearTimeout(t));
      window.removeEventListener("resize", handleResize);
    };
  }, [tags]);

  if (!tags || tags.length === 0) return null;

  const popoverContent = (
    <div className="max-w-xs">
      <div className="flex flex-wrap gap-1">
        {hiddenTags.map((tag, index) => (
          <Tag
            key={index}
            color={typeof tag === "string" ? undefined : tag.color}
            style={
              typeof tag === "string"
                ? undefined
                : { background: tag.background, color: tag.color }
            }
          >
            {typeof tag === "string" ? tag : (tag.label ? tag.label : tag.name)}
          </Tag>
        ))}
      </div>
    </div>
  );

  return (
    <div ref={containerRef} className="inline-flex gap-1" style={{ overflow: 'hidden', flexWrap: 'nowrap', maxWidth: '100%' }}>
      {visibleTags.map((tag, index) => (
        <Tag
          key={index}
          color={typeof tag === "string" ? undefined : tag.color}
          style={
            typeof tag === "string"
              ? undefined
              : { background: tag.background, color: tag.color }
          }
          className="shrink-0"
        >
          {typeof tag === "string" ? tag : (tag.label ? tag.label : tag.name)}
        </Tag>
      ))}
      {hiddenTags.length > 0 && (
        <Popover
          content={popoverContent}
          title="更多标签"
          trigger="hover"
          placement="topLeft"
        >
          <Tag className="cursor-pointer bg-gray-100 border-gray-300 text-gray-600 hover:bg-gray-200 shrink-0">
            +{hiddenTags.length}
          </Tag>
        </Popover>
      )}
    </div>
  );
};

function CardView<T extends BaseCardDataType>(props: CardViewProps<T>) {
  const {
    data,
    pagination,
    operations,
    loading,
    onView,
    onFavorite,
    isFavorite,
  } = props;

  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <Empty />
      </div>
    );
  }

  const ops = (item) =>
    typeof operations === "function" ? operations(item) : operations;

  return (
    <div className="flex-overflow-hidden">
      <div className="overflow-auto grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4">
        {data.map((item) => (
          <div
            key={item.id}
            className="border-card p-4 bg-white duration-200 transition-shadow transition-transform hover:-translate-y-0.5 hover:shadow-[0_8px_24px_rgba(0,0,0,0.06)]"
          >
            <div className="flex flex-col space-y-4 h-full">
              <div
                className="flex flex-col space-y-4 h-full"
                onClick={() => onView?.(item)}
                style={{ cursor: onView ? "pointer" : "default" }}
              >
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3 min-w-0">
                    {item?.icon && (
                      <div
                        className={`flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center ${
                          item?.iconColor
                            ? ""
                            : "bg-gradient-to-br from-sky-300 to-blue-500 text-white"
                        }`}
                        style={
                          item?.iconColor
                            ? { backgroundColor: item.iconColor }
                            : {}
                        }
                      >
                        <div className="w-[2.1rem] h-[2.1rem] text-gray-50">{item?.icon}</div>
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3
                          className={`text-base flex-1 text-ellipsis overflow-hidden whitespace-nowrap font-semibold text-gray-900 truncate`}
                        >
                          {item?.name}
                        </h3>
                        {item?.status && (
                          <Tag color={item?.status?.color}>
                            <div className="flex items-center gap-2 text-xs py-0.5">
                              {item?.status?.icon && (
                                <span>{item?.status?.icon}</span>
                              )}
                              <span>{item?.status?.label}</span>
                            </div>
                          </Tag>
                        )}
                      </div>
                    </div>
                  </div>
                  {onFavorite &&
                    (isFavorite?.(item) ? (
                      <StarFilled
                        style={{ fontSize: "16px", color: "#ffcc00ff" }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onFavorite?.(item);
                        }}
                      />
                    ) : (
                      <StarOutlined
                        style={{ fontSize: "16px", color: "#d1d5db" }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onFavorite?.(item);
                        }}
                      />
                    ))}
                </div>

                <div className="flex-1 flex flex-col justify-end">
                  {/* Tags */}
                  <TagsRenderer tags={Array.isArray(item?.tags) ? item.tags : []} />

                  {/* Description */}
                  <Tooltip
                    title={item?.description}
                    placement="topLeft"
                    getPopupContainer={(triggerNode) => triggerNode.parentElement || document.body}
                  >
                    <p className="text-gray-400 text-xs text-ellipsis overflow-hidden whitespace-nowrap line-clamp-2 mt-3 mb-2">
                      {item?.description}
                    </p>
                  </Tooltip>

                  {/* Statistics */}
                  <div className="grid grid-cols-2 gap-4 py-2">
                    {item?.statistics?.map((stat, idx) => (
                      <div key={idx}>
                        <div className="text-sm text-gray-500 overflow-hidden whitespace-nowrap text-ellipsis w-full">
                          {stat?.label}:
                        </div>
                        <div className="text-base font-semibold text-gray-900 overflow-hidden whitespace-nowrap text-ellipsis w-full">
                          {stat?.value}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Divider & Actions */}
              <div className="flex border-t border-t-gray-200 mt-2" />
              <div className="flex items-center justify-between pt-3">
                <div className=" text-gray-500 text-right">
                  <div className="flex items-center gap-1">
                    <ClockCircleOutlined className="w-4 h-4" />{" "}
                    {formatDateTime(item?.updatedAt)}
                  </div>
                </div>
                {operations && (
                  <ActionDropdown
                    actions={ops(item)}
                    item={item}
                    onAction={(key) => {
                      // ActionDropdown 已经处理了 onClick 调用
                    }}
                  />
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="flex justify-end mt-6">
        <Pagination {...pagination} />
      </div>
    </div>
  );
}

export default CardView;
