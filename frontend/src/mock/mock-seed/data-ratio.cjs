
const Mock = require("mockjs");
const API = require("../mock-apis.cjs");

function ratioJobItem() {
	return {
		id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
		name: Mock.Random.ctitle(5, 15),
		description: Mock.Random.csentence(10, 30),
		status: Mock.Random.pick(["PENDING", "RUNNING", "COMPLETED", "FAILED", "PAUSED"]),
		totals: Mock.Random.integer(1000, 10000),
		ratio_method: Mock.Random.pick(["DATASET", "TAG"]),
		target_dataset_id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
		target_dataset_name: Mock.Random.ctitle(3, 8),
		config: [
			{
				datasetId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
				counts: Mock.Random.integer(100, 1000).toString(),
				filter_conditions: "",
			},
			{
				datasetId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
				counts: Mock.Random.integer(100, 1000).toString(),
				filter_conditions: "",
			},
		],
		created_at: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
		updated_at: Mock.Random.datetime("yyyy-MM-dd HH:mm:ss"),
	};
}

const ratioJobList = new Array(20).fill(null).map(ratioJobItem);


module.exports = function (router) {
	// 获取配比任务列表
	router.get(API.queryRatioTasksUsingGet, (req, res) => {
		const { page = 0, size = 10, status } = req.query;
		let filteredJobs = ratioJobList;
		if (status) {
			filteredJobs = ratioJobList.filter((job) => job.status === status);
		}
		const startIndex = page * size;
		const endIndex = startIndex + parseInt(size);
		const pageData = filteredJobs.slice(startIndex, endIndex);
		res.send({
			code: "0",
			msg: "Success",
			data: {
				content: pageData,
				totalElements: filteredJobs.length,
				totalPages: Math.ceil(filteredJobs.length / size),
				size: parseInt(size),
				number: parseInt(page),
			},
		});
	});

	// 创建配比任务
	router.post(API.createRatioTaskUsingPost, (req, res) => {
		const newJob = {
			...ratioJobItem(),
			...req.body,
			id: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
			status: "PENDING",
			createdAt: new Date().toISOString(),
		};
		ratioJobList.push(newJob);
		res.status(201).send({
			code: "0",
			msg: "Ratio job created successfully",
			data: newJob,
		});
	});

	// 获取配比任务详情
	router.get(API.queryRatioTaskByIdUsingGet, (req, res) => {
		const { taskId } = req.params;
		const job = ratioJobList.find((j) => j.id === taskId);
		if (job) {
			res.send({
				code: "0",
				msg: "Success",
				data: job,
			});
		} else {
			res.status(404).send({
				code: "1",
				msg: "Ratio job not found",
				data: null,
			});
		}
	});

	// 删除配比任务
	router.delete(API.deleteRatioTaskByIdUsingDelete, (req, res) => {
		const { taskId } = req.params;
		const index = ratioJobList.findIndex((j) => j.id === taskId);
		if (index !== -1) {
			ratioJobList.splice(index, 1);
			res.send({
				code: "0",
				msg: "Ratio job deleted successfully",
				data: null,
			});
		} else {
			res.status(404).send({
				code: "1",
				msg: "Ratio job not found",
				data: null,
			});
		}
	});

	// 更新配比任务
	router.put(API.updateRatioTaskByIdUsingPut, (req, res) => {
		const { taskId } = req.params;
		const index = ratioJobList.findIndex((j) => j.id === taskId);
		if (index !== -1) {
			ratioJobList[index] = {
				...ratioJobList[index],
				...req.body,
				updatedAt: new Date().toISOString(),
			};
			res.send({
				code: "0",
				msg: "Ratio job updated successfully",
				data: ratioJobList[index],
			});
		} else {
			res.status(404).send({
				code: "1",
				msg: "Ratio job not found",
				data: null,
			});
		}
	});

	// 执行配比任务
	router.post(API.executeRatioTaskByIdUsingPost, (req, res) => {
		const { taskId } = req.params;
		const job = ratioJobList.find((j) => j.id === taskId);
		if (job) {
			job.status = "RUNNING";
			job.startedAt = new Date().toISOString();
			res.send({
				code: "0",
				msg: "Ratio job execution started",
				data: {
					executionId: Mock.Random.guid().replace(/[^a-zA-Z0-9]/g, ""),
					status: "RUNNING",
					message: "Job execution started successfully",
				},
			});
		} else {
			res.status(404).send({
				code: "1",
				msg: "Ratio job not found",
				data: null,
			});
		}
	});

	// 停止配比任务
	router.post(API.stopRatioTaskByIdUsingPost, (req, res) => {
		const { taskId } = req.params;
		const job = ratioJobList.find((j) => j.id === taskId);
		if (job) {
			job.status = "STOPPED";
			job.finishedAt = new Date().toISOString();
			res.send({
				code: "0",
				msg: "Ratio job stopped successfully",
				data: null,
			});
		} else {
			res.status(404).send({
				code: "1",
				msg: "Ratio job not found",
				data: null,
			});
		}
	});

	// 获取配比任务状态
	router.get(API.queryRatioJobStatusUsingGet, (req, res) => {
		const { taskId } = req.params;
		const job = ratioJobList.find((j) => j.id === taskId);
		if (job) {
			res.send({
				code: "0",
				msg: "Success",
				data: {
					status: job.status,
					progress: job.progress,
				},
			});
		} else {
			res.status(404).send({
				code: "1",
				msg: "Ratio job not found",
				data: null,
			});
		}
	});

	// 获取配比模型列表
	router.get(API.queryRatioModelsUsingGet, (req, res) => {
		const models = [
			{ id: "model1", name: "均匀分配模型", description: "将目标数量均匀分配到各数据集。" },
			{ id: "model2", name: "标签优先模型", description: "优先满足标签配比需求。" },
			{ id: "model3", name: "自定义模型", description: "支持自定义分配逻辑。" },
		];
		res.send({
			code: "0",
			msg: "Success",
			data: models,
		});
	});
};
