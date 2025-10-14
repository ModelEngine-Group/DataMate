import React, { useState, useEffect, useRef } from "react";
import { Tag, Pagination, Dropdown, Tooltip, Empty, Popover } from "antd";
import {
  EllipsisOutlined,
  ClockCircleOutlined,
  StarFilled,
} from "@ant-design/icons";
import type { ItemType } from "antd/es/menu/interface";
import { formatDateTime } from "@/utils/unit";

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
  tags?: string[];
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
        icon?: React.JSX.Element;
        onClick?: (item: T) => void;
      }[]
    | ((item: T) => ItemType[]);
  onView: (item: T) => void;
  onFavorite?: (item: T) => void;
  isFavorite?: (item: T) => boolean;
}

// 标签渲染组件
const TagsRenderer = ({ tags }: { tags?: any[] }) => {
  const [visibleTags, setVisibleTags] = useState<any[]>([]);
  const [hiddenTags, setHiddenTags] = useState<any[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!tags || tags.length === 0) return;

    const calculateVisibleTags = () => {
      if (!containerRef.current) return;

      const containerWidth = containerRef.current.offsetWidth;
      const tempDiv = document.createElement("div");
      tempDiv.style.visibility = "hidden";
      tempDiv.style.position = "absolute";
      tempDiv.style.top = "-9999px";
      tempDiv.className = "flex flex-wrap gap-1";
      document.body.appendChild(tempDiv);

      let totalWidth = 0;
      let visibleCount = 0;
      const tagElements: HTMLElement[] = [];

      // 为每个tag创建临时元素来测量宽度
      tags.forEach((tag, index) => {
        const tagElement = document.createElement("span");
        tagElement.className = "ant-tag ant-tag-default";
        tagElement.style.margin = "2px";
        tagElement.textContent = typeof tag === "string" ? tag : tag.name;
        tempDiv.appendChild(tagElement);
        tagElements.push(tagElement);

        const tagWidth = tagElement.offsetWidth + 4; // 加上gap的宽度

        // 如果不是最后一个标签，需要预留+n标签的空间
        const plusTagWidth = index < tags.length - 1 ? 35 : 0; // +n标签大约35px宽度

        if (totalWidth + tagWidth + plusTagWidth <= containerWidth) {
          totalWidth += tagWidth;
          visibleCount++;
        } else {
          // 如果当前标签放不下，且已经有可见标签，则停止
          if (visibleCount > 0) return;
          // 如果是第一个标签就放不下，至少显示一个
          if (index === 0) {
            totalWidth += tagWidth;
            visibleCount = 1;
          }
        }
      });

      document.body.removeChild(tempDiv);

      setVisibleTags(tags.slice(0, visibleCount));
      setHiddenTags(tags.slice(visibleCount));
    };

    // 延迟执行以确保DOM已渲染
    const timer = setTimeout(calculateVisibleTags, 0);

    // 监听窗口大小变化
    const handleResize = () => {
      calculateVisibleTags();
    };

    window.addEventListener("resize", handleResize);

    return () => {
      clearTimeout(timer);
      window.removeEventListener("resize", handleResize);
    };
  }, [tags]);

  if (!tags || tags.length === 0) return null;

  const popoverContent = (
    <div className="max-w-xs">
      <div className="flex flex-wrap gap-1">
        {hiddenTags.map((tag, index) => (
          <Tag key={index}>{typeof tag === "string" ? tag : tag.name}</Tag>
        ))}
      </div>
    </div>
  );

  return (
    <div ref={containerRef} className="flex flex-wrap gap-1 w-full">
      {visibleTags.map((tag, index) => (
        <Tag key={index}>{typeof tag === "string" ? tag : tag.name}</Tag>
      ))}
      {hiddenTags.length > 0 && (
        <Popover
          content={popoverContent}
          title="更多标签"
          trigger="hover"
          placement="topLeft"
        >
          <Tag className="cursor-pointer bg-gray-100 border-gray-300 text-gray-600 hover:bg-gray-200">
            +{hiddenTags.length}
          </Tag>
        </Popover>
      )}
    </div>
  );
};

function CardView<T extends BaseCardDataType>(props: CardViewProps<T>) {
  const { data, pagination, operations, onView, onFavorite, isFavorite } =
    props;

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
    <div className="flex-1 overflow-auto">
      <div className="grid md:grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {data.map((item) => (
          <div
            key={item.id}
            className="border border-gray-100 rounded-lg p-4 bg-white hover:shadow-lg transition-shadow duration-200"
          >
            <div className="flex flex-col space-y-4 h-full">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  {item?.icon && (
                    <div
                      className={`flex-shrink-0 w-12 h-12 ${
                        item?.iconColor ||
                        "bg-gradient-to-br from-blue-100 to-blue-200"
                      } rounded-lg flex items-center justify-center`}
                    >
                      {item?.icon}
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3
                        className="text-base flex-1 text-ellipsis overflow-hidden whitespace-nowrap font-semibold text-gray-900 truncate cursor-pointer hover:text-blue-600"
                        onClick={() => onView?.(item)}
                      >
                        {item?.name}
                      </h3>
                      {item?.status && (
                        <Tag color={item?.status?.color}>
                          <div className="flex items-center gap-2 text-xs py-0.5">
                            <span>{item?.status?.icon}</span>
                            <span>{item?.status?.label}</span>
                          </div>
                        </Tag>
                      )}
                    </div>
                  </div>
                </div>
                {onFavorite && (
                  <StarFilled
                    style={{
                      fontSize: "16px",
                      color: isFavorite?.(item) ? "#ffcc00ff" : "#d1d5db",
                      cursor: "pointer",
                    }}
                    onClick={() => onFavorite?.(item)}
                  />
                )}
              </div>

              <div className="flex-1 flex flex-col justify-end">
                {/* Tags */}
                <TagsRenderer tags={item?.tags || []} />

                {/* Description */}
                <p className="text-gray-600 text-xs text-ellipsis overflow-hidden whitespace-nowrap text-xs line-clamp-2 mt-2">
                  <Tooltip title={item?.description}>
                    {item?.description}
                  </Tooltip>
                </p>

                {/* Statistics */}
                <div className="grid grid-cols-2 gap-4 py-3">
                  {item?.statistics?.map((stat, idx) => (
                    <div key={idx}>
                      <div className="text-sm text-gray-500">
                        {stat?.label}:
                      </div>
                      <div className="text-base font-semibold text-gray-900">
                        {stat?.value}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-3 border-t border-t-gray-200">
                <div className=" text-gray-500 text-right">
                  <div className="flex items-center gap-1">
                    <ClockCircleOutlined className="w-4 h-4" />{" "}
                    {formatDateTime(item?.updatedAt)}
                  </div>
                </div>
                <Dropdown
                  trigger={["click"]}
                  menu={{
                    items: ops(item),
                    onClick: ({ key }) => {
                      const operation = ops(item).find((op) => op.key === key);
                      if (operation?.onClick) {
                        operation.onClick(item);
                      }
                    },
                  }}
                >
                  <div className="cursor-pointer">
                    <EllipsisOutlined style={{ fontSize: 24 }} />
                  </div>
                </Dropdown>
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
