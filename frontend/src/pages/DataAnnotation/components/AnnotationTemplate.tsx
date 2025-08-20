import { useState } from "react";
import {
  Modal,
  Button,
  Input,
  Badge,
  Card,
  message,
  Divider,
  Radio,
  Form,
} from "antd";
import {
  SettingOutlined,
  CodeOutlined,
  SaveOutlined,
  CloseOutlined,
  AppstoreOutlined,
  BorderOutlined,
  DotChartOutlined,
  EditOutlined,
  CheckSquareOutlined,
  BarsOutlined,
  DeploymentUnitOutlined,
  AimOutlined,
  TableOutlined,
  ThunderboltOutlined,
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

const sidebarItems = [
  { id: "general", label: "通用", icon: <SettingOutlined /> },
  { id: "interface", label: "标注接口", icon: <CodeOutlined /> },
  { id: "annotation", label: "标注", icon: <AimOutlined /> },
  { id: "model", label: "Model", icon: <DeploymentUnitOutlined /> },
  { id: "prediction", label: "预测", icon: <ThunderboltOutlined /> },
  { id: "storage", label: "云存储", icon: <SaveOutlined /> },
  { id: "webhooks", label: "Webhooks", icon: <TableOutlined /> },
  { id: "danger", label: "危险区", icon: <CloseOutlined /> },
];

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

export function CustomTemplateDialog({
  open,
  onOpenChange,
  onSaveTemplate,
  datasetType,
}: CustomTemplateDialogProps) {
  const [activeSidebarItem, setActiveSidebarItem] = useState("interface");
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

  const filteredTools = annotationTools.filter(
    (tool) => tool.type === "both" || tool.type === datasetType
  );

  return (
    <Modal
      open={open}
      onCancel={() => onOpenChange(false)}
      footer={null}
      width={1200}
      bodyStyle={{ maxHeight: "80vh", overflow: "auto" }}
      title={
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span>自定义标注模板</span>
          <div>
            <Badge
              count={datasetType === "image" ? "图像模板" : "文本模板"}
              style={{ backgroundColor: "#52c41a", marginRight: 16 }}
            />
            <Button type="primary" icon={<SaveOutlined />} onClick={handleSave}>
              保存模板
            </Button>
          </div>
        </div>
      }
    >
      <div style={{ display: "flex", minHeight: 500 }}>
        {/* Sidebar */}
        <div
          style={{
            width: 160,
            borderRight: "1px solid #f0f0f0",
            paddingRight: 8,
          }}
        >
          {sidebarItems.map((item) => (
            <Button
              key={item.id}
              type={activeSidebarItem === item.id ? "primary" : "text"}
              icon={item.icon}
              block
              style={{ marginBottom: 8, textAlign: "left" }}
              onClick={() => setActiveSidebarItem(item.id)}
            >
              {item.label}
            </Button>
          ))}
        </div>
        {/* Main Content */}
        <div style={{ flex: 1, paddingLeft: 24 }}>
          {activeSidebarItem === "general" && (
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
          )}

          {activeSidebarItem === "interface" && (
            <div style={{ display: "flex", gap: 24 }}>
              <div style={{ flex: 1 }}>
                <div style={{ marginBottom: 8, fontWeight: 500 }}>代码</div>
                <Card>
                  <TextArea
                    rows={20}
                    value={templateCode}
                    onChange={(e) => setTemplateCode(e.target.value)}
                    placeholder="输入模板代码"
                  />
                </Card>
              </div>
              <div
                style={{
                  width: 400,
                  borderLeft: "1px solid #f0f0f0",
                  paddingLeft: 24,
                }}
              >
                <div style={{ marginBottom: 8, fontWeight: 500 }}>预览</div>
                <Card
                  cover={
                    <img
                      alt="预览图像"
                      src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/img_v3_02oi_9b855efe-ce37-4387-a845-d8ef9aaa1a8g.jpg-GhkhlenJlzOQLSDqyBm2iaC6jbv7VA.jpeg"
                      style={{ objectFit: "cover", height: 200 }}
                    />
                  }
                >
                  <div style={{ marginBottom: 8 }}>
                    <span style={{ color: "#888" }}>病例号：</span>
                    <span>undefined</span>
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <span style={{ color: "#888" }}>取材部位：</span>
                    <span>undefined</span>
                  </div>
                  <Divider />
                  <div>
                    <div style={{ fontWeight: 500, marginBottom: 8 }}>标注</div>
                    <div style={{ marginBottom: 8, color: "#888" }}>
                      是否有肿瘤
                    </div>
                    <Radio.Group>
                      <Radio value="1">是[1]</Radio>
                      <Radio value="0">否[2]</Radio>
                    </Radio.Group>
                    <div style={{ marginTop: 16 }}>
                      <div style={{ color: "#888", marginBottom: 4 }}>备注</div>
                      <TextArea rows={3} placeholder="添加备注..." />
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          )}

          {activeSidebarItem === "annotation" && (
            <div>
              <div style={{ fontWeight: 500, marginBottom: 16 }}>标注工具</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 16 }}>
                {filteredTools.map((tool) => (
                  <Card
                    key={tool.id}
                    hoverable
                    style={{ width: 120, textAlign: "center" }}
                  >
                    <div style={{ fontSize: 24, marginBottom: 8 }}>
                      {tool.icon}
                    </div>
                    <div>{tool.label}</div>
                  </Card>
                ))}
              </div>
              <Divider />
              <div style={{ fontWeight: 500, marginBottom: 8 }}>使用说明</div>
              <div style={{ color: "#888" }}>
                <div>• 拖拽工具到代码编辑器中使用</div>
                <div>• 每个工具都有对应的XML标签</div>
                <div>• 可以通过属性自定义工具行为</div>
              </div>
            </div>
          )}

          {!["general", "interface", "annotation"].includes(
            activeSidebarItem
          ) && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                height: 400,
                color: "#bbb",
                flexDirection: "column",
              }}
            >
              <SettingOutlined
                style={{ fontSize: 48, marginBottom: 16, opacity: 0.5 }}
              />
              <div>该功能正在开发中</div>
            </div>
          )}
        </div>
      </div>
      <Divider />
      <div style={{ color: "#888" }}>
        配置中的tag的标注接口， 查看所有可用标签说明
      </div>
    </Modal>
  );
}
