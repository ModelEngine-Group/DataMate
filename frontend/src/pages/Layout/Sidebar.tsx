import { memo, useEffect, useState } from "react";
import { Button, Drawer, Menu, Popover } from "antd";
import {
  CloseOutlined,
  MenuOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { ClipboardList, Sparkles, X } from "lucide-react";
import { menuItems } from "@/pages/Layout/menu";
import { NavLink, useLocation, useNavigate } from "react-router";
import TaskUpload from "./TaskUpload";
import SettingsPage from "../SettingsPage/SettingsPage";

const AsiderAndHeaderLayout = () => {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [activeItem, setActiveItem] = useState<string>("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [taskCenterVisible, setTaskCenterVisible] = useState(false);
  const [settingVisible, setSettingVisible] = useState(false);

  // Initialize active item based on current pathname
  const initActiveItem = () => {
    for (let index = 0; index < menuItems.length; index++) {
      const element = menuItems[index];
      if (element.children) {
        element.children.forEach((subItem) => {
          if (pathname.includes(subItem.id)) {
            setActiveItem(subItem.id);
            return;
          }
        });
      } else if (pathname.includes(element.id)) {
        setActiveItem(element.id);
        return;
      }
    }
    console.log(pathname);
  };

  useEffect(() => {
    initActiveItem();
  }, [pathname]);

  useEffect(() => {
    const handleShowTaskPopover = (event: CustomEvent) => {
      const { show } = event.detail;
      setTaskCenterVisible(show);
    };

    window.addEventListener(
      "show:task-popover",
      handleShowTaskPopover as EventListener
    );

    return () => {
      window.removeEventListener(
        "show:task-popover",
        handleShowTaskPopover as EventListener
      );
    };
  }, []);

  return (
    <div
      className={`${
        sidebarOpen ? "w-64" : "w-20"
      } bg-white border-r border-gray-200 transition-all duration-300 flex flex-col relative`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        {sidebarOpen && (
          <NavLink to="/" className="flex items-center gap-2 cursor-pointer">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold text-gray-900">DataMate</span>
          </NavLink>
        )}
        <span
          className="cursor-pointer hover:text-blue-500"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          {sidebarOpen ? <CloseOutlined /> : <MenuOutlined className="ml-4" />}
        </span>
      </div>

      {/* Navigation */}
      <div className="flex-1">
        <Menu
          mode="inline"
          inlineCollapsed={!sidebarOpen}
          items={menuItems.map((item) => ({
            key: item.id,
            label: item.title,
            icon: item.icon ? <item.icon className="w-4 h-4" /> : null,
            children: item.children
              ? item.children.map((subItem) => ({
                  key: subItem.id,
                  label: subItem.title,
                  icon: subItem.icon ? (
                    <subItem.icon className="w-4 h-4" />
                  ) : null,
                }))
              : undefined,
          }))}
          selectedKeys={[activeItem]}
          defaultOpenKeys={["synthesis"]}
          onClick={({ key }) => {
            setActiveItem(key);
            navigate(`/data/${key}`);
          }}
        />
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        {sidebarOpen ? (
          <div className="space-y-2">
            <Popover
              forceRender
              title={
                <div className="flex items-center justify-between gap-2 border-b border-gray-200 pb-2 mb-2">
                  <h4 className="font-bold">任务中心</h4>
                  <X
                    onClick={() => setTaskCenterVisible(false)}
                    className="cursor-pointer w-4 h-4 text-gray-500 hover:text-gray-900"
                  />
                </div>
              }
              open={taskCenterVisible}
              content={<TaskUpload />}
              trigger="click"
              destroyOnHidden={false}
            >
              <Button block onClick={() => setTaskCenterVisible(true)}>
                任务中心
              </Button>
            </Popover>
            <Button
              block
              onClick={() => {
                setSettingVisible(true);
              }}
            >
              设置
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="relative">
              <Popover
                forceRender
                title="任务中心"
                open={taskCenterVisible}
                content={<TaskUpload />}
                trigger="click"
                destroyOnHidden={false}
              >
                <Button
                  block
                  onClick={() => setTaskCenterVisible(true)}
                  icon={<ClipboardList className="w-4 h-4" />}
                ></Button>
              </Popover>
            </div>
            <Button
              block
              onClick={() => {
                setSettingVisible(true);
              }}
            >
              <SettingOutlined />
            </Button>
          </div>
        )}
      </div>
      <Drawer
        title="设置"
        placement="bottom"
        width="100%"
        height="100%"
        open={settingVisible}
        onClose={() => setSettingVisible(false)}
        bodyStyle={{ padding: 0 }}
        destroyOnHidden={true}
      >
        <SettingsPage></SettingsPage>
      </Drawer>
      {/* 添加遮罩层，点击外部区域时关闭 */}
      {taskCenterVisible && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => {
            setTaskCenterVisible(false);
          }}
        />
      )}
    </div>
  );
};

export default memo(AsiderAndHeaderLayout);
