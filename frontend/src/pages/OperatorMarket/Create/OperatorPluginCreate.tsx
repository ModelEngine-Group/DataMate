import { Button, App, Steps } from "antd";
import {
  ArrowLeft,
  CheckCircle,
  Settings,
  TagIcon,
  Upload,
} from "lucide-react";
import { useNavigate, useParams } from "react-router";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import UploadStep from "./components/UploadStep";
import ParsingStep from "./components/ParsingStep";
import ConfigureStep from "./components/ConfigureStep";
import PreviewStep from "./components/PreviewStep";
import { useFileSliceUpload } from "@/hooks/useSliceUpload";
import {
  createOperatorUsingPost,
  preUploadOperatorUsingPost,
  queryOperatorByIdUsingGet,
  updateOperatorByIdUsingPut,
  uploadOperatorChunkUsingPost,
  uploadOperatorUsingPost,
} from "../operator.api";
import { sliceFile } from "@/utils/file.util";

export default function OperatorPluginCreate() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams();
  const { message } = App.useApp();
  const [uploadStep, setUploadStep] = useState<
    "upload" | "parsing" | "configure" | "preview"
  >(id ? "configure" : "upload");
  const [isUploading, setIsUploading] = useState(false);
  const [parsedInfo, setParsedInfo] = useState({});
  const [parseError, setParseError] = useState<string | null>(null);

  const { handleUpload, createTask, taskList } = useFileSliceUpload(
    {
      preUpload: preUploadOperatorUsingPost,
      uploadChunk: uploadOperatorChunkUsingPost,
      cancelUpload: null,
    },
    false
  );

  // 模拟文件上传
  const handleFileUpload = async (files: FileList) => {
    setIsUploading(true);
    setParseError(null);
    try {
      const fileName = files[0].name;
      const fileSize = files[0].size;
      await handleUpload({
        task: createTask({
          dataset: { id: "operator-upload", name: t("operatorMarket.create.title") },
        }),
        files: [
          {
            originFile: files[0],
            slices: sliceFile(files[0]),
            name: fileName,
            size: fileSize,
          },
        ], // 假设只上传一个文件
      });
      setParsedInfo({ ...parsedInfo, percent: 100 }); // 上传完成，进度100%
      // 解析文件过程
      const res = await uploadOperatorUsingPost({ fileName });
      const configs = res.data.settings && typeof res.data.settings === "string"
        ? JSON.parse(res.data.settings)
        : {};
      const defaultParams: Record<string, string> = {};
      Object.keys(configs).forEach((key) => {
        const { value } = configs[key];
        defaultParams[key] = value;
      });
      setParsedInfo({ ...res.data, fileName, fileSize, configs, defaultParams});
      setUploadStep("parsing");
    } catch (err) {
      setParseError(t("operatorMarket.create.messages.fileParseFailed") + " " + err.data.message);
    } finally {
      setIsUploading(false);
      setUploadStep("configure");
    }
  };

  const handlePublish = async () => {
    try {
      if (id) {
        await updateOperatorByIdUsingPut(id, parsedInfo!);
      } else {
        await createOperatorUsingPost(parsedInfo);
      }
      setUploadStep("preview");
    } catch (err) {
      message.error(t("operatorMarket.create.messages.publishFailed") + "，" + err.data.message);
    }
  };

  const onFetchOperator = async (operatorId: string) => {
    // 编辑模式，加载已有算子信息逻辑待实现
    const { data } = await queryOperatorByIdUsingGet(operatorId);
    const configs = data.settings && typeof data.settings === "string"
      ? JSON.parse(data.settings)
      : {};
    const defaultParams: Record<string, string> = {};
    Object.keys(configs).forEach((key) => {
      const { value } = configs[key];
      defaultParams[key] = value;
    });
    setParsedInfo({ ...data, configs, defaultParams});
    setUploadStep("configure");
  };

  useEffect(() => {
    if (id) {
      // 编辑模式，加载已有算子信息逻辑待实现
      onFetchOperator(id);
    }
  }, [id]);

  return (
    <div className="flex-overflow-auto bg-gray-50">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Button type="text" onClick={() => navigate("/data/operator-market")}>
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <h1 className="text-xl font-bold text-gray-900">
            {id ? t("operatorMarket.create.updateTitle") : t("operatorMarket.create.title")}
          </h1>
        </div>
        <div className="w-1/2">
          <Steps
            size="small"
            items={[
              {
                title: t("operatorMarket.create.steps.uploadFile"),
                icon: <Upload />,
              },
              {
                title: t("operatorMarket.create.steps.parseFile"),
                icon: <Settings />,
              },
              {
                title: t("operatorMarket.create.steps.configure"),
                icon: <TagIcon />,
              },
              {
                title: t("operatorMarket.create.steps.publish"),
                icon: <CheckCircle />,
              },
            ]}
            current={
              uploadStep === "upload"
                ? 0
                : uploadStep === "parsing"
                ? 1
                : uploadStep === "configure"
                ? 2
                : 3
            }
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-overflow-auto p-6 mt-4 bg-white border-card">
        <div className="flex-overflow-auto">
          {uploadStep === "upload" && (
            <UploadStep onUpload={handleFileUpload} isUploading={isUploading} />
          )}
          {uploadStep === "parsing" && (
            <ParsingStep
              parseProgress={taskList[0]?.percent || parsedInfo.percent || 0}
              uploadedFiles={taskList}
            />
          )}
          {uploadStep === "configure" && (
            <ConfigureStep
              setParsedInfo={setParsedInfo}
              parseError={parseError}
              parsedInfo={parsedInfo}
            />
          )}
          {uploadStep === "preview" && (
            <PreviewStep setUploadStep={setUploadStep} />
          )}
        </div>
        {uploadStep === "configure" && (
          <div className="flex justify-end gap-3 mt-8">
            <Button onClick={() => setUploadStep("upload")}>重新上传</Button>
            <Button type="primary" onClick={handlePublish}>
              {id ? "更新" : "发布"}算子
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
