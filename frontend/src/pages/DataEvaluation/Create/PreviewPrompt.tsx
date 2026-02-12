import React from 'react';
import { Button, message, Modal } from 'antd';
import { useTranslation } from "react-i18next";

interface PreviewPromptModalProps {
  previewVisible: boolean;
  onCancel: () => void;
  evaluationPrompt: string;
}

const PreviewPromptModal: React.FC<PreviewPromptModalProps> = ({ previewVisible, onCancel, evaluationPrompt }) => {
  const { t } = useTranslation();
  return (
    <Modal
      title={t("dataEvaluation.preview.title")}
      open={previewVisible}
      onCancel={onCancel}
      footer={[
        <Button key="copy" onClick={() => {
          navigator.clipboard.writeText(evaluationPrompt).then();
          message.success(t("dataEvaluation.preview.copiedMessage"));
        }}>
          {t("dataEvaluation.preview.copy")}
        </Button>,
        <Button key="close" type="primary" onClick={onCancel}>
          {t("dataEvaluation.preview.close")}
        </Button>
      ]}
      width={800}
    >
      <div style={{
        background: '#f5f5f5',
        padding: '16px',
        borderRadius: '4px',
        whiteSpace: 'pre-wrap',
        fontFamily: 'monospace'
      }}>
        {evaluationPrompt}
      </div>
    </Modal>
  )
}

export default PreviewPromptModal;
