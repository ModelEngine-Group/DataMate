import { Button, List, Tag, Badge } from "antd";
import { StarFilled } from "@ant-design/icons";
import { Zap, Settings, X } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router";
import { Operator } from "../../operator.model";

export function ListView({ operators = [], pagination, operations }) {
  const navigate = useNavigate();
  const [favoriteOperators, setFavoriteOperators] = useState<Set<number>>(
    new Set([1, 3, 6])
  );
  const handleUpdateOperator = (operator: Operator) => {
    navigate(`/data/operator-market/create/${operator.id}`);
  };
  const handleViewOperator = (operator: Operator) => {
    navigate(`/data/operator-market/plugin-detail/${operator.id}`);
  };
  const handleToggleFavorite = (operatorId: number) => {
    setFavoriteOperators((prev) => {
      const newFavorites = new Set(prev);
      if (newFavorites.has(operatorId)) {
        newFavorites.delete(operatorId);
      } else {
        newFavorites.add(operatorId);
      }
      return newFavorites;
    });
  };
  const getStatusBadge = (status: string) => {
    const statusConfig = {
      active: {
        label: "活跃",
        color: "green",
        icon: <Zap className="w-3 h-3" />,
      },
      beta: {
        label: "测试版",
        color: "blue",
        icon: <Settings className="w-3 h-3" />,
      },
      deprecated: {
        label: "已弃用",
        color: "gray",
        icon: <X className="w-3 h-3" />,
      },
    };
    return (
      statusConfig[status as keyof typeof statusConfig] || statusConfig.active
    );
  };

  return (
    <List
      className="p-4 flex-1 overflow-auto mx-4"
      dataSource={operators}
      pagination={pagination}
      renderItem={(operator) => (
        <List.Item
          className="hover:bg-gray-50 transition-colors px-6 py-4"
          actions={[
            // <Button
            //   key="favorite"
            //   type="text"
            //   size="small"
            //   onClick={() => handleToggleFavorite(operator.id)}
            //   className={
            //     favoriteOperators.has(operator.id)
            //       ? "text-yellow-500 hover:text-yellow-600"
            //       : "text-gray-400 hover:text-yellow-500"
            //   }
            //   icon={
            //     <StarFilled
            //       style={{
            //         fontSize: "16px",
            //         color: favoriteOperators.has(operator.id)
            //           ? "#ffcc00ff"
            //           : "#d1d5db",
            //         cursor: "pointer",
            //       }}
            //       onClick={() => handleToggleFavorite(operator.id)}
            //     />
            //   }
            //   title="收藏"
            // />,
            ...operations.map((operation) => (
              <Button
                type="text"
                size="small"
                title={operation.label}
                icon={operation.icon}
                onClick={() => operation.onClick(operator)}
              />
            )),
          ]}
        >
          <List.Item.Meta
            avatar={
              <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-blue-200 rounded-lg flex items-center justify-center">
                {operator?.icon}
              </div>
            }
            title={
              <div className="flex items-center gap-3">
                <span
                  className="font-medium text-gray-900 cursor-pointer hover:text-blue-600"
                  onClick={() => handleViewOperator(operator)}
                >
                  {operator.name}
                </span>
                <Tag color="default">v{operator.version}</Tag>
                <Badge color={getStatusBadge(operator.status).color}>
                  {getStatusBadge(operator.status).label}
                </Badge>
              </div>
            }
            description={
              <div className="space-y-2">
                <div className="text-gray-600 ">{operator.description}</div>
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span>作者: {operator.author}</span>
                  <span>类型: {operator.type}</span>
                  <span>框架: {operator.framework}</span>
                  <span>使用次数: {operator?.usage?.toLocaleString()}</span>
                </div>
              </div>
            }
          />
        </List.Item>
      )}
    />
  );
}
