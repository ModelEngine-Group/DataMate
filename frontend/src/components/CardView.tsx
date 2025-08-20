import React, { useState } from "react";
import { Card, Tag, Pagination, Dropdown, Tooltip } from "antd";
import { Star, Ellipsis, Clock } from "lucide-react";
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
  pageSize?: number;
  operations: {
    key: string;
    label: string;
    icon?: React.JSX.Element;
    onClick?: (item: T) => void;
  }[];
  onView: (item: T) => void;
  onFavorite?: (item: T) => void;
  isFavorite?: (item: T) => boolean;
}

function CardView<T extends BaseCardDataType>(props: CardViewProps<T>) {
  const {
    data,
    pageSize = 8,
    operations,
    onView,
    onFavorite,
    isFavorite,
  } = props;

  const [current, setCurrent] = useState(1);

  const pagedData = data.slice((current - 1) * pageSize, current * pageSize);

  return (
    <div className="flex-1 overflow-auto">
      <div className="grid md:grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-4">
        {pagedData.map((item) => (
          <Card key={item.id} className="hover:shadow-lg transition-shadow">
            <div className="space-y-4">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3 flex-1">
                  <div
                    className={`flex-shrink-0 w-12 h-12 ${item.iconColor} rounded flex items-center justify-center`}
                  >
                    {item.icon}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3
                        className="text-lg font-semibold text-gray-900 truncate cursor-pointer hover:text-blue-600"
                        onClick={() => onView?.(item)}
                      >
                        {item.name}
                      </h3>
                      {item.status && (
                        <Tag
                          icon={item.status.icon}
                          color={item.status.color}
                          className="text-xs"
                        >
                          {item.status.label}
                        </Tag>
                      )}
                    </div>
                  </div>
                </div>
                {onFavorite && (
                  <Star
                    className={`w-4 h-4 p-0 border-none ${
                      isFavorite?.(item)
                        ? "fill-current text-yellow-500 hover:text-yellow-600"
                        : "text-gray-400 hover:text-yellow-500"
                    }`}
                    onClick={() => onFavorite?.(item)}
                  />
                )}
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-1">
                {item?.tags?.slice(0, 3)?.map((tag, index) => (
                  <Tag key={index} className="">
                    {tag}
                  </Tag>
                ))}
              </div>

              {/* Description */}
              <p className="text-gray-600 text-ellipsis overflow-hidden whitespace-nowrap  text-sm line-clamp-2">
                <Tooltip title={item.description}>{item.description}</Tooltip>
              </p>

              {/* Statistics */}
              <div className="grid grid-cols-2 gap-4 py-3">
                {item.statistics?.map((stat, idx) => (
                  <div key={idx}>
                    <div className="text-sm text-gray-500">{stat.label}:</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {stat.value}
                    </div>
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-3 border-t border-t-gray-200">
                <div className=" text-gray-500 text-right">
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" /> {item.lastModified}
                  </div>
                </div>
                <Dropdown
                  trigger={["click"]}
                  menu={{
                    items: operations as ItemType[],
                    onClick: ({ key }) => {
                      const operation = operations.find((op) => op.key === key);
                      if (operation?.onClick) {
                        operation.onClick(item);
                      }
                    },
                  }}
                >
                  <div className="cursor-pointer">
                    <Ellipsis />
                  </div>
                </Dropdown>
              </div>
            </div>
          </Card>
        ))}
      </div>
      <div className="flex justify-end mt-6">
        <Pagination
          current={current}
          pageSize={pageSize}
          total={data.length}
          onChange={setCurrent}
          showSizeChanger={false}
        />
      </div>
    </div>
  );
}

export default CardView;
