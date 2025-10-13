import { Button } from "antd";
import { ArrowLeft } from "lucide-react";
import OperatorUpload from "./components/OperatorUpload";
import { useNavigate } from "react-router";

export default function OperatorPluginCreate() {
  const navigate = useNavigate();
  return (
    <div className="h-screen bg-gray-50">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button type="text" onClick={() => navigate("/data/operator-market")}>
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <h1 className="text-xl font-bold text-gray-900">上传算子</h1>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <OperatorUpload />
      </div>
    </div>
  );
}
