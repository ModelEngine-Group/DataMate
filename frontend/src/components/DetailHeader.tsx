import React from "react";
import { Database } from "lucide-react";
import { Card, Dropdown, Button, Tag, Tooltip } from "antd";
import type { ItemType } from "antd/es/menu/interface";

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

interface DetailHeaderProps<T> {
  data: T;
  statistics: StatisticItem[];
  operations: OperationItem[];
}

const DetailHeader: React.FC<DetailHeaderProps<any>> = <T,>({
  data,
  statistics,
  operations,
}: DetailHeaderProps<T>) => {
  return (
    <Card>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4 flex-1">
          <div
            className={`w-16 h-16 text-white rounded-xl flex items-center justify-center shadow-lg ${
              data?.iconColor
                ? data.iconColor
                : "bg-gradient-to-br from-blue-100 to-blue-200"
            }`}
          >
            {data?.icon || <Database className="w-8 h-8" />}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-lg font-bold text-gray-900">{data.name}</h1>
              {data?.status && (
                <Tag color={data.status.color}>
                  <div className="flex items-center gap-2 text-xs">
                    <span>{data.status.icon}</span>
                    <span>{data.status.label}</span>
                  </div>
                </Tag>
              )}
            </div>
            <p className="text-gray-700 mb-4">{data.description}</p>
            {data?.tags?.map((tag) => (
              <Tag
                key={tag.id}
                className="mr-1"
                style={{ background: tag.color }}
              >
                {tag.name}
              </Tag>
            ))}
            <div className="flex items-center gap-6 text-sm">
              {statistics.map((stat, idx) => (
                <div key={idx} className="flex items-center gap-1">
                  {stat.icon}
                  <span>
                    {stat.value} {stat.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {operations.map((op) => {
            if (op.isDropdown) {
              return (
                <Dropdown
                  key={op.key}
                  menu={{
                    items: op.items as ItemType[],
                    onClick: op.onMenuClick,
                  }}
                >
                  <Tooltip title={op.label}>
                    <Button icon={op.icon} />
                  </Tooltip>
                </Dropdown>
              );
            }
            return (
              <Tooltip title={op.label}>
                <Button
                  key={op.key}
                  onClick={op.onClick}
                  className={
                    op.danger
                      ? "text-red-600 border-red-200 bg-transparent"
                      : ""
                  }
                  icon={op.icon}
                />
              </Tooltip>
            );
          })}
          {/* <Dropdown trigger={['click']} menu={{
                        items: operations as ItemType[], onClick: ({ key }) => {
                            const operation = operations.find(op => op.key === key);
                            if (operation?.onClick) {
                                operation.onClick(item);
                            }
                        }
                    }}><div className="cursor-pointer"><Ellipsis /></div></Dropdown> */}
        </div>
      </div>
    </Card>
  );
};

export default DetailHeader;
