import React, { useEffect } from "react";

import { useState } from "react";
import {Card, Breadcrumb, message} from "antd";
import {
  DeleteOutlined, StarFilled,
  StarOutlined, UploadOutlined,
} from "@ant-design/icons";
import {Clock, GitBranch} from "lucide-react";
import DetailHeader from "@/components/DetailHeader";
import {Link, useNavigate, useParams} from "react-router";
import { useTranslation } from "react-i18next";
import Overview from "./components/Overview";
import Requirement from "./components/Requirement";
import Documentation from "./components/Documentation";
import ChangeLog from "./components/ChangeLog";
import OperatorServiceMonitor from "./components/OperatorServiceMonitor";

import {deleteOperatorByIdUsingDelete, queryOperatorByIdUsingGet, updateOperatorByIdUsingPut} from "../operator.api";
import { OperatorI } from "../operator.model";
import { mapOperator } from "../operator.const";

export default function OperatorPluginDetail() {
  const { t } = useTranslation();
  const { id } = useParams(); // 获取动态路由参数
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("overview");
  const [isStar, setIsStar] = useState(false);
  const [operator, setOperator] = useState<OperatorI | null>(null);

  const fetchOperator = async () => {
    try {
      const { data } = await queryOperatorByIdUsingGet(id as unknown as number);
      setOperator(mapOperator(data, t))
      setIsStar(data.isStar)
    } catch (error) {
      setOperator("error");
    }
  };

  useEffect(() => {
    fetchOperator();
  }, [id]);

  if (!operator) {
    return <div>Loading...</div>;
  }

  if (operator === "error") {
    return (
      <div className="text-red-500">
        Failed to load operator details. Please try again later.
      </div>
    );
  }

  const handleStar = async () => {
    const data = {
      id: operator.id,
      isStar: !isStar
    };
    await updateOperatorByIdUsingPut(operator.id, data)
    setIsStar(!isStar)
  }

  const handleDelete = async () => {
    await deleteOperatorByIdUsingDelete(operator.id);
    navigate("/data/operator-market");
    message.success(t("operatorMarket.detail.operations.messages.deleteSuccess"));
  };

  // 模拟算子数据
  const statistics = [
    {
      icon: <GitBranch className="text-blue-400 w-4 h-4" />,
      label: "",
      value: "v" + operator?.version,
    },
    {
      icon: <Clock className="text-blue-400 w-4 h-4" />,
      label: "",
      value: operator?.updatedAt,
    },
  ];

  const operations = [
    {
      key: "favorite",
      label: t("operatorMarket.detail.operations.favorite"),
      icon: (isStar ? (
          <StarFilled style={{ color: '#f59e0b' }} />
        ) : (
          <StarOutlined />
        )
      ),
      onClick: handleStar,
    },
    {
      key: "update",
      label: t("operatorMarket.detail.operations.update"),
      icon: <UploadOutlined />,
      onClick: () => navigate("/data/operator-market/create/" + operator.id),
    },
    {
      key: "delete",
      label: t("operatorMarket.detail.operations.delete"),
      danger: true,
      confirm: {
        title: t("operatorMarket.detail.operations.confirm.title"),
        description: t("operatorMarket.detail.operations.confirm.description"),
        okText: t("operatorMarket.detail.operations.confirm.okText"),
        cancelText: t("operatorMarket.detail.operations.confirm.cancelText"),
        okType: "danger"
      },
      icon: <DeleteOutlined />,
      onClick: handleDelete,
    },
  ];

  return (
    <div className="min-h-screen flex flex-col gap-4">
      {/* Header */}
      <Breadcrumb
        items={[
          {
            title: <Link to="/data/operator-market">{t("operatorMarket.detail.breadcrumb.market")}</Link>,
            href: "/data/operator-market",
          },
          {
            title: operator?.name,
          },
        ]}
      />
      <DetailHeader
        data={operator}
        statistics={statistics}
        operations={operations}
      />
      <Card
        tabList={[
          {
            key: "overview",
            label: t("operatorMarket.detail.tabs.overview"),
          },
          {
            key: "requirement",
            label: t("operatorMarket.detail.tabs.requirement"),
          },
          {
            key: "documentation",
            label: t("operatorMarket.detail.tabs.documentation"),
          },
          {
            key: "changeLog",
            label: t("operatorMarket.detail.tabs.changeLog"),
          },
          // {
          //   key: "service",
          //   label: "服务监控",
          // },
        ]}
        activeTabKey={activeTab}
        onTabChange={setActiveTab}
      >
        {activeTab === "overview" && <Overview operator={operator} />}
        {activeTab === "requirement" && <Requirement operator={operator} />}
        {activeTab === "documentation" && <Documentation operator={operator} />}
        {activeTab === "changeLog" && <ChangeLog operator={operator} />}
        {activeTab === "service" && <OperatorServiceMonitor operatorName={operator.name} supportsService={true} />}
      </Card>
    </div>
  );
}
