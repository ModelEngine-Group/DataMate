import { Modal } from "antd";
import { useTranslation } from "react-i18next";

export interface DeleteConfirmModalProps {
  visible: boolean;
  title?: string;
  message?: string;
  itemName?: string;
  onConfirm: () => void | Promise<void>;
  onCancel: () => void;
}

/**
 * 公共删除确认弹窗组件
 * 样式参考任务管理的删除弹窗
 *
 * @example
 * ```tsx
 * const [deleteModal, setDeleteModal] = useState({
 *   visible: false,
 *   itemName: "",
 * });
 *
 * <DeleteConfirmModal
 *   visible={deleteModal.visible}
 *   itemName={deleteModal.itemName}
 *   onConfirm={async () => {
 *     await deleteItem(deleteModal.id);
 *     setDeleteModal({ visible: false, itemName: "" });
 *   }}
 *   onCancel={() => setDeleteModal({ visible: false, itemName: "" })}
 * />
 * ```
 */
export default function DeleteConfirmModal({
  visible,
  title,
  message,
  itemName,
  onConfirm,
  onCancel,
}: DeleteConfirmModalProps) {
  const { t } = useTranslation();

  const defaultTitle = title || t("components.deleteConfirm.title");
  // 如果提供了自定义 message，直接使用；否则使用默认消息并替换占位符
  const defaultMessage = message
    ? message.replace("{{itemName}}", itemName || "").replace("{{taskName}}", itemName || "")
    : t("components.deleteConfirm.message", { itemName: itemName || "" });

  return (
    <Modal
      title={defaultTitle}
      open={visible}
      onOk={onConfirm}
      onCancel={onCancel}
      okType="danger"
      okText={t("components.deleteConfirm.confirm")}
      cancelText={t("components.deleteConfirm.cancel")}
      centered
    >
      <p>{defaultMessage}</p>
    </Modal>
  );
}
