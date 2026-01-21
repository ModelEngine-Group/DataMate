import { Card } from "antd";
import ReactMarkdown from "react-markdown";
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

export default function Documentation({ operator }) {
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <div className="prose prose-blue max-w-none dark:prose-invert">
          <ReactMarkdown
            // 1. 启用 GFM 插件 (支持表格等)
            remarkPlugins={[remarkGfm]}

            // 2. 自定义渲染组件 (实现代码高亮)
            components={{
              code({ node, inline, className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter
                    {...props}
                    style={vscDarkPlus} // 代码块样式
                    language={match[1]} // 语言类型
                    PreTag="div"
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code {...props} className={className}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {operator.readme || ""}
          </ReactMarkdown>
        </div>
      </Card>
    </div>
  );
}
