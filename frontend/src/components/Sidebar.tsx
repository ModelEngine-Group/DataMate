"use client";

import React, { memo, useState } from "react";
import { Button, Menu } from "antd";
import { Sparkles, X, Menu as MenuIcon } from "lucide-react";
import { antMenuItems as items } from "@/mock/menu";
import TaskPopover from "./TaskPopover";
import { NavLink, useLocation, useNavigate } from "react-router";

const AsiderAndHeaderLayout = () => {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [activeItem, setActiveItem] = useState<string>(
    pathname.split("/data/")[1] || "management"
  );
  const [sidebarOpen, setSidebarOpen] = useState(true);

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
        <Button
          type="text"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 hover:bg-gray-100"
        >
          {sidebarOpen ? (
            <X className="w-4 h-4" />
          ) : (
            <MenuIcon className="w-4 h-4" />
          )}
        </Button>
      </div>

      {/* Navigation */}
      <div className="flex-1">
        <Menu
          mode="inline"
          inlineCollapsed={!sidebarOpen}
          items={items}
          selectedKeys={[activeItem]}
          defaultOpenKeys={["data-synthesis"]}
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
            <TaskPopover />
            <Button className="w-full justify-start bg-transparent">
              设置
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            <Button className="w-full p-2">?</Button>
            <Button className="w-full p-2">⚙</Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default memo(AsiderAndHeaderLayout);
