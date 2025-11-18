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
      await handleUpload({
        task: createTask({
          dataset: { id: "operator-upload", name: "上传算子" },
        }),
        files: [
          {
            originFile: files[0],
            slices: sliceFile(files[0]),
            name: fileName,
            size: files[0].size,
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
      setParsedInfo({ ...res.data, fileName, configs, defaultParams});
      setUploadStep("parsing");
    } catch (err) {
      setParseError("文件解析失败，" + err.data.message);
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
      message.error("算子发布失败，" + err.data.message);
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
            {id ? "更新算子" : "上传算子"}
          </h1>
        </div>
        <div className="w-1/2">
          <Steps
            size="small"
            items={[
              {
                title: "上传文件",
                icon: <Upload />,
              },
              {
                title: "解析文件",
                icon: <Settings />,
              },
              {
                title: "配置信息",
                icon: <TagIcon />,
              },
              {
                title: "发布完成",
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
