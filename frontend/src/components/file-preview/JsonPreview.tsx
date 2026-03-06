import React, { useMemo } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

export interface JsonPreviewProps {
  content?: string;
  fileName?: string;
}

export const JsonPreview: React.FC<JsonPreviewProps> = ({
  content = '',
  fileName
}) => {
  // 尝试解析并格式化 JSON
  const { formattedContent, error } = useMemo(() => {
    if (!content) {
      return { formattedContent: '', error: 'No content available' };
    }

    try {
      const data = JSON.parse(content);
      const formatted = JSON.stringify(data, null, 2);
      return { formattedContent: formatted, error: null };
    } catch (err) {
      return {
        formattedContent: '',
        error: err instanceof Error ? err.message : 'Invalid JSON format'
      };
    }
  }, [content]);

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-500">
        <div className="text-center">
          <p className="text-lg mb-2">⚠️ JSON Parse Failed</p>
          <p className="text-sm text-gray-400 mb-4">{error}</p>
          <p className="text-xs text-gray-500">Displaying as plain text</p>
        </div>
      </div>
    );
  }

  if (!formattedContent) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No content available
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      <SyntaxHighlighter
        language="json"
        style={vscDarkPlus}
        showLineNumbers
        customStyle={{
          margin: 0,
          borderRadius: 0,
          fontSize: '0.875rem',
          minHeight: '100%'
        }}
      >
        {formattedContent}
      </SyntaxHighlighter>
    </div>
  );
};
