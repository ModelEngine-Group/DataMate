import { useState, useEffect } from "react";
import { Modal, Form, Input, Select, Slider, message, Checkbox } from "antd";
import { createAutoAnnotationTaskUsingPost } from "../../annotation.api";
import { queryDatasetsUsingGet } from "@/pages/DataManagement/dataset.api";
import { mapDataset } from "@/pages/DataManagement/dataset.const";
import { DatasetType, type DatasetFile, type Dataset } from "@/pages/DataManagement/dataset.model";
import DatasetFileTransfer from "@/components/business/DatasetFileTransfer";

const { Option } = Select;

interface CreateAutoAnnotationDialogProps {
	visible: boolean;
	onCancel: () => void;
	onSuccess: () => void;
}

const COCO_CLASSES = [
	{ id: 0, name: "person", label: "人" },
	{ id: 1, name: "bicycle", label: "自行车" },
	{ id: 2, name: "car", label: "汽车" },
	{ id: 3, name: "motorcycle", label: "摩托车" },
	{ id: 4, name: "airplane", label: "飞机" },
	{ id: 5, name: "bus", label: "公交车" },
	{ id: 6, name: "train", label: "火车" },
	{ id: 7, name: "truck", label: "卡车" },
	{ id: 8, name: "boat", label: "船" },
	{ id: 9, name: "traffic light", label: "红绿灯" },
	{ id: 10, name: "fire hydrant", label: "消防栓" },
	{ id: 11, name: "stop sign", label: "停止标志" },
	{ id: 12, name: "parking meter", label: "停车计时器" },
	{ id: 13, name: "bench", label: "长椅" },
	{ id: 14, name: "bird", label: "鸟" },
	{ id: 15, name: "cat", label: "猫" },
	{ id: 16, name: "dog", label: "狗" },
	{ id: 17, name: "horse", label: "马" },
	{ id: 18, name: "sheep", label: "羊" },
	{ id: 19, name: "cow", label: "牛" },
	{ id: 20, name: "elephant", label: "大象" },
	{ id: 21, name: "bear", label: "熊" },
	{ id: 22, name: "zebra", label: "斑马" },
	{ id: 23, name: "giraffe", label: "长颈鹿" },
	{ id: 24, name: "backpack", label: "背包" },
	{ id: 25, name: "umbrella", label: "雨伞" },
	{ id: 26, name: "handbag", label: "手提包" },
	{ id: 27, name: "tie", label: "领带" },
	{ id: 28, name: "suitcase", label: "行李箱" },
	{ id: 29, name: "frisbee", label: "飞盘" },
	{ id: 30, name: "skis", label: "滑雪板" },
	{ id: 31, name: "snowboard", label: "滑雪板" },
	{ id: 32, name: "sports ball", label: "球类" },
	{ id: 33, name: "kite", label: "风筝" },
	{ id: 34, name: "baseball bat", label: "棒球棒" },
	{ id: 35, name: "baseball glove", label: "棒球手套" },
	{ id: 36, name: "skateboard", label: "滑板" },
	{ id: 37, name: "surfboard", label: "冲浪板" },
	{ id: 38, name: "tennis racket", label: "网球拍" },
	{ id: 39, name: "bottle", label: "瓶子" },
	{ id: 40, name: "wine glass", label: "酒杯" },
	{ id: 41, name: "cup", label: "杯子" },
	{ id: 42, name: "fork", label: "叉子" },
	{ id: 43, name: "knife", label: "刀" },
	{ id: 44, name: "spoon", label: "勺子" },
	{ id: 45, name: "bowl", label: "碗" },
	{ id: 46, name: "banana", label: "香蕉" },
	{ id: 47, name: "apple", label: "苹果" },
	{ id: 48, name: "sandwich", label: "三明治" },
	{ id: 49, name: "orange", label: "橙子" },
	{ id: 50, name: "broccoli", label: "西兰花" },
	{ id: 51, name: "carrot", label: "胡萝卜" },
	{ id: 52, name: "hot dog", label: "热狗" },
	{ id: 53, name: "pizza", label: "披萨" },
	{ id: 54, name: "donut", label: "甜甜圈" },
	{ id: 55, name: "cake", label: "蛋糕" },
	{ id: 56, name: "chair", label: "椅子" },
	{ id: 57, name: "couch", label: "沙发" },
	{ id: 58, name: "potted plant", label: "盆栽" },
	{ id: 59, name: "bed", label: "床" },
	{ id: 60, name: "dining table", label: "餐桌" },
	{ id: 61, name: "toilet", label: "马桶" },
	{ id: 62, name: "tv", label: "电视" },
	{ id: 63, name: "laptop", label: "笔记本电脑" },
	{ id: 64, name: "mouse", label: "鼠标" },
	{ id: 65, name: "remote", label: "遥控器" },
	{ id: 66, name: "keyboard", label: "键盘" },
	{ id: 67, name: "cell phone", label: "手机" },
	{ id: 68, name: "microwave", label: "微波炉" },
	{ id: 69, name: "oven", label: "烤箱" },
	{ id: 70, name: "toaster", label: "烤面包机" },
	{ id: 71, name: "sink", label: "水槽" },
	{ id: 72, name: "refrigerator", label: "冰箱" },
	{ id: 73, name: "book", label: "书" },
	{ id: 74, name: "clock", label: "钟表" },
	{ id: 75, name: "vase", label: "花瓶" },
	{ id: 76, name: "scissors", label: "剪刀" },
	{ id: 77, name: "teddy bear", label: "玩具熊" },
	{ id: 78, name: "hair drier", label: "吹风机" },
	{ id: 79, name: "toothbrush", label: "牙刷" },
];

export default function CreateAutoAnnotationDialog({
	visible,
	onCancel,
	onSuccess,
}: CreateAutoAnnotationDialogProps) {
	const [form] = Form.useForm();
	const [loading, setLoading] = useState(false);
	const [datasets, setDatasets] = useState<any[]>([]);
	const [selectAllClasses, setSelectAllClasses] = useState(true);
	const [selectedFilesMap, setSelectedFilesMap] = useState<Record<string, DatasetFile>>({});
	const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
	const [imageFileCount, setImageFileCount] = useState(0);

	useEffect(() => {
		if (visible) {
			fetchDatasets();
			form.resetFields();
			form.setFieldsValue({
				modelSize: "l",
				confThreshold: 0.7,
				targetClasses: [],
			});
		}
	}, [visible, form]);

	const fetchDatasets = async () => {
		try {
			const { data } = await queryDatasetsUsingGet({
				page: 0,
				pageSize: 1000,
			});
			const imageDatasets = (data.content || [])
				.map(mapDataset)
				.filter((ds: any) => ds.datasetType === DatasetType.IMAGE);
			setDatasets(imageDatasets);
		} catch (error) {
			console.error("Failed to fetch datasets:", error);
			message.error("获取数据集列表失败");
		}
	};

	useEffect(() => {
		const imageExtensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"];
		const count = Object.values(selectedFilesMap).filter((file) => {
			const ext = file.fileName?.toLowerCase().match(/\.[^.]+$/)?.[0] || "";
			return imageExtensions.includes(ext);
		}).length;
		setImageFileCount(count);
	}, [selectedFilesMap]);

	const handleSubmit = async () => {
		try {
			const values = await form.validateFields();

			if (imageFileCount === 0) {
				message.error("请至少选择一个图像文件");
				return;
			}

			setLoading(true);

			const imageExtensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"];
			const imageFileIds = Object.values(selectedFilesMap)
				.filter((file) => {
					const ext = file.fileName?.toLowerCase().match(/\.[^.]+$/)?.[0] || "";
					return imageExtensions.includes(ext);
				})
				.map((file) => file.id);

			const payload = {
				name: values.name,
				datasetId: values.datasetId,
				fileIds: imageFileIds,
				config: {
					modelSize: values.modelSize,
					confThreshold: values.confThreshold,
					targetClasses: selectAllClasses ? [] : values.targetClasses || [],
					outputDatasetName: values.outputDatasetName || undefined,
				},
			};

			await createAutoAnnotationTaskUsingPost(payload);
			message.success("自动标注任务创建成功");
			onSuccess();
		} catch (error: any) {
			if (error.errorFields) return;
			console.error("Failed to create auto annotation task:", error);
			message.error(error.message || "创建任务失败");
		} finally {
			setLoading(false);
		}
	};

	const handleClassSelectionChange = (checked: boolean) => {
		setSelectAllClasses(checked);
		if (checked) {
			form.setFieldsValue({ targetClasses: [] });
		}
	};

	return (
		<Modal
			title="创建自动标注任务"
			open={visible}
			onCancel={onCancel}
			onOk={handleSubmit}
			confirmLoading={loading}
			width={600}
			destroyOnClose
		>
			<Form form={form} layout="vertical" preserve={false}>
				<Form.Item
					name="name"
					label="任务名称"
					rules={[
						{ required: true, message: "请输入任务名称" },
						{ max: 100, message: "任务名称不能超过100个字符" },
					]}
				>
					<Input placeholder="请输入任务名称" />
				</Form.Item>

				<Form.Item label="选择数据集和图像文件" required>
					<DatasetFileTransfer
						open
						selectedFilesMap={selectedFilesMap}
						onSelectedFilesChange={setSelectedFilesMap}
						onDatasetSelect={(dataset) => {
							setSelectedDataset(dataset);
							form.setFieldsValue({ datasetId: dataset?.id ?? "" });
						}}
						datasetTypeFilter={DatasetType.IMAGE}
					/>
					{selectedDataset && (
						<div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200 text-xs">
							当前数据集：<span className="font-medium">{selectedDataset.name}</span> - 已选择
							<span className="font-medium text-blue-600"> {imageFileCount} </span>个图像文件
						</div>
					)}
				</Form.Item>

				<Form.Item hidden name="datasetId" rules={[{ required: true, message: "请选择数据集" }]}>
					<Input type="hidden" />
				</Form.Item>

				<Form.Item name="modelSize" label="模型规模" rules={[{ required: true, message: "请选择模型规模" }]}>
					<Select>
						<Option value="n">YOLOv8n (最快)</Option>
						<Option value="s">YOLOv8s</Option>
						<Option value="m">YOLOv8m</Option>
						<Option value="l">YOLOv8l (推荐)</Option>
						<Option value="x">YOLOv8x (最精确)</Option>
					</Select>
				</Form.Item>

				<Form.Item
					name="confThreshold"
					label="置信度阈值"
					rules={[{ required: true, message: "请选择置信度阈值" }]}
				>
					<Slider min={0.1} max={0.9} step={0.05} tooltip={{ formatter: (v) => `${(v || 0) * 100}%` }} />
				</Form.Item>

				<Form.Item label="目标类别">
					<Checkbox checked={selectAllClasses} onChange={(e) => handleClassSelectionChange(e.target.checked)}>
						选中所有类别
					</Checkbox>
					{!selectAllClasses && (
						<Form.Item name="targetClasses" noStyle>
							<Select mode="multiple" placeholder="选择目标类别" style={{ marginTop: 8 }}>
								{COCO_CLASSES.map((cls) => (
									<Option key={cls.id} value={cls.id}>
										{cls.label} ({cls.name})
									</Option>
								))}
							</Select>
						</Form.Item>
					)}
				</Form.Item>

				<Form.Item name="outputDatasetName" label="输出数据集名称 (可选)">
					<Input placeholder="留空则将结果写入原数据集的标签中" />
				</Form.Item>
			</Form>
		</Modal>
	);
}