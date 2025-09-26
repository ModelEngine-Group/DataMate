import React from "react";
import { Card, Tag, Pagination, Dropdown, Tooltip, Empty } from "antd";
import {
  EllipsisOutlined,
  ClockCircleOutlined,
  StarFilled,
} from "@ant-design/icons";
import type { ItemType } from "antd/es/menu/interface";

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
  lastModified: string;
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
          <Card key={item.id} className="hover:shadow-lg transition-shadow">
            <div className="space-y-4">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className={`flex-shrink-0 w-10 h-10 ${item.iconColor} rounded-lg flex items-center justify-center`}
                  >
                    {item.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3
                        className="text-base flex-1 text-ellipsis overflow-hidden whitespace-nowrap font-semibold text-gray-900 truncate cursor-pointer hover:text-blue-600"
                        onClick={() => onView?.(item)}
                      >
                        {item.name}
                      </h3>
                      {item.status && (
                        <Tag color={item.status.color}>
                          <div className="flex items-center gap-2 text-xs py-0.5">
                            <span>{item.status.icon}</span>
                            <span>{item.status.label}</span>
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

              {/* Tags */}
              <div className="flex flex-wrap gap-1">
                {item?.tags?.slice(0, 3)?.map((tag, index) => (
                  <Tag key={index}>{tag}</Tag>
                ))}
              </div>
              {/* Description */}
              <p className="text-gray-600 text-xs text-ellipsis overflow-hidden whitespace-nowrap text-xs line-clamp-2">
                <Tooltip title={item.description}>{item.description}</Tooltip>
              </p>
              {/* Statistics */}
              <div className="grid grid-cols-2 gap-4 py-3">
                {item.statistics?.map((stat, idx) => (
                  <div key={idx}>
                    <div className="text-sm text-gray-500">{stat.label}:</div>
                    <div className="text-base font-semibold text-gray-900">
                      {stat.value}
                    </div>
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-3 border-t border-t-gray-200">
                <div className=" text-gray-500 text-right">
                  <div className="flex items-center gap-1">
                    <ClockCircleOutlined className="w-4 h-4" />{" "}
                    {item.lastModified}
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
          </Card>
        ))}
      </div>
      <div className="flex justify-end mt-6">
        <Pagination {...pagination} />
      </div>
    </div>
  );
}

export default CardView;
