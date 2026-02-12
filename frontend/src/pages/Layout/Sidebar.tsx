import { memo, useEffect, useState } from "react";
import { Button, Drawer, Menu, Popover } from "antd";
import {
  SettingOutlined,
} from "@ant-design/icons";
import { ClipboardList, X, ChevronRight, ChevronLeft } from "lucide-react";
import { menuItems } from "@/pages/Layout/Menu.tsx";
import { useLocation, useNavigate } from "react-router";
import TaskUpload from "./TaskUpload";
import SettingsPage from "../SettingsPage/SettingsPage";
import { useAppSelector, useAppDispatch } from "@/store/hooks";
import { showSettings, hideSettings } from "@/store/slices/settingsSlice";
import { useTranslation } from "react-i18next";

const AsiderAndHeaderLayout = () => {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [activeItem, setActiveItem] = useState<string>("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [taskCenterVisible, setTaskCenterVisible] = useState(false);
  const settingVisible = useAppSelector((state) => state.settings.visible);
  const dispatch = useAppDispatch();

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

      {/* Navigation */}
      <div className="flex-1">
        <Menu
          mode="inline"
          inlineCollapsed={!sidebarOpen}
          items={menuItems.map((item) => ({
            key: item.id,
            label: t(item.i18Key),
            icon: item.icon ? <item.icon className="w-4 h-4" /> : null,
            children: item.children
              ? item.children.map((subItem) => ({
                  key: subItem.id,
                  label: t(subItem.i18Key),
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
                  <h4 className="font-bold">{t("common.taskCenter.title")}</h4>
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
                {t("common.taskCenter.title")}
              </Button>
            </Popover>
            <Button
              block
              onClick={() => {
                dispatch(showSettings());
              }}
            >
              {t("common.settings.title")}
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="relative">
              <Popover
                forceRender
                title={t("common.taskCenter.title")}
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
                dispatch(showSettings());
              }}
            >
              <SettingOutlined />
            </Button>
          </div>
        )}
      </div>
      <Drawer
        title={t("common.settings.title")}
        placement="bottom"
        width="100%"
        height="100%"
        open={settingVisible}
        onClose={() => dispatch(hideSettings())}
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
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="absolute top-1/2 -right-3 -translate-y-1/2 z-10 flex h-6 w-6 items-center justify-center rounded-full bg-gray-600 text-white shadow-md hover:bg-gray-700 transition-colors"
        title={sidebarOpen ? t("common.actions.openSidebar") : t("common.actions.closeSidebar")}
      >
        {sidebarOpen ? <ChevronLeft className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
      </button>
    </div>
  );
};

export default memo(AsiderAndHeaderLayout);
