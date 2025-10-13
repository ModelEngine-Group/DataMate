import { copyToClipboard } from "@/utils/unit";
import { Card, Button } from "antd";
import { Copy } from "lucide-react";

export default function Examples({ operator }) {
  return (
    <div className="flex flex-col gap-4">
      {operator.examples.map((example, index) => (
        <Card key={index}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              {example.title}
            </h3>
            <Button size="small" onClick={() => copyToClipboard(example.code)}>
              <Copy className="w-4 h-4 mr-2" />
              复制代码
            </Button>
          </div>
          <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
            <pre className="text-sm">
              <code>{example.code}</code>
            </pre>
          </div>
        </Card>
      ))}
    </div>
  );
}
