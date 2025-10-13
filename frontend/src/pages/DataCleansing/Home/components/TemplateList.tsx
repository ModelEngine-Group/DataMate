import {
  DeleteOutlined,
  EditOutlined,
  AppstoreOutlined,
} from "@ant-design/icons";
import CardView from "@/components/CardView";
import { queryCleaningTemplatesUsingGet } from "../../cleansing.api";
import { useNavigate } from "react-router";
import useFetchData from "@/hooks/useFetchData";
import { mapTemplate } from "../../cleansing.const";

export default function TemplateList() {
  const navigate = useNavigate();

  const { tableData, pagination } = useFetchData(
    queryCleaningTemplatesUsingGet,
    mapTemplate
  );

  const handleViewTemplate = (template: any) => {
    navigate("/data/cleansing/template-detail/" + template.id);
  };

  const useTemplate = (template: any) => {};

  const editTemplate = (template: any) => {};

  const DeleteTemplate = (template: any) => {
    // 实现删除逻辑
    console.log("删除模板", template);
  };

  const operations = [
    {
      key: "use",
      label: "使用模板",
      icon: <AppstoreOutlined />,
      onClick: useTemplate, // 可实现使用模板逻辑
    },
    {
      key: "edit",
      label: "编辑模板",
      icon: <EditOutlined />,
      onClick: editTemplate, // 可实现编辑逻辑
    },
    {
      key: "delete",
      label: "删除模板",
      icon: <DeleteOutlined />,
      onClick: DeleteTemplate, // 可实现删除逻辑
    },
  ];

  return (
    <CardView
      data={tableData}
      operations={operations}
      onView={handleViewTemplate}
      pagination={pagination}
    />
  );
}
