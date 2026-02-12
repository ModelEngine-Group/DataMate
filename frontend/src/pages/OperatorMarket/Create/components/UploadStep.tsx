import { Spin } from "antd";
import { Upload, FileText } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function UploadStep({ isUploading, onUpload }) {
  const { t } = useTranslation();
  const supportedFormats = [
    { ext: ".zip", desc: t("operatorMarket.create.upload.formats.zip") },
    { ext: ".tar", desc: t("operatorMarket.create.upload.formats.tar") },
  ];

  return (
    <div className="py-2 w-full text-center">
      <div className="w-24 h-24 mx-auto mb-6 bg-blue-50 rounded-full flex items-center justify-center">
        <Upload className="w-12 h-12 text-blue-500" />
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">{t("operatorMarket.create.upload.title")}</h2>
      <p className="text-gray-600 mb-8">
        {t("operatorMarket.create.upload.description")}
      </p>

      {/* 支持的格式 */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {t("operatorMarket.create.upload.supportedFormats")}
        </h3>
        <div className="flex gap-4">
          {supportedFormats.map((format, index) => (
            <div key={index} className="p-3 border border-gray-200 rounded-lg flex-1">
              <div className="font-medium text-gray-900">{format.ext}</div>
              <div className="text-sm text-gray-500">{format.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 文件上传区域 */}
      <div
        className="border-2 border-dashed border-gray-300 rounded-lg p-8 hover:border-blue-400 transition-colors cursor-pointer"
        onDrop={(e) => {
          e.preventDefault();
          const files = e.dataTransfer.files;
          if (files.length > 0) {
            onUpload(files);
          }
        }}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => {
          const input = document.createElement("input");
          input.type = "file";
          input.multiple = false;
          input.accept = supportedFormats.map((f) => f.ext).join(",");
          input.onchange = (e) => {
            const files = (e.target as HTMLInputElement).files;
            if (files) {
              onUpload(files);
            }
          };
          input.click();
        }}
      >
        {isUploading ? (
          <div className="flex flex-col items-center">
            <Spin size="large" />
            <p className="mt-4 text-gray-600">{t("operatorMarket.create.upload.uploadArea.uploading")}</p>
          </div>
        ) : (
          <div>
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-lg text-gray-600 mb-2">
              {t("operatorMarket.create.upload.uploadArea.dragDrop")}
            </p>
            <p className="text-sm text-gray-500">
              {t("operatorMarket.create.upload.uploadArea.onlySingle")}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
