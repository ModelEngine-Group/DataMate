import React, { memo, useEffect, useState } from "react";
import { Button, Menu } from "antd";
import {
  CloseOutlined,
  MenuOutlined,
  OrderedListOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { Sparkles, X, Menu as MenuIcon } from "lucide-react";
import { antMenuItems, antMenuItems as items } from "@/pages/Layout/menu";
import TaskPopover from "../../components/TaskPopover";
import { NavLink, useLocation, useNavigate } from "react-router";

const AsiderAndHeaderLayout = () => {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [activeItem, setActiveItem] = useState<string>("management");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Initialize active item based on current pathname
  const initActiveItem = () => {
    for (let index = 0; index < antMenuItems.length; index++) {
      const element = antMenuItems[index];
      if (element.children) {
        element.children.forEach((subItem) => {
          if (pathname.includes(subItem.key)) {
            setActiveItem(subItem.key);
            return;
          }
        });
      } else if (pathname.includes(element.key)) {
        setActiveItem(element.key);
        return;
      }
    }
  };

  useEffect(() => {
    initActiveItem();
  }, [pathname]);

  return (
    <div
      className={`${
        sidebarOpen ? "w-64" : "w-20"
      } bg-white border-r border-gray-200 transition-all duration-300 flex flex-col`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        {sidebarOpen && (
          <NavLink to="/" className="flex items-center gap-2 cursor-pointer">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold text-gray-900">ModelEngine</span>
          </NavLink>
        )}
        <span className="cursor-pointer hover:text-blue-500" onClick={() => setSidebarOpen(!sidebarOpen)}>
          {sidebarOpen ? (
            <CloseOutlined />
          ) : (
            <MenuOutlined className="ml-4" />
          )}
        </span>
      </div>

      {/* Navigation */}
      <div className="flex-1">
        <Menu
          mode="inline"
          inlineCollapsed={!sidebarOpen}
          items={items}
          selectedKeys={[activeItem]}
          defaultOpenKeys={["synthesis"]}
          onClick={({ key }) => {
            setActiveItem(key);
            console.log(`/data/${key}`);
            navigate(`/data/${key}`);
          }}
        />
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        {sidebarOpen ? (
          <div className="space-y-2">
            {/* <TaskPopover /> */}
            <Button block onClick={() => navigate("/data/settings")}>
              设置
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            <Button block>
              <OrderedListOutlined />
            </Button>
            <Button block onClick={() => navigate("/data/settings")}>
              <SettingOutlined />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default memo(AsiderAndHeaderLayout);
