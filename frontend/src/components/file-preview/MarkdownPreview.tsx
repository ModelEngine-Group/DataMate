import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

export interface MarkdownPreviewProps {
  content?: string;
  fileName?: string;
}

export const MarkdownPreview: React.FC<MarkdownPreviewProps> = ({
  content = '',
  fileName
}) => {
  if (!content) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No content available
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto p-6 bg-white">
      <div className="prose prose-sm max-w-none markdown-content">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // 代码块高亮
            code({ node, inline, className, children, ...props }: any) {
              const match = /language-(\w+)/.exec(className || '');
              const codeString = String(children).replace(/\n$/, '');

              if (inline) {
                return (
                  <code className="px-1 py-0.5 bg-gray-100 rounded text-sm font-mono" {...props}>
                    {children}
                  </code>
                );
              }

              if (match) {
                return (
                  <SyntaxHighlighter
                    {...props}
                    style={vscDarkPlus}
                    language={match[1]}
                    PreTag="div"
                    customStyle={{
                      borderRadius: '0.5rem',
                      padding: '1rem',
                      fontSize: '0.875rem'
                    }}
                  >
                    {codeString}
                  </SyntaxHighlighter>
                );
              }

              return (
                <pre className="bg-gray-100 p-4 rounded-lg overflow-x-auto">
                  <code className="text-sm" {...props}>
                    {codeString}
                  </code>
                </pre>
              );
            },
            // 链接
            a: ({ href, children }) => (
              <a
                href={href}
                className="text-blue-600 hover:text-blue-800 underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                {children}
              </a>
            ),
            // 表格
            table: ({ children }) => (
              <div className="overflow-x-auto my-4">
                <table className="min-w-full divide-y divide-gray-200 border">
                  {children}
                </table>
              </div>
            ),
            thead: ({ children }) => (
              <thead className="bg-gray-50">{children}</thead>
            ),
            th: ({ children }) => (
              <th className="px-4 py-2 text-left text-sm font-semibold text-gray-700 border">
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td className="px-4 py-2 text-sm text-gray-700 border">
                {children}
              </td>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
};
