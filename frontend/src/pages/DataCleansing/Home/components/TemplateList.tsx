import { DeleteOutlined } from "@ant-design/icons";
import CardView from "@/components/CardView";
import {
  deleteCleaningTemplateByIdUsingDelete,
  queryCleaningTemplatesUsingGet,
} from "../../cleansing.api";
import useFetchData from "@/hooks/useFetchData";
import { mapTemplate } from "../../cleansing.const";
import { App } from "antd";
import { CleansingTemplate } from "../../cleansing.model";

export default function TemplateList() {
  const { message } = App.useApp();

  const { tableData, pagination, fetchData } = useFetchData(
    queryCleaningTemplatesUsingGet,
    mapTemplate
  );

  const deleteTemplate = async (template: CleansingTemplate) => {
    if (!template.id) {
      return;
    }
    // 实现删除逻辑
    await deleteCleaningTemplateByIdUsingDelete(template.id);
    fetchData();
    message.success("模板删除成功");
  };

  const operations = [
    {
      key: "delete",
      label: "删除模板",
      danger: true,
      icon: <DeleteOutlined />,
      onClick: (template: CleansingTemplate) => deleteTemplate(template), // 可实现删除逻辑
    },
  ];

  return (
    <CardView
      data={tableData}
      operations={operations}
      pagination={pagination}
    />
  );
}
