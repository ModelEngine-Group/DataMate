import { Button, List, Tag } from "antd";
import { useNavigate } from "react-router";
import { Operator } from "../../operator.model";

export function ListView({ operators = [], pagination, operations }) {
  const navigate = useNavigate();

  const handleViewOperator = (operator: Operator) => {
    navigate(`/data/operator-market/plugin-detail/${operator.id}`);
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
                danger={operation.danger}
                onClick={() => operation.onClick(operator)}
              />
            )),
          ]}
        >
          <List.Item.Meta
            avatar={
              <div
                className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                  operator?.iconColor
                    ? ""
                    : "bg-gradient-to-br from-sky-300 to-blue-500"
                }`}
                style={
                  operator?.iconColor
                    ? { backgroundColor: operator.iconColor }
                    : undefined
                }
              >
                <div className="w-[2.8rem] h-[2.8rem] text-white">{operator?.icon}</div>
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
              </div>
            }
            description={
              <div className="space-y-2">
                <div className="text-gray-600 ">{operator.description}</div>
                {/* <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span>作者: {operator.author}</span>
                  <span>类型: {operator.type}</span>
                  <span>框架: {operator.framework}</span>
                  <span>使用次数: {operator?.usage?.toLocaleString()}</span>
                </div> */}
              </div>
            }
          />
        </List.Item>
      )}
    />
  );
}
