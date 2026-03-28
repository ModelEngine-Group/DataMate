import { Dropdown, Button, Space } from "antd";
import { EllipsisOutlined } from "@ant-design/icons";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import DeleteConfirmModal from "./DeleteConfirmModal";

interface ActionItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  danger?: boolean;
  disabled?: boolean;
  confirm?: {
    title?: string;
    message?: string;
    itemName?: string | ((item: any) => string);
    okText?: string;
    cancelText?: string;
    okType?: "default" | "primary" | "danger";
  };
  onClick?: (item?: any) => void | Promise<void>;
}

interface ActionDropdownProps {
  actions?: ActionItem[];
  onAction?: (key: string, action: ActionItem, item?: any) => void;
  item?: any;
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
  item,
  placement = "bottomRight",
}: ActionDropdownProps) => {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{
    visible: boolean;
    action: ActionItem | null;
  }>({
    visible: false,
    action: null,
  });

  const handleActionClick = (action: ActionItem, e: React.MouseEvent) => {
    e?.stopPropagation();

    if (action.confirm) {
      // 显示删除确认弹窗
      setDeleteConfirm({
        visible: true,
        action,
      });
      setOpen(false);
      return;
    }

    // 执行操作
    if (action.onClick) {
      action.onClick(item);
    }
    onAction?.(action.key, action, item);
    setOpen(false);
  };

  const handleConfirmDelete = async () => {
    if (deleteConfirm.action?.onClick) {
      await deleteConfirm.action.onClick(item);
    }
    if (deleteConfirm.action) {
      onAction?.(deleteConfirm.action.key, deleteConfirm.action, item);
    }
    setDeleteConfirm({ visible: false, action: null });
  };

  const handleCancelDelete = () => {
    setDeleteConfirm({ visible: false, action: null });
  };

  const dropdownContent = (
    <div className="bg-white p-2 rounded shadow-md">
      <Space direction="vertical" className="w-full">
        {actions.map((action) => (
          <Button
            key={action.key}
            className="w-full"
            size="small"
            type="text"
            disabled={action.disabled || false}
            danger={action.danger}
            icon={action.icon}
            onClick={(e) => handleActionClick(action, e)}
          >
            {action.label}
          </Button>
        ))}
      </Space>
    </div>
  );

  return (
    <>
      <Dropdown
        menu={{ items: [] }}
        popupRender={() => dropdownContent}
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

      {deleteConfirm.action?.confirm && (
        <DeleteConfirmModal
          visible={deleteConfirm.visible}
          title={deleteConfirm.action.confirm.title}
          message={deleteConfirm.action.confirm.message}
          itemName={
            typeof deleteConfirm.action.confirm.itemName === 'function'
              ? deleteConfirm.action.confirm.itemName(item)
              : deleteConfirm.action.confirm.itemName
          }
          onConfirm={handleConfirmDelete}
          onCancel={handleCancelDelete}
        />
      )}
    </>
  );
};

export default ActionDropdown;
