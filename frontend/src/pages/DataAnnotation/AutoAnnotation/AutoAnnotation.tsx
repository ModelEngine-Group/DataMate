import { useState, useEffect } from "react";
import { Card, Button, Table, message, Modal, Tag, Progress, Space, Tooltip } from "antd";
import {
	PlusOutlined,
	DeleteOutlined,
	DownloadOutlined,
	ReloadOutlined,
	EyeOutlined,
} from "@ant-design/icons";
import type { ColumnType } from "antd/es/table";
import type { AutoAnnotationTask, AutoAnnotationStatus } from "../annotation.model";
import {
	queryAutoAnnotationTasksUsingGet,
	deleteAutoAnnotationTaskByIdUsingDelete,
	downloadAutoAnnotationResultUsingGet,
} from "../annotation.api";
import CreateAutoAnnotationDialog from "./components/CreateAutoAnnotationDialog";

const STATUS_COLORS: Record<AutoAnnotationStatus, string> = {
	pending: "default",
	running: "processing",
	completed: "success",
	failed: "error",
	cancelled: "default",
};

const STATUS_LABELS: Record<AutoAnnotationStatus, string> = {
	pending: "等待中",
	running: "处理中",
	completed: "已完成",
	failed: "失败",
	cancelled: "已取消",
};

const MODEL_SIZE_LABELS: Record<string, string> = {
	n: "YOLOv8n (最快)",
	s: "YOLOv8s",
	m: "YOLOv8m",
	l: "YOLOv8l (推荐)",
	x: "YOLOv8x (最精确)",
};

export default function AutoAnnotation() {
	const [loading, setLoading] = useState(false);
	const [tasks, setTasks] = useState<AutoAnnotationTask[]>([]);
	const [showCreateDialog, setShowCreateDialog] = useState(false);
	const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);

	useEffect(() => {
		fetchTasks();
		const interval = setInterval(() => {
			fetchTasks(true);
		}, 3000);
		return () => clearInterval(interval);
	}, []);

	const fetchTasks = async (silent = false) => {
		if (!silent) setLoading(true);
		try {
			const response = await queryAutoAnnotationTasksUsingGet();
			setTasks(response.data || response || []);
		} catch (error) {
			console.error("Failed to fetch auto annotation tasks:", error);
			if (!silent) message.error("获取任务列表失败");
		} finally {
			if (!silent) setLoading(false);
		}
	};

	const handleDelete = (task: AutoAnnotationTask) => {
		Modal.confirm({
			title: `确认删除自动标注任务「${task.name}」吗？`,
			content: "删除任务后，已生成的标注结果不会被删除。",
			okText: "删除",
			okType: "danger",
			cancelText: "取消",
			onOk: async () => {
				try {
					await deleteAutoAnnotationTaskByIdUsingDelete(task.id);
					message.success("任务删除成功");
					fetchTasks();
					setSelectedRowKeys((keys) => keys.filter((k) => k !== task.id));
				} catch (error) {
					console.error(error);
					message.error("删除失败，请稍后重试");
				}
			},
		});
	};

	const handleDownload = async (task: AutoAnnotationTask) => {
		try {
			message.loading("正在准备下载...", 0);
			await downloadAutoAnnotationResultUsingGet(task.id);
			message.destroy();
			message.success("下载已开始");
		} catch (error) {
			console.error(error);
			message.destroy();
			message.error("下载失败");
		}
	};

	const handleViewResult = (task: AutoAnnotationTask) => {
		if (task.outputPath) {
			Modal.info({
				title: "标注结果路径",
				content: (
					<div>
						<p>输出路径：{task.outputPath}</p>
						<p>检测对象数：{task.detectedObjects}</p>
						<p>
							处理图片数：{task.processedImages} / {task.totalImages}
						</p>
					</div>
				),
			});
		}
	};

	const columns: ColumnType<AutoAnnotationTask>[] = [
		{ title: "任务名称", dataIndex: "name", key: "name", width: 200 },
		{
			title: "数据集",
			dataIndex: "datasetName",
			key: "datasetName",
			width: 220,
			render: (_: any, record: AutoAnnotationTask) => {
				const list =
					record.sourceDatasets && record.sourceDatasets.length > 0
						? record.sourceDatasets
						: record.datasetName
						? [record.datasetName]
						: [];

				if (list.length === 0) return "-";

				const text = list.join("，");
				return (
					<Tooltip title={text}>
						<span>{text}</span>
					</Tooltip>
				);
			},
		},
		{
			title: "模型",
			dataIndex: ["config", "modelSize"],
			key: "modelSize",
			width: 120,
			render: (size: string) => MODEL_SIZE_LABELS[size] || size,
		},
		{
			title: "置信度",
			dataIndex: ["config", "confThreshold"],
			key: "confThreshold",
			width: 100,
			render: (threshold: number) => `${(threshold * 100).toFixed(0)}%`,
		},
		{
			title: "目标类别",
			dataIndex: ["config", "targetClasses"],
			key: "targetClasses",
			width: 120,
			render: (classes: number[]) => (
				<Tooltip
					title={classes.length > 0 ? classes.join(", ") : "全部类别"}
				>
					<span>
						{classes.length > 0
							? `${classes.length} 个类别`
							: "全部类别"}
					</span>
				</Tooltip>
			),
		},
		{
			title: "状态",
			dataIndex: "status",
			key: "status",
			width: 100,
			render: (status: AutoAnnotationStatus) => (
				<Tag color={STATUS_COLORS[status]}>{STATUS_LABELS[status]}</Tag>
			),
		},
		{
			title: "进度",
			dataIndex: "progress",
			key: "progress",
			width: 150,
			render: (progress: number, record: AutoAnnotationTask) => (
				<div>
					<Progress percent={progress} size="small" />
					<div style={{ fontSize: "12px", color: "#999" }}>
						{record.processedImages} / {record.totalImages}
					</div>
				</div>
			),
		},
		{
			title: "检测对象数",
			dataIndex: "detectedObjects",
			key: "detectedObjects",
			width: 100,
			render: (count: number) => count.toLocaleString(),
		},
		{
			title: "创建时间",
			dataIndex: "createdAt",
			key: "createdAt",
			width: 150,
			render: (time: string) => new Date(time).toLocaleString(),
		},
		{
			title: "操作",
			key: "actions",
			width: 180,
			fixed: "right",
			render: (_: any, record: AutoAnnotationTask) => (
				<Space size="small">
					{record.status === "completed" && (
						<>
							<Tooltip title="查看结果">
								<Button
									type="link"
									size="small"
									icon={<EyeOutlined />}
									onClick={() => handleViewResult(record)}
								/>
							</Tooltip>
							<Tooltip title="下载结果">
								<Button
									type="link"
									size="small"
									icon={<DownloadOutlined />}
									onClick={() => handleDownload(record)}
								/>
							</Tooltip>
						</>
					)}
					<Tooltip title="删除">
						<Button
							type="link"
							size="small"
							danger
							icon={<DeleteOutlined />}
							onClick={() => handleDelete(record)}
						/>
					</Tooltip>
				</Space>
			),
		},
	];

	return (
		<div>
			<Card
				title="自动标注任务"
				extra={
					<Space>
						<Button
							type="primary"
							icon={<PlusOutlined />}
							onClick={() => setShowCreateDialog(true)}
						>
							创建任务
						</Button>
						<Button
							icon={<ReloadOutlined />}
							loading={loading}
							onClick={() => fetchTasks()}
						>
							刷新
						</Button>
					</Space>
				}
			>
				<Table
					rowKey="id"
					loading={loading}
					columns={columns}
					dataSource={tasks}
					rowSelection={{
						selectedRowKeys,
						onChange: (keys) => setSelectedRowKeys(keys as string[]),
					}}
					pagination={{ pageSize: 10 }}
					scroll={{ x: 1000 }}
				/>
			</Card>

			<CreateAutoAnnotationDialog
				visible={showCreateDialog}
				onCancel={() => setShowCreateDialog(false)}
				onSuccess={() => {
					setShowCreateDialog(false);
					fetchTasks();
				}}
			/>
		</div>
	);
}