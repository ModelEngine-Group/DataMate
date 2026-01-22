import { Card } from "antd";
import ReactMarkdown from "react-markdown";
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

export default function Documentation({ operator }) {
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <div className="prose prose-slate max-w-none dark:prose-invert">
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
              // 2. 标题样式 (强制覆盖 Tailwind 的默认重置)
              h1: ({node, ...props}) => <h1 className="text-3xl font-bold text-gray-900 mt-8 mb-4 border-b pb-2" {...props} />,
              h2: ({node, ...props}) => <h2 className="text-2xl font-bold text-gray-800 mt-6 mb-4" {...props} />,
              h3: ({node, ...props}) => <h3 className="text-xl font-semibold text-gray-800 mt-5 mb-3" {...props} />,
              h4: ({node, ...props}) => <h4 className="text-lg font-semibold text-gray-700 mt-4 mb-2" {...props} />,
              h5: ({node, ...props}) => <h5 className="text-base font-medium text-gray-700 mt-3 mb-2" {...props} />,
              // 3. 其他常用标签优化 (推荐加上)
              p: ({node, ...props}) => <p className="leading-7 text-gray-700 my-4" {...props} />,
              ul: ({node, ...props}) => <ul className="list-disc list-outside ml-6 space-y-2 my-4 text-gray-700" {...props} />,
              ol: ({node, ...props}) => <ol className="list-decimal list-outside ml-6 space-y-2 my-4 text-gray-700" {...props} />,
              li: ({node, ...props}) => <li className="pl-1" {...props} />,
              a: ({node, ...props}) => <a className="text-blue-600 hover:underline font-medium" target="_blank" {...props} />,
              blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600 my-4" {...props} />,
              hr: ({node, ...props}) => <hr className="my-8 border-gray-200" {...props} />,
              img: ({node, ...props}) => <img className="rounded-lg border shadow-sm my-4 max-w-full h-auto" {...props} alt="" />,
              table: ({node, ...props}) => <div className="overflow-x-auto my-4"><table className="min-w-full divide-y divide-gray-200 border" {...props} /></div>,
              th: ({node, ...props}) => <th className="bg-gray-50 px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b" {...props} />,
              td: ({node, ...props}) => <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-700 border-b" {...props} />,
            }}
          >
            {operator.readme || ""}
          </ReactMarkdown>
        </div>
      </Card>
    </div>
  );
}
