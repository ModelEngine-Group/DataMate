import { memo } from "react";
import { Outlet } from "react-router";
import Sidebar from "./Sidebar";
import Header from "./Header.tsx";

const MainLayout = () => {
  return (
    <div className="w-full h-screen flex flex-col bg-gray-50 min-w-6xl">
      <Header />
      <div className="w-full h-full flex">
        {/* Sidebar */}
        <Sidebar />
        {/* Main Content */}
        <div className="flex-overflow-auto p-6">
          {/* Content Area */}
          <div className="flex-overflow-auto">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
};

export default memo(MainLayout);
