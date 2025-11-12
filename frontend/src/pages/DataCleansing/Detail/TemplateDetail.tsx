import { useEffect, useState } from "react";
import {Breadcrumb, App, Tabs} from "antd";
import {
  Trash2,
  LayoutList,
} from "lucide-react";
import DetailHeader from "@/components/DetailHeader";
import { Link, useNavigate, useParams } from "react-router";
import {
  deleteCleaningTemplateByIdUsingDelete,
  queryCleaningTemplateByIdUsingGet,
} from "../cleansing.api";
import {mapTemplate} from "../cleansing.const";
import OperatorTable from "./components/OperatorTable";
import {EditOutlined, ReloadOutlined, NumberOutlined} from "@ant-design/icons";

// 任务详情页面组件
export default function CleansingTemplateDetail() {
  const { id = "" } = useParams(); // 获取动态路由参数
  const { message } = App.useApp();
  const navigate = useNavigate();
  const [template, setTemplate] = useState();

  const fetchTemplateDetail = async () => {
    if (!id) return;
    try {
      const { data } = await queryCleaningTemplateByIdUsingGet(id);
      setTemplate(mapTemplate(data));
    } catch (error) {
      message.error("获取任务详情失败");
      navigate("/data/cleansing");
    }
  };

  const deleteTemplate = async () => {
    await deleteCleaningTemplateByIdUsingDelete(id);
    message.success("模板已删除");
    navigate("/data/cleansing");
  };

  const handleRefresh = async () => {
    fetchTemplateDetail();
  };

  useEffect(() => {
    fetchTemplateDetail();
  }, [id]);

  const [activeTab, setActiveTab] = useState("operators");

  const headerData = {
    ...template,
    icon: <LayoutList className="w-8 h-8" />,
    createdAt: template?.createdAt,
    lastUpdated: template?.updatedAt,
  };

  const statistics = [
    {
      icon: <NumberOutlined className="w-4 h-4 text-green-500" />,
      label: "算子数量",
      value: template?.instance?.length || 0,
    },
  ];

  const operations = [
    {
      key: "update",
      label: "更新任务",
      icon: <EditOutlined className="w-4 h-4" />,
      onClick: () => navigate(`/data/cleansing/update-template/${id}`),
    },
    {
      key: "refresh",
      label: "更新任务",
      icon: <ReloadOutlined className="w-4 h-4" />,
      onClick: handleRefresh,
    },
    {
      key: "delete",
      label: "删除任务",
      icon: <Trash2 className="w-4 h-4" />,
      danger: true,
      onClick: deleteTemplate,
    },
  ];

  const tabList = [
    {
      key: "operators",
      label: "处理算子",
    },
  ];

  const breadItems = [
    {
      title: <Link to="/data/cleansing">数据清洗</Link>,
    },
    {
      title: "模板详情",
    },
  ];

  return (
    <>
      <Breadcrumb items={breadItems} />
      <div className="mb-4 mt-4">
        <DetailHeader
          data={headerData}
          statistics={statistics}
          operations={operations}
        />
      </div>
      <div className="flex-overflow-auto p-6 pt-2 bg-white rounded-md shadow">
        <Tabs activeKey={activeTab} items={tabList} onChange={setActiveTab} />
        <div className="h-full flex-1 overflow-auto">
          <OperatorTable task={template} />
        </div>
      </div>
    </>
  );
}
