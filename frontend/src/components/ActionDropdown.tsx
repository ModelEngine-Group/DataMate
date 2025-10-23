import { Dropdown, Popconfirm, Button, Space } from "antd";
import { EllipsisOutlined } from "@ant-design/icons";
import { useState } from "react";

interface ActionItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  danger?: boolean;
  confirm?: {
    title: string;
    description?: string;
    okText?: string;
    cancelText?: string;
  };
}

interface ActionDropdownProps {
  actions?: ActionItem[];
  onAction?: (key: string, action: ActionItem) => void;
  placement?:
    | "bottomRight"
    | "topLeft"
    | "topCenter"
    | "topRight"
    | "bottomLeft"
    | "bottomCenter"
    | "top"
    | "bottom";
}

const ActionDropdown = ({
  actions = [],
  onAction,
  placement = "bottomRight",
}: ActionDropdownProps) => {
  const [open, setOpen] = useState(false);
  const handleActionClick = (action: ActionItem) => {
    if (action.confirm) {
      // 如果有确认框，不立即执行，等待确认
      return;
    }
    // 执行操作
    onAction?.(action.key, action);
    // 如果没有确认框，则立即关闭 Dropdown
    setOpen(false);
  };

  const dropdownContent = (
    <div className="bg-white p-2 rounded shadow-md">
      <Space direction="vertical" className="w-full">
        {actions.map((action) => {
          if (action.confirm) {
            return (
              <Popconfirm
                key={action.key}
                title={action.confirm.title}
                description={action.confirm.description}
                onConfirm={() => {
                  onAction?.(action.key, action);
                  setOpen(false);
                }}
                okText={action.confirm.okText || "确定"}
                cancelText={action.confirm.cancelText || "取消"}
                okType={action.danger ? "danger" : "primary"}
                styles={{ root: { zIndex: 9999 } }}
              >
                <Button
                  type="text"
                  size="small"
                  className="w-full text-left"
                  danger={action.danger}
                  icon={action.icon}
                >
                  {action.label}
                </Button>
              </Popconfirm>
            );
          }

          return (
            <Button
              key={action.key}
              className="w-full"
              size="small"
              type="text"
              danger={action.danger}
              icon={action.icon}
              onClick={() => handleActionClick(action)}
            >
              {action.label}
            </Button>
          );
        })}
      </Space>
    </div>
  );

  return (
    <Dropdown
      overlay={dropdownContent}
      trigger={["click"]}
      placement={placement}
      open={open}
      onOpenChange={setOpen}
    >
      <Button
        type="text"
        icon={<EllipsisOutlined style={{ fontSize: 24 }} />}
      />
    </Dropdown>
  );
};

export default ActionDropdown;
