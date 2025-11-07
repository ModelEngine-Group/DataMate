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
import Overview from "./components/Overview";
import Install from "./components/Install";

import {deleteOperatorByIdUsingDelete, queryOperatorByIdUsingGet, updateOperatorByIdUsingPut} from "../operator.api";
import { OperatorI } from "../operator.model";
import { mapOperator } from "../operator.const";

export default function OperatorPluginDetail() {
  const { id } = useParams(); // 获取动态路由参数
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("overview");
  const [isStar, setIsStar] = useState(false);
  const [operator, setOperator] = useState<OperatorI | null>(null);

  const fetchOperator = async () => {
    try {
      const { data } = await queryOperatorByIdUsingGet(id as unknown as number);
      setOperator(mapOperator(data));
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
    message.success("算子删除成功");
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
      label: "收藏",
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
      label: "更新",
      icon: <UploadOutlined />,
      onClick: () => navigate("/data/operator-market/create/" + operator.id),
    },
    {
      key: "delete",
      label: "删除",
      danger: true,
      confirm: {
        title: "确认删除当前算子？",
        description: "删除后该算子将无法恢复，请谨慎操作。",
        okText: "删除",
        cancelText: "取消",
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
            title: <Link to="/data/operator-market">算子市场</Link>,
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
            label: "概览",
          },
        ]}
        activeTabKey={activeTab}
        onTabChange={setActiveTab}
      >
        {activeTab === "overview" && <Overview operator={operator} />}
        {activeTab === "service" && <Install operator={operator} />}
      </Card>
    </div>
  );
}
