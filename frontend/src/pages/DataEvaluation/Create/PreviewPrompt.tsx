import React from 'react';
import { Button, message, Modal } from 'antd';

interface PreviewPromptModalProps {
  previewVisible: boolean;
  onCancel: () => void;
  evaluationPrompt: string;
}

const PreviewPromptModal: React.FC<PreviewPromptModalProps> = ({ previewVisible, onCancel, evaluationPrompt }) => {
  return (
    <Modal
      title="评估提示词预览"
      open={previewVisible}
      onCancel={onCancel}
      footer={[
        <Button key="copy" onClick={() => {
          navigator.clipboard.writeText(evaluationPrompt).then();
          message.success('已复制到剪贴板');
        }}>
          复制
        </Button>,
        <Button key="close" type="primary" onClick={onCancel}>
          关闭
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
