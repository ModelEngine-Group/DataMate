import { Card } from "antd";
import { Badge, ChevronRight } from "lucide-react";

export default function ChangeLog({ operator }) {
  return (
    <div className="flex flex-col gap-4">
      {operator.changelog.map((version, index) => (
        <Card key={index}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                版本 {version.version}
              </h3>
              <p className="text-sm text-gray-600">{version.date}</p>
            </div>
            {index === 0 && (
              <Badge className="bg-blue-100 text-blue-800 border border-blue-200">
                最新版本
              </Badge>
            )}
          </div>
          <ul className="space-y-2">
            {version.changes.map((change, changeIndex) => (
              <li key={changeIndex} className="flex items-start gap-2">
                <ChevronRight className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">{change}</span>
              </li>
            ))}
          </ul>
        </Card>
      ))}
    </div>
  );
}
