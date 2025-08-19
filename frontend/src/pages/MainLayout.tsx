"use client";

import React, { memo } from "react";
import { Outlet } from "react-router";
import Sidebar from "@/components/Sidebar";
// import "./globals.css";

const MainLayout = () => {
  return (
    <div className="w-full h-screen flex flex-col bg-gray-50">
      <div className="w-full h-full flex">
        {/* Sidebar */}
        <Sidebar />
        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden p-6">
          {/* Content Area */}
          <div className="flex-1 overflow-auto">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
};

export default memo(MainLayout);
