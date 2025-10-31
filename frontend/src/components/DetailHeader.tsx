import React from "react";
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
  tags: { id: number; name: string; color: string }[];
  onFetchTags?: () => Promise<{
    data: { id: number; name: string; color: string }[];
  }>;
  onAddTag?: (tag: { id: number; name: string; color: string }) => void;
  onCreateAndTag?: (tagName: string) => void;
}
interface DetailHeaderProps<T> {
  data: T;
  statistics: StatisticItem[];
  operations: OperationItem[];
  tagConfig?: TagConfig;
}

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
            className={`w-16 h-16 text-white rounded-lg flex-center shadow-lg bg-gradient-to-br from-sky-300 to-blue-500 text-white`}
          >
            {<div className="w-8 h-8 text-gray-50">{data?.icon}</div> || (
              <Database className="w-8 h-8 text-white" />
            )}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-lg font-bold text-gray-900">{data?.name}</h1>
              {data?.status && (
                <Tag color={data.status?.color}>
                  <div className="flex items-center gap-2 text-xs">
                    <span>{data.status?.icon}</span>
                    <span>{data.status?.label}</span>
                  </div>
                </Tag>
              )}
            </div>
            {data?.tags && (
              <div className="flex flex-wrap mb-2">
                {data?.tags?.map((tag) => (
                  <Tag key={tag.id} className="mr-1">
                    {tag.name}
                  </Tag>
                ))}
                {tagConfig?.showAdd && (
                  <AddTagPopover
                    tags={tagConfig.tags}
                    onFetchTags={tagConfig.onFetchTags}
                    onAddTag={tagConfig.onAddTag}
                    onCreateAndTag={tagConfig.onCreateAndTag}
                  />
                )}
              </div>
            )}
            <p className="text-gray-700 mb-4">{data?.description}</p>
            <div className="flex items-center gap-6 text-sm">
              {statistics.map((stat) => (
                <div key={stat.key} className="flex items-center gap-1">
                  {stat.icon}
                  <span>{stat.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {operations.map((op) => {
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
                      op?.confirm?.onConfirm?.();
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
