import { useEffect, useState } from "react";
import {Breadcrumb, App, Tabs} from "antd";
import {
  Trash2,
  LayoutList,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import DetailHeader from "@/components/DetailHeader";
import { Link, useNavigate, useParams } from "react-router";
import {
  deleteCleaningTemplateByIdUsingDelete,
  queryCleaningTemplateByIdUsingGet,
} from "../cleansing.api";
import {mapTemplate} from "../cleansing.const";
import TemplateOperatorTable from "./components/TemplateOperatorTable";
import {EditOutlined, ReloadOutlined, NumberOutlined} from "@ant-design/icons";

// 任务详情页面组件
export default function CleansingTemplateDetail() {
  const { t } = useTranslation();
  const { id = "" } = useParams(); // 获取动态路由参数
  const { message } = App.useApp();
  const navigate = useNavigate();
  const [template, setTemplate] = useState();

  const fetchTemplateDetail = async () => {
    if (!id) return;
    try {
      const { data } = await queryCleaningTemplateByIdUsingGet(id);
      setTemplate(mapTemplate(data, t));
    } catch (error) {
      message.error(t("dataCleansing.template.messages.templateDetailFailed"));
      navigate("/data/cleansing");
    }
  };

  const deleteTemplate = async () => {
    await deleteCleaningTemplateByIdUsingDelete(id);
    message.success(t("dataCleansing.template.messages.templateDeleted"));
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
      label: t("dataCleansing.detail.statistics.operatorCount"),
      value: template?.instance?.length || 0,
    },
  ];

  const operations = [
    {
      key: "update",
      label: t("dataCleansing.actions.updateTemplate"),
      icon: <EditOutlined className="w-4 h-4" />,
      onClick: () => navigate(`/data/cleansing/update-template/${id}`),
    },
    {
      key: "refresh",
      label: t("dataCleansing.actions.refreshTemplate"),
      icon: <ReloadOutlined className="w-4 h-4" />,
      onClick: handleRefresh,
    },
    {
      key: "delete",
      label: t("dataCleansing.actions.deleteTemplate"),
      icon: <Trash2 className="w-4 h-4" />,
      danger: true,
      onClick: deleteTemplate,
    },
  ];

  const tabList = [
    {
      key: "operators",
      label: t("dataCleansing.detail.tabs.operators"),
    },
  ];

  const breadItems = [
    {
      title: <Link to="/data/cleansing">{t("dataCleansing.detail.breadcrumb.dataProcessing")}</Link>,
    },
    {
      title: t("dataCleansing.detail.breadcrumb.templateDetail"),
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
          <TemplateOperatorTable template={template} />
        </div>
      </div>
    </>
  );
}
