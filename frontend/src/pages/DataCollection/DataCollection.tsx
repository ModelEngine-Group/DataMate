"use client"

import { useState } from "react"
import { Button, Card, Tabs } from "antd"
import { PlusOutlined } from "@ant-design/icons"
import TaskManagement from "./components/TaskManagement"
import ExecutionLog from "./components/ExecutionLog"
import { useNavigate } from "react-router"

export default function DataCollection() {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState("task-management")

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 mb-2">数据归集</h1>
                    <p className="text-gray-600">管理数据归集任务和查看执行日志</p>
                </div>
                <div>
                    <Button
                        type="primary"
                        onClick={() => navigate('/data/collection/task-create')}
                        icon={<PlusOutlined />}
                    >
                        创建任务
                    </Button>
                </div>
            </div>
            <Tabs activeKey={activeTab}
                items={[{ label: '任务管理', key: 'task-management' }, { label: '执行日志', key: 'execution-log' }]}
                onChange={(tab) => { setActiveTab(tab) }} />
            <Card>
                {activeTab === "task-management" ? (
                    <TaskManagement />
                ) : (
                    <ExecutionLog />
                )}
            </Card>
        </div >
    )
}
