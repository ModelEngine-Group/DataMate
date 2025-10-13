import { Card } from "antd";

export default function Documentation({ operator }) {
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <div className="prose max-w-none">
          <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
            {operator.documentation}
          </div>
        </div>
      </Card>
    </div>
  );
}
