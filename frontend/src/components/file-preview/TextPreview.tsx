import React from 'react';

export interface TextPreviewProps {
  content?: string;
}

export const TextPreview: React.FC<TextPreviewProps> = ({
  content = ''
}) => {
  if (!content) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No content available
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto p-4 bg-gray-50">
      <pre className="text-sm font-mono whitespace-pre-wrap break-words text-gray-800">
        {content}
      </pre>
    </div>
  );
};
