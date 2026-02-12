import { Button } from "antd";
import { CheckCircle, Plus } from "lucide-react";
import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";

export default function PreviewStep({ setUploadStep }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  return (
    <div className="text-center py-2">
      <div className="w-24 h-24 mx-auto mb-6 bg-green-50 rounded-full flex items-center justify-center">
        <CheckCircle className="w-12 h-12 text-green-500" />
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">{t("operatorMarket.create.preview.title")}</h2>
      <p className="text-gray-600 mb-8">{t("operatorMarket.create.preview.description")}</p>

      <div className="flex justify-center gap-4">
        <Button onClick={() => setUploadStep("upload")}>
          <Plus className="w-4 h-4 mr-2" />
          {t("operatorMarket.create.preview.continueUpload")}
        </Button>
        <Button type="primary" onClick={() => navigate("/data/operator-market")}>
          {t("operatorMarket.create.preview.backToHome")}
        </Button>
      </div>
    </div>
  );
}
