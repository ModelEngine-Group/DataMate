import { useState } from "react";
import {
  Modal,
  Input,
  Card,
  message,
  Divider,
  Radio,
  Form,
} from "antd";
import {
  AppstoreOutlined,
  BorderOutlined,
  DotChartOutlined,
  EditOutlined,
  CheckSquareOutlined,
  BarsOutlined,
  DeploymentUnitOutlined,
} from "@ant-design/icons";

interface CustomTemplateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaveTemplate: (templateData: any) => void;
  datasetType: "text" | "image";
}

const { TextArea } = Input;

const defaultImageTemplate = `<View style="display: flex; flex-direction: column; height: 100vh; overflow: auto;">
  <View style="display: flex; height: 100%; gap: 10px;">
    <View style="height: 100%; width: 85%; display: flex; flex-direction: column; gap: 5px;">
      <Header value="WSI图像预览" />
      <View style="min-height: 100%;">
        <Image name="image" value="$image" zoom="true" />
      </View>
    </View>
    <View style="height: 100%; width: auto;">
      <View style="width: auto; display: flex;">
        <Text name="case_id_title" toName="image" value="病例号: $case_id" />
      </View>
      <Text name="part_title" toName="image" value="取材部位: $part" />
      <Header value="标注" />
      <View style="display: flex; gap: 5px;">
        <View>
          <Text name="cancer_or_not_title" value="是否有肿瘤" />
          <Choices name="cancer_or_not" toName="image">
            <Choice value="是" alias="1" />
            <Choice value="否" alias="0" />
          </Choices>
          <Text name="remark_title" value="备注" />
          <TextArea name="remark" toName="image" editable="true"/>
        </View>
      </View>
    </View>
  </View>
</View>`;

const defaultTextTemplate = `<View style="display: flex; flex-direction: column; height: 100vh;">
  <Header value="文本标注界面" />
  <View style="display: flex; height: 100%; gap: 10px;">
    <View style="flex: 1; padding: 10px;">
      <Text name="content" value="$text" />
      <Labels name="label" toName="content">
        <Label value="正面" background="green" />
        <Label value="负面" background="red" />
        <Label value="中性" background="gray" />
      </Labels>
    </View>
    <View style="width: 300px; padding: 10px; border-left: 1px solid #ccc;">
      <Header value="标注选项" />
      <Text name="sentiment_title" value="情感分类" />
      <Choices name="sentiment" toName="content">
        <Choice value="正面" />
        <Choice value="负面" />
        <Choice value="中性" />
      </Choices>
      <Text name="confidence_title" value="置信度" />
      <Rating name="confidence" toName="content" maxRating="5" />
      <Text name="comment_title" value="备注" />
      <TextArea name="comment" toName="content" placeholder="添加备注..." />
    </View>
  </View>
</View>`;

const annotationTools = [
  { id: "rectangle", label: "矩形框", icon: <BorderOutlined />, type: "image" },
  {
    id: "polygon",
    label: "多边形",
    icon: <DeploymentUnitOutlined />,
    type: "image",
  },
  { id: "circle", label: "圆形", icon: <DotChartOutlined />, type: "image" },
  { id: "point", label: "关键点", icon: <AppstoreOutlined />, type: "image" },
  { id: "text", label: "文本", icon: <EditOutlined />, type: "both" },
  { id: "choices", label: "选择题", icon: <BarsOutlined />, type: "both" },
  {
    id: "checkbox",
    label: "多选框",
    icon: <CheckSquareOutlined />,
    type: "both",
  },
  { id: "textarea", label: "文本域", icon: <BarsOutlined />, type: "both" },
];

export default function CustomTemplateDialog({
  open,
  onOpenChange,
  onSaveTemplate,
  datasetType,
}: CustomTemplateDialogProps) {
  const [templateName, setTemplateName] = useState("");
  const [templateDescription, setTemplateDescription] = useState("");
  const [templateCode, setTemplateCode] = useState(
    datasetType === "image" ? defaultImageTemplate : defaultTextTemplate
  );

  const handleSave = () => {
    if (!templateName.trim()) {
      message.error("请输入模板名称");
      return;
    }
    if (!templateCode.trim()) {
      message.error("请输入模板代码");
      return;
    }
    const templateData = {
      id: `custom-${Date.now()}`,
      name: templateName,
      description: templateDescription,
      code: templateCode,
      type: datasetType,
      isCustom: true,
    };
    onSaveTemplate(templateData);
    onOpenChange(false);
    message.success("自定义模板已保存");
    setTemplateName("");
    setTemplateDescription("");
    setTemplateCode(
      datasetType === "image" ? defaultImageTemplate : defaultTextTemplate
    );
  };

  return (
    <Modal
      open={open}
      onCancel={() => onOpenChange(false)}
      okText={"保存模板"}
      onOk={handleSave}
      width={1200}
      className="max-h-[80vh] overflow-auto"
      title="自定义标注模板"
    >
      <div className="flex min-h-[500px]">
        <div className="flex-1 pl-6">
          <Form layout="vertical">
            <Form.Item label="模板名称 *" required>
              <Input
                placeholder="输入模板名称"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
              />
            </Form.Item>
            <Form.Item label="模板描述">
              <Input
                placeholder="输入模板描述"
                value={templateDescription}
                onChange={(e) => setTemplateDescription(e.target.value)}
              />
            </Form.Item>
          </Form>
          <div className="flex gap-6">
            <div className="flex-1">
              <div className="mb-2 font-medium">代码</div>
              <Card>
                <TextArea
                  rows={20}
                  value={templateCode}
                  onChange={(e) => setTemplateCode(e.target.value)}
                  placeholder="输入模板代码"
                />
              </Card>
            </div>
            <div className="w-96 border-l border-gray-100 pl-6">
              <div className="mb-2 font-medium">预览</div>
              <Card
                cover={
                  <img
                    alt="预览图像"
                    src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/img_v3_02oi_9b855efe-ce37-4387-a845-d8ef9aaa1a8g.jpg-GhkhlenJlzOQLSDqyBm2iaC6jbv7VA.jpeg"
                    className="object-cover h-48"
                  />
                }
              >
                <div className="mb-2">
                  <span className="text-gray-500">病例号：</span>
                  <span>undefined</span>
                </div>
                <div className="mb-2">
                  <span className="text-gray-500">取材部位：</span>
                  <span>undefined</span>
                </div>
                <Divider />
                <div>
                  <div className="font-medium mb-2">标注</div>
                  <div className="mb-2 text-gray-500">是否有肿瘤</div>
                  <Radio.Group>
                    <Radio value="1">是[1]</Radio>
                    <Radio value="0">否[2]</Radio>
                  </Radio.Group>
                  <div className="mt-4">
                    <div className="text-gray-500 mb-1">备注</div>
                    <TextArea rows={3} placeholder="添加备注..." />
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
}
