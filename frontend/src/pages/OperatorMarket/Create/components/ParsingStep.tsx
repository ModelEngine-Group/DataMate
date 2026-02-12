import { Progress } from "antd";
import { Settings, FileText, CheckCircle } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function ParsingStep({ parseProgress, uploadedFiles }) {
  const { t } = useTranslation();
  return (
    <div className="text-center py-2">
      <div className="w-24 h-24 mx-auto mb-6 bg-blue-50 rounded-full flex items-center justify-center">
        <Settings className="w-12 h-12 text-blue-500 animate-spin" />
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">
        {t("operatorMarket.create.parse.title")}
      </h2>
      <p className="text-gray-600 mb-8">
        {t("operatorMarket.create.parse.description")}
      </p>

      {/* 已上传文件列表 */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{t("operatorMarket.create.parse.uploadedFiles")}</h3>
        <div className="space-y-2">
          {uploadedFiles.map((file, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-gray-500" />
                <span className="font-medium">{file.name}</span>
                <span className="text-sm text-gray-500">
                  ({(file.size / 1024).toFixed(1)} KB)
                </span>
              </div>
              <CheckCircle className="w-5 h-5 text-green-500" />
            </div>
          ))}
        </div>
      </div>

      {/* 解析进度 */}
      <div className="max-w-md mx-auto">
        <Progress
          percent={parseProgress}
          status="active"
          strokeColor="#3B82F6"
        />
        <p className="mt-2 text-sm text-gray-600">{t("operatorMarket.create.parse.progress")}: {parseProgress}%</p>
      </div>
    </div>
  );
}
