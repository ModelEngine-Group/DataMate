import { Card } from "antd";
import { AlertTriangle } from "lucide-react";

export default function DataQuality() {
  return (
    <div className=" mt-0">
      <div className="grid md:grid-cols-2 gap-6">
        <Card title="质量分布">
          {[
            { metric: "图像清晰度", value: 96.2, color: "bg-green-500" },
            { metric: "色彩一致性", value: 94.8, color: "bg-blue-500" },
            { metric: "标注完整性", value: 98.1, color: "bg-purple-500" },
          ].map((item, index) => (
            <div key={index} className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{item.metric}</span>
                <span className="font-semibold">{item.value}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`${item.color} h-3 rounded-full transition-all duration-500`}
                  style={{ width: `${item.value}%` }}
                ></div>
              </div>
            </div>
          ))}
        </Card>

        <Card title="数据完整性">
          {[
            { metric: "文件完整性", value: 99.7, color: "bg-green-500" },
            { metric: "元数据完整性", value: 97.3, color: "bg-blue-500" },
            { metric: "标签一致性", value: 95.6, color: "bg-purple-500" },
          ].map((item, index) => (
            <div key={index} className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{item.metric}</span>
                <span className="font-semibold">{item.value}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`${item.color} h-3 rounded-full transition-all duration-500`}
                  style={{ width: `${item.value}%` }}
                ></div>
              </div>
            </div>
          ))}
        </Card>
      </div>

      <Card className="bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200">
        <div className="flex items-start gap-4">
          <AlertTriangle className="w-6 h-6 text-yellow-600 mt-1 flex-shrink-0" />
          <div>
            <h4 className="font-semibold text-yellow-800 mb-2">质量改进建议</h4>
            <ul className="text-sm text-yellow-700 space-y-2">
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-yellow-600 rounded-full mt-2 flex-shrink-0"></span>
                建议对42张图像进行重新标注以提高准确性
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-yellow-600 rounded-full mt-2 flex-shrink-0"></span>
                检查并补充缺失的病理分级信息
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-yellow-600 rounded-full mt-2 flex-shrink-0"></span>
                考虑增加更多低分化样本以平衡数据分布
              </li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
}
