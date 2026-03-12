import { Card, Button } from "antd";
import { Copy } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function Requirement({ operator }) {
  const { t } = useTranslation();

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // 这里可以添加提示消息
  };

  let requirement = [];
  try {
    requirement = JSON.parse(operator.runtime || "{}");
  } catch (e) {
    console.error(t("operatorMarket.detail.requirement.parseError"), e);
  }

  return (
    <div className="flex flex-col gap-4">
      {/* 系统要求 */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{t("operatorMarket.detail.requirement.systemRequirements")}</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-700">{t("operatorMarket.detail.requirement.cpuSpec")}</span>
            <span className="text-gray-900">
              {requirement?.cpu || t("operatorMarket.detail.requirement.noLimit")}
            </span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-700">{t("operatorMarket.detail.requirement.memorySpec")}</span>
            <span className="text-gray-900">
              {requirement?.memory || t("operatorMarket.detail.requirement.noLimit")}
            </span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-700">{t("operatorMarket.detail.requirement.storage")}</span>
            <span className="text-gray-900">
              {requirement?.storage || t("operatorMarket.detail.requirement.noLimit")}
            </span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="font-medium text-gray-700">{t("operatorMarket.detail.requirement.gpuSupport")}</span>
            <span className="text-gray-900">
              {requirement?.gpu > 0 ? t("common.yes") : t("common.no")}
            </span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="font-medium text-gray-700">{t("operatorMarket.detail.requirement.npuSupport")}</span>
            <span className="text-gray-900">
              {requirement?.npu > 0 ? t("common.yes") : t("common.no")}
            </span>
          </div>
        </div>
      </Card>

      {/* 依赖项 */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{t("operatorMarket.detail.requirement.dependencies")}</h3>
        <div className="space-y-2">
          {operator.requirements?.map((dep, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <span className="font-mono text-sm text-gray-900">{dep}</span>
              <Button size="small" onClick={() => copyToClipboard(dep)}>
                <Copy className="w-3 h-3" />
              </Button>
            </div>
          ))}
        </div>
      </Card>

    </div>
  );
}
