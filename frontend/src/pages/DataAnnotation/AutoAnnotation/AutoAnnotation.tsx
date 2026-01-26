import { useState, useEffect } from "react";
import { Card, Button, Table, message, Modal, Tag, Progress, Space, Tooltip, Dropdown } from "antd";
import {
	PlusOutlined,
	DeleteOutlined,
	DownloadOutlined,
	ReloadOutlined,
	EyeOutlined,
	EditOutlined,
	MoreOutlined,
	SettingOutlined,
	ExportOutlined,
	ImportOutlined,
} from "@ant-design/icons";
import type { ColumnType } from "antd/es/table";
import type { AutoAnnotationTask, AutoAnnotationStatus } from "../annotation.model";
import {
	queryAutoAnnotationTasksUsingGet,
	deleteAutoAnnotationTaskByIdUsingDelete,
	downloadAutoAnnotationResultUsingGet,
  queryAnnotationTasksUsingGet,
  syncAutoAnnotationTaskToLabelStudioUsingPost,
} from "../annotation.api";
import CreateAutoAnnotationDialog from "./components/CreateAutoAnnotationDialog";
import EditAutoAnnotationDatasetDialog from "./components/EditAutoAnnotationDatasetDialog";
import ImportFromLabelStudioDialog from "./components/ImportFromLabelStudioDialog";

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
	const [labelStudioBase, setLabelStudioBase] = useState<string | null>(null);
	const [datasetProjectMap, setDatasetProjectMap] = useState<Record<string, string>>({});
	const [editingTask, setEditingTask] = useState<AutoAnnotationTask | null>(null);
	const [showEditDatasetDialog, setShowEditDatasetDialog] = useState(false);
	const [importingTask, setImportingTask] = useState<AutoAnnotationTask | null>(null);
	const [showImportDialog, setShowImportDialog] = useState(false);

	useEffect(() => {
		fetchTasks();
		const interval = setInterval(() => {
			fetchTasks(true);
		}, 3000);
		return () => clearInterval(interval);
	}, []);

	// 预取 Label Studio 基础 URL 和数据集到项目的映射
	useEffect(() => {
		let mounted = true;
		(async () => {
			try {
				const baseUrl = `http://${window.location.hostname}:${parseInt(window.location.port) + 1}`;
				if (mounted) setLabelStudioBase(baseUrl);
			} catch (e) {
				if (mounted) setLabelStudioBase(null);
			}

			// 拉取所有标注任务，构建 datasetId -> labelingProjId 映射
			try {
				const resp = await queryAnnotationTasksUsingGet({ page: 1, size: 1000 } as any);
				const content: any[] = (resp as any)?.data?.content || (resp as any)?.data || resp || [];
				const map: Record<string, string> = {};
				content.forEach((task: any) => {
					const datasetId = task.datasetId || task.dataset_id;
					const projId = task.labelingProjId || task.projId || task.labeling_project_id;
					if (datasetId && projId) {
						map[String(datasetId)] = String(projId);
					}
				});
				if (mounted) setDatasetProjectMap(map);
			} catch (e) {
				console.error("Failed to build dataset->LabelStudio project map:", e);
			}
		})();
		return () => {
			mounted = false;
		};
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

	const handleEditTaskDataset = (task: AutoAnnotationTask) => {
		setEditingTask(task);
		setShowEditDatasetDialog(true);
	};

	const handleImportFromLabelStudio = (task: AutoAnnotationTask) => {
		setImportingTask(task);
		setShowImportDialog(true);
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

	const handleSyncToLabelStudio = (task: AutoAnnotationTask) => {
		if (task.status !== "completed") {
			message.warning("仅已完成的任务可以同步到 Label Studio");
			return;
		}

		Modal.confirm({
			title: `确认同步自动标注任务「${task.name}」到 Label Studio 吗？`,
			content: (
				<div>
					<div>将把该任务的检测结果作为预测框写入 Label Studio。</div>
					<div>不会覆盖已有人工标注，仅作为可编辑的预测结果。</div>
				</div>
			),
			okText: "同步",
			cancelText: "取消",
			onOk: async () => {
				try {
					await syncAutoAnnotationTaskToLabelStudioUsingPost(task.id);
					message.success("同步请求已发送");
				} catch (error) {
					console.error(error);
					message.error("同步失败，请稍后重试");
				}
			},
		});
	};

	const handleAnnotate = (task: AutoAnnotationTask) => {
		const datasetId = task.datasetId;
		if (!datasetId) {
			message.error("该任务未绑定数据集，无法跳转 Label Studio");
			return;
		}

		const projId = datasetProjectMap[String(datasetId)];
		if (!projId) {
			message.error("未找到对应的标注工程，请先为该数据集创建手动标注任务");
			return;
		}

		if (!labelStudioBase) {
			message.error("无法跳转到 Label Studio：未配置 Label Studio 基础 URL");
			return;
		}

		const target = `${labelStudioBase}/projects/${projId}/data`;
		window.open(target, "_blank");
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
			width: 320,
			fixed: "right",
			render: (_: any, record: AutoAnnotationTask) => (
				<Space size="small">
					{/* 一级功能菜单：前向同步 + 编辑（跳转 Label Studio） */}
					<Tooltip title="将 YOLO 预测结果前向同步到 Label Studio">
						<Button
							type="link"
							size="small"
							icon={<ExportOutlined />}
							onClick={() => handleSyncToLabelStudio(record)}
						>
							前向同步
						</Button>
					</Tooltip>
					<Tooltip title="在 Label Studio 中手动标注">
						<Button
							type="link"
							size="small"
							icon={<EditOutlined />}
							onClick={() => handleAnnotate(record)}
						>
							编辑
						</Button>
					</Tooltip>
					<Tooltip title="从 Label Studio 导回标注结果到数据集">
						<Button
							type="link"
							size="small"
							icon={<ImportOutlined />}
							onClick={() => handleImportFromLabelStudio(record)}
						>
							后向同步
						</Button>
					</Tooltip>

					{/* 已完成任务的查看/下载结果仍保留 */}
					{record.status === "completed" && (
						<>
							<Tooltip title="查看结果信息">
								<Button
									type="link"
									size="small"
									icon={<EyeOutlined />}
									onClick={() => handleViewResult(record)}
								/>
							</Tooltip>
							<Tooltip title="下载标注结果 ZIP">
								<Button
									type="link"
									size="small"
									icon={<DownloadOutlined />}
									onClick={() => handleDownload(record)}
								/>
							</Tooltip>
						</>
					)}

					{/* 二级功能菜单：折叠的删除任务 + 编辑任务数据集 */}
					<Dropdown
						menu={{
							items: [
								{
									key: "edit-dataset",
									label: "编辑任务数据集",
									icon: <SettingOutlined />,
									onClick: () => handleEditTaskDataset(record),
								},
								{
									key: "delete",
									label: "删除任务",
									icon: <DeleteOutlined />,
									danger: true,
									onClick: () => handleDelete(record),
								},
							],
						}}
						trigger={["click"]}
					>
						<Button type="link" size="small" icon={<MoreOutlined />}
						>
							更多
						</Button>
					</Dropdown>
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

			{editingTask && (
				<EditAutoAnnotationDatasetDialog
					visible={showEditDatasetDialog}
					task={editingTask}
					onCancel={() => {
						setShowEditDatasetDialog(false);
						setEditingTask(null);
					}}
					onSuccess={() => {
						setShowEditDatasetDialog(false);
						setEditingTask(null);
						fetchTasks();
					}}
				/>
			)}

			{importingTask && (
				<ImportFromLabelStudioDialog
					visible={showImportDialog}
					task={importingTask}
					onCancel={() => {
						setShowImportDialog(false);
						setImportingTask(null);
					}}
					onSuccess={() => {
						setShowImportDialog(false);
						setImportingTask(null);
					}}
				/>
			)}
		</div>
	);
}