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
	SyncOutlined,
} from "@ant-design/icons";
import type { ColumnType } from "antd/es/table";
import type { AutoAnnotationTask, AutoAnnotationStatus } from "../annotation.model";
import {
	queryAutoAnnotationTasksUsingGet,
	deleteAutoAnnotationTaskByIdUsingDelete,
	downloadAutoAnnotationResultUsingGet,
	queryAnnotationTasksUsingGet,
	syncAutoAnnotationToDatabaseUsingPost,
} from "../annotation.api";
import CreateAutoAnnotationDialog from "./components/CreateAutoAnnotationDialog";
import EditAutoAnnotationDatasetDialog from "./components/EditAutoAnnotationDatasetDialog";
import ImportFromLabelStudioDialog from "./components/ImportFromLabelStudioDialog";
import { useTranslation } from "react-i18next";

const STATUS_COLORS: Record<AutoAnnotationStatus, string> = {
	pending: "default",
	running: "processing",
	completed: "success",
	failed: "error",
	cancelled: "default",
};

export default function AutoAnnotation() {
	const { t } = useTranslation();
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
			if (!silent) message.error(t("dataAnnotation.autoAnnotation.messages.fetchTasksFailed"));
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

	const handleSyncToDatabase = (task: AutoAnnotationTask) => {
		Modal.confirm({
			title: t("dataAnnotation.autoAnnotation.messages.syncToDbTitle", { name: task.name }),
			content: (
				<div>
					<div>{t("dataAnnotation.autoAnnotation.messages.syncToDbContent1")}</div>
					<div>{t("dataAnnotation.autoAnnotation.messages.syncToDbContent2")}</div>
				</div>
			),
			okText: t("dataAnnotation.home.actions.syncToDb"),
			cancelText: t("dataAnnotation.home.confirm.deleteCancelText"),
			onOk: async () => {
				const hide = message.loading(t("dataAnnotation.autoAnnotation.messages.syncLoading"), 0);
				try {
					await syncAutoAnnotationToDatabaseUsingPost(task.id);
					hide();
					message.success(t("dataAnnotation.autoAnnotation.messages.syncSuccess"));
				} catch (e) {
					console.error(e);
					hide();
					message.error(t("dataAnnotation.autoAnnotation.messages.syncFailed"));
				}
			},
		});
	};

	const handleDelete = (task: AutoAnnotationTask) => {
		Modal.confirm({
			title: t("dataAnnotation.autoAnnotation.confirm.deleteTitle", { name: task.name }),
			content: t("dataAnnotation.autoAnnotation.confirm.deleteContent"),
			okText: t("dataAnnotation.autoAnnotation.confirm.deleteOkText"),
			okType: "danger",
			cancelText: t("dataAnnotation.autoAnnotation.confirm.deleteCancelText"),
			onOk: async () => {
				try {
					await deleteAutoAnnotationTaskByIdUsingDelete(task.id);
					message.success(t("dataAnnotation.autoAnnotation.messages.deleteSuccess"));
					fetchTasks();
					setSelectedRowKeys((keys) => keys.filter((k) => k !== task.id));
				} catch (error) {
					console.error(error);
					message.error(t("dataAnnotation.autoAnnotation.messages.deleteFailed"));
				}
			},
		});
	};

	const handleDownload = async (task: AutoAnnotationTask) => {
		try {
			message.loading(t("dataAnnotation.autoAnnotation.messages.downloadPreparing"), 0);
			await downloadAutoAnnotationResultUsingGet(task.id);
			message.destroy();
			message.success(t("dataAnnotation.autoAnnotation.messages.downloadStarted"));
		} catch (error) {
			console.error(error);
			message.destroy();
			message.error(t("dataAnnotation.autoAnnotation.messages.downloadFailed"));
		}
	};

	const handleAnnotate = (task: AutoAnnotationTask) => {
		const datasetId = task.datasetId;
		if (!datasetId) {
			message.error(t("dataAnnotation.autoAnnotation.messages.noDatasetBound"));
			return;
		}

		const projId = datasetProjectMap[String(datasetId)];
		if (!projId) {
			message.error(t("dataAnnotation.autoAnnotation.messages.noProjectFound"));
			return;
		}

		if (!labelStudioBase) {
			message.error(t("dataAnnotation.autoAnnotation.messages.cannotJumpNoBase"));
			return;
		}

		const target = `${labelStudioBase}/projects/${projId}/data`;
		window.open(target, "_blank");
	};

	const handleViewResult = (task: AutoAnnotationTask) => {
		if (task.outputPath) {
			Modal.info({
				title: t("dataAnnotation.autoAnnotation.messages.resultPathTitle"),
				content: (
					<div>
						<p>{t("dataAnnotation.autoAnnotation.messages.outputPath")}: {task.outputPath}</p>
						<p>{t("dataAnnotation.autoAnnotation.columns.detectedObjects")}: {task.detectedObjects}</p>
						<p>
							{t("dataAnnotation.autoAnnotation.messages.processedImages")}: {task.processedImages} / {task.totalImages}
						</p>
					</div>
				),
			});
		}
	};

	const columns: ColumnType<AutoAnnotationTask>[] = [
		{ title: t("dataAnnotation.autoAnnotation.columns.name"), dataIndex: "name", key: "name", width: 200 },
		{
			title: t("dataAnnotation.autoAnnotation.columns.dataset"),
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
			title: t("dataAnnotation.autoAnnotation.columns.modelSize"),
			dataIndex: ["config", "modelSize"],
			key: "modelSize",
			width: 120,
			render: (size: string) => t(`dataAnnotation.autoAnnotation.modelSizeLabels.${size}`) || size,
		},
		{
			title: t("dataAnnotation.autoAnnotation.columns.confThreshold"),
			dataIndex: ["config", "confThreshold"],
			key: "confThreshold",
			width: 100,
			render: (threshold: number) => `${(threshold * 100).toFixed(0)}%`,
		},
		{
			title: t("dataAnnotation.autoAnnotation.columns.targetClasses"),
			dataIndex: ["config", "targetClasses"],
			key: "targetClasses",
			width: 120,
			render: (classes: number[]) => (
				<Tooltip
					title={classes.length > 0 ? classes.join(", ") : t("dataAnnotation.home.allCategories")}
				>
					<span>
						{classes.length > 0
							? t("dataAnnotation.home.categoriesCount", { count: classes.length })
							: t("dataAnnotation.home.allCategories")}
					</span>
				</Tooltip>
			),
		},
		{
			title: t("dataAnnotation.autoAnnotation.columns.status"),
			dataIndex: "status",
			key: "status",
			width: 100,
			render: (status: AutoAnnotationStatus) => (
				<Tag color={STATUS_COLORS[status]}>{t(`dataAnnotation.autoAnnotation.statusLabels.${status}`)}</Tag>
			),
		},
		{
			title: t("dataAnnotation.autoAnnotation.columns.progress"),
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
			title: t("dataAnnotation.autoAnnotation.columns.detectedObjects"),
			dataIndex: "detectedObjects",
			key: "detectedObjects",
			width: 100,
			render: (count: number) => count.toLocaleString(),
		},
		{
			title: t("dataAnnotation.autoAnnotation.columns.createdAt"),
			dataIndex: "createdAt",
			key: "createdAt",
			width: 150,
			render: (time: string) => new Date(time).toLocaleString(),
		},
		{
			title: t("dataAnnotation.autoAnnotation.columns.actions"),
			key: "actions",
			width: 300,
			fixed: "right",
			render: (_: any, record: AutoAnnotationTask) => (
				<Space size="small">
					<Tooltip title={t("dataAnnotation.home.actions.annotate")}>
						<Button
							type="link"
							size="small"
							icon={<EditOutlined />}
							onClick={() => handleAnnotate(record)}
						>
							{t("dataAnnotation.home.actions.edit")}
						</Button>
					</Tooltip>
					<Tooltip title={t("dataAnnotation.autoAnnotation.actions.syncToDb")}>
						<Button
							type="link"
							size="small"
							icon={<SyncOutlined />}
							onClick={() => handleSyncToDatabase(record)}
						>
							{t("dataAnnotation.autoAnnotation.actions.syncToDb")}
						</Button>
					</Tooltip>

					{record.status === "completed" && (
						<>
							<Tooltip title={t("dataAnnotation.autoAnnotation.viewResult")}>
								<Button
									type="link"
									size="small"
									icon={<EyeOutlined />}
									onClick={() => handleViewResult(record)}
								/>
							</Tooltip>
							<Tooltip title={t("dataAnnotation.autoAnnotation.downloadResult")}>
								<Button
									type="link"
									size="small"
									icon={<DownloadOutlined />}
									onClick={() => handleDownload(record)}
								/>
							</Tooltip>
						</>
					)}

					<Dropdown
						menu={{
							items: [
								{
									key: "export-result",
									label: t("dataAnnotation.autoAnnotation.actions.exportResult"),
									icon: <DownloadOutlined />,
									onClick: () => handleImportFromLabelStudio(record),
								},
								{
									key: "edit-dataset",
									label: t("dataAnnotation.autoAnnotation.actions.editDataset"),
									icon: <SettingOutlined />,
									onClick: () => handleEditTaskDataset(record),
								},
								{
									key: "delete",
									label: t("dataAnnotation.autoAnnotation.actions.delete"),
									icon: <DeleteOutlined />,
									danger: true,
									onClick: () => handleDelete(record),
								},
							],
						}}
						trigger={["click"]}
					>
						<Button type="link" size="small" icon={<MoreOutlined />}>
							{t("dataAnnotation.autoAnnotation.more")}
						</Button>
					</Dropdown>
				</Space>
			),
		},
	];

	return (
		<div>
			<Card
				title={t("dataAnnotation.autoAnnotation.title")}
				extra={
					<Space>
						<Button
							type="primary"
							icon={<PlusOutlined />}
							onClick={() => setShowCreateDialog(true)}
						>
							{t("dataAnnotation.autoAnnotation.createTask")}
						</Button>
						<Button
							icon={<ReloadOutlined />}
							loading={loading}
							onClick={() => fetchTasks()}
						>
							{t("dataAnnotation.autoAnnotation.refresh")}
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