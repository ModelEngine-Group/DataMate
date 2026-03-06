import React, { useMemo } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

export interface CodePreviewProps {
  content?: string;
  fileName?: string;
}

// 文件扩展名到 Prism 语言映射
const LANGUAGE_MAP: Record<string, string> = {
  // JavaScript/TypeScript
  'js': 'javascript',
  'jsx': 'jsx',
  'ts': 'typescript',
  'tsx': 'tsx',
  'mjs': 'javascript',

  // Python
  'py': 'python',
  'pyw': 'python',

  // Java
  'java': 'java',

  // C/C++
  'c': 'c',
  'cpp': 'cpp',
  'cc': 'cpp',
  'cxx': 'cpp',
  'h': 'c',
  'hpp': 'cpp',

  // C#
  'cs': 'csharp',

  // Go
  'go': 'go',

  // Rust
  'rs': 'rust',

  // PHP
  'php': 'php',

  // Ruby
  'rb': 'ruby',

  // Shell
  'sh': 'bash',
  'bash': 'bash',
  'zsh': 'bash',

  // SQL
  'sql': 'sql',

  // HTML/CSS
  'html': 'html',
  'htm': 'html',
  'css': 'css',
  'scss': 'scss',
  'less': 'less',

  // XML
  'xml': 'xml',

  // YAML
  'yaml': 'yaml',
  'yml': 'yaml',

  // 其他
  'txt': 'clike', // 通用类 C 语言
};

export const CodePreview: React.FC<CodePreviewProps> = ({
  content = '',
  fileName
}) => {
  // 根据文件扩展名检测语言
  const language = useMemo(() => {
    if (!fileName) return 'clike';
    const ext = fileName.toLowerCase().split('.').pop() || '';
    return LANGUAGE_MAP[ext] || 'clike';
  }, [fileName]);

  if (!content) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No content available
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      <SyntaxHighlighter
        language={language}
        style={vscDarkPlus}
        showLineNumbers
        customStyle={{
          margin: 0,
          borderRadius: 0,
          fontSize: '0.875rem',
          minHeight: '100%'
        }}
      >
        {content}
      </SyntaxHighlighter>
    </div>
  );
};
