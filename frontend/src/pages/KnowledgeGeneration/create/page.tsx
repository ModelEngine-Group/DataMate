import { useState } from "react";

const KnowledgeBaseCreatePage: React.FC = () => {
    const [createForm, setCreateForm] = useState({
        name: "",
        description: "",
        type: "unstructured" as "unstructured" | "structured",
        embeddingModel: "text-embedding-3-large",
        llmModel: "gpt-4o",
        chunkSize: 512,
        overlap: 50,
        sliceMethod: "semantic" as "paragraph" | "length" | "delimiter" | "semantic",
        delimiter: "",
        enableQA: true,
        vectorDatabase: "pinecone",
        selectedSliceOperators: ["semantic-split", "paragraph-split"] as string[],
        uploadedFiles: [] as File[],
        selectedDatasetFiles: [] as { datasetId: string; fileId: string; name: string; size: string; type: string }[],
    })
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold">创建知识库</h1>
                    <p className="text-gray-600 mt-1">配置知识库参数，支持结构化和非结构化数据清洗</p>
                </div>
                <Button variant="outline" onClick={() => setCurrentView("list")}>
                    取消
                </Button>
            </div>

            <Card>
                <CardContent className="pt-6">
                    <div className="space-y-6">
                        <div className="space-y-4">
                            <h4 className="font-medium">基本信息</h4>
                            <div className="space-y-3">
                                <div>
                                    <Label htmlFor="kb-name">
                                        知识库名称 <span className="text-red-500">*</span>
                                    </Label>
                                    <Input
                                        id="kb-name"
                                        value={createForm.name}
                                        onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                                        placeholder="输入知识库名称"
                                        required
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="kb-description">描述</Label>
                                    <Textarea
                                        id="kb-description"
                                        value={createForm.description}
                                        onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                                        placeholder="描述知识库的用途和内容"
                                        rows={3}
                                    />
                                </div>
                                <div>
                                    <Label>知识库类型</Label>
                                    <div className="grid grid-cols-2 gap-4">
                                        <Button
                                            variant="outline"
                                            onClick={() => setCreateForm({ ...createForm, type: "unstructured" })}
                                            className={`h-auto py-4 flex flex-col items-center gap-2 transition-all duration-200 ${createForm.type === "unstructured"
                                                ? "bg-blue-600 text-white border-blue-600 shadow-lg"
                                                : "bg-white text-gray-800 border-gray-300 hover:bg-gray-50"
                                                }`}
                                        >
                                            <BookOpen className="w-6 h-6" />
                                            <p className="font-medium">非结构化知识库</p>
                                            <p className="text-xs text-center opacity-80">支持文档、PDF等文件</p>
                                        </Button>
                                        <Button
                                            variant="outline"
                                            onClick={() => setCreateForm({ ...createForm, type: "structured" })}
                                            className={`h-auto py-4 flex flex-col items-center gap-2 transition-all duration-200 ${createForm.type === "structured"
                                                ? "bg-blue-600 text-white border-blue-600 shadow-lg"
                                                : "bg-white text-gray-800 border-gray-300 hover:bg-gray-50"
                                                }`}
                                        >
                                            <Database className="w-6 h-6" />
                                            <p className="font-medium">结构化知识库</p>
                                            <p className="text-xs text-center opacity-80">支持问答对、表格数据</p>
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <Separator />

                        <div className="space-y-4">
                            <h4 className="font-medium flex items-center gap-2">
                                <Brain className="w-4 h-4" />
                                模型配置
                            </h4>
                            <div className="space-y-3">
                                <div>
                                    <Label htmlFor="embedding-model">嵌入模型</Label>
                                    <Select
                                        value={createForm.embeddingModel}
                                        onValueChange={(value) => setCreateForm({ ...createForm, embeddingModel: value })}
                                    >
                                        <SelectTrigger id="embedding-model">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="text-embedding-3-large">text-embedding-3-large (推荐)</SelectItem>
                                            <SelectItem value="text-embedding-3-small">text-embedding-3-small</SelectItem>
                                            <SelectItem value="text-embedding-ada-002">text-embedding-ada-002</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                {createForm.type === "unstructured" && createForm.enableQA && (
                                    <div>
                                        <Label htmlFor="llm-model">LLM模型 (用于Q&A生成)</Label>
                                        <Select
                                            value={createForm.llmModel}
                                            onValueChange={(value) => setCreateForm({ ...createForm, llmModel: value })}
                                        >
                                            <SelectTrigger id="llm-model">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="gpt-4o">GPT-4o (推荐)</SelectItem>
                                                <SelectItem value="gpt-4o-mini">GPT-4o Mini</SelectItem>
                                                <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                )}
                                <div>
                                    <Label htmlFor="vector-database">向量数据库</Label>
                                    <Select
                                        value={createForm.vectorDatabase}
                                        onValueChange={(value) => setCreateForm({ ...createForm, vectorDatabase: value })}
                                    >
                                        <SelectTrigger id="vector-database">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {vectorDatabases.map((db) => (
                                                <SelectItem key={db.id} value={db.id}>
                                                    <div className="flex flex-col">
                                                        <span className="font-medium">{db.name}</span>
                                                        <span className="text-xs text-gray-500">{db.description}</span>
                                                    </div>
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                        </div>

                        <Separator />

                        {createForm.type === "unstructured" && (
                            <>
                                <div className="space-y-4">
                                    <h4 className="font-medium flex items-center gap-2">
                                        <Scissors className="w-4 h-4" />
                                        切片算子配置
                                    </h4>
                                    <div className="space-y-3">
                                        <div>
                                            <Label>选择切片算子</Label>
                                            <p className="text-sm text-gray-500 mb-3">选择适合的切片算子来处理文档内容</p>
                                            <div className="grid grid-cols-2 gap-3">
                                                {sliceOperators.map((operator) => (
                                                    <div
                                                        key={operator.id}
                                                        className={`border rounded-lg p-3 cursor-pointer transition-all ${createForm.selectedSliceOperators.includes(operator.id)
                                                            ? "border-blue-500 bg-blue-50"
                                                            : "border-gray-200 hover:border-gray-300"
                                                            }`}
                                                        onClick={() => handleSliceOperatorToggle(operator.id)}
                                                    >
                                                        <div className="flex items-start gap-3">
                                                            <Checkbox
                                                                checked={createForm.selectedSliceOperators.includes(operator.id)}
                                                                onChange={() => handleSliceOperatorToggle(operator.id)}
                                                            />
                                                            <div className="flex-1">
                                                                <div className="flex items-center gap-2 mb-1">
                                                                    <span className="text-lg">{operator.icon}</span>
                                                                    <span className="font-medium text-sm">{operator.name}</span>
                                                                    <Badge variant="outline" className="text-xs">
                                                                        {operator.type}
                                                                    </Badge>
                                                                </div>
                                                                <p className="text-xs text-gray-600">{operator.description}</p>
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <Separator />

                                <div className="space-y-4">
                                    <h4 className="font-medium flex items-center gap-2">
                                        <Split className="w-4 h-4" />
                                        文档分割配置
                                    </h4>
                                    <div className="space-y-3">
                                        <div>
                                            <Label htmlFor="slice-method">分割方式</Label>
                                            <Select
                                                value={createForm.sliceMethod}
                                                onValueChange={(value: any) => setCreateForm({ ...createForm, sliceMethod: value })}
                                            >
                                                <SelectTrigger id="slice-method">
                                                    <SelectValue />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="semantic">语义分割 (推荐)</SelectItem>
                                                    <SelectItem value="paragraph">段落分割</SelectItem>
                                                    <SelectItem value="length">长度分割</SelectItem>
                                                    <SelectItem value="delimiter">分隔符分割</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>

                                        {createForm.sliceMethod === "delimiter" && (
                                            <div>
                                                <Label htmlFor="delimiter">分隔符</Label>
                                                <Input
                                                    id="delimiter"
                                                    value={createForm.delimiter}
                                                    onChange={(e) => setCreateForm({ ...createForm, delimiter: e.target.value })}
                                                    placeholder="输入分隔符，如 \\n\\n"
                                                />
                                            </div>
                                        )}

                                        <div className="grid grid-cols-2 gap-3">
                                            <div>
                                                <Label htmlFor="chunk-size">分块大小</Label>
                                                <Input
                                                    id="chunk-size"
                                                    type="number"
                                                    value={createForm.chunkSize}
                                                    onChange={(e) => setCreateForm({ ...createForm, chunkSize: Number(e.target.value) })}
                                                />
                                            </div>
                                            <div>
                                                <Label htmlFor="overlap-length">重叠长度</Label>
                                                <Input
                                                    id="overlap-length"
                                                    type="number"
                                                    value={createForm.overlap}
                                                    onChange={(e) => setCreateForm({ ...createForm, overlap: Number(e.target.value) })}
                                                />
                                            </div>
                                        </div>

                                        <div className="flex items-center justify-between">
                                            <div>
                                                <Label htmlFor="enable-qa">启用Q&A生成</Label>
                                                <p className="text-xs text-gray-500">将文档内容转换为问答对</p>
                                            </div>
                                            <Switch
                                                id="enable-qa"
                                                checked={createForm.enableQA}
                                                onCheckedChange={(checked) => setCreateForm({ ...createForm, enableQA: checked })}
                                            />
                                        </div>
                                    </div>
                                </div>

                                <Separator />
                            </>
                        )}

                        <div className="space-y-4">
                            <h4 className="font-medium flex items-center gap-2">
                                <Upload className="w-4 h-4" />
                                {createForm.type === "structured" ? "导入模板文件" : "选择数据源"}
                            </h4>

                            <Tabs defaultValue="upload">
                                <TabsList className="grid w-full grid-cols-2">
                                    <TabsTrigger value="upload">上传文件</TabsTrigger>
                                    <TabsTrigger value="dataset">从数据集选择</TabsTrigger>
                                </TabsList>

                                <TabsContent value="upload" className="space-y-3">
                                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center relative">
                                        <Input
                                            id="file-upload"
                                            type="file"
                                            multiple
                                            className="absolute inset-0 opacity-0 cursor-pointer"
                                            onChange={handleFileChange}
                                        />
                                        <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                                        <p className="text-sm text-gray-600">
                                            {createForm.type === "structured"
                                                ? "拖拽或点击上传Excel/CSV模板文件"
                                                : "拖拽或点击上传文档文件"}
                                        </p>
                                        <Button variant="outline" className="mt-2 bg-transparent pointer-events-none">
                                            选择文件
                                        </Button>
                                    </div>
                                    {createForm.uploadedFiles.length > 0 && (
                                        <div className="space-y-2">
                                            <p className="text-sm font-medium">已选择文件:</p>
                                            <ul className="list-disc pl-5 text-sm text-gray-700">
                                                {createForm.uploadedFiles.map((file, index) => (
                                                    <li key={index}>{file.name}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </TabsContent>

                                <TabsContent value="dataset" className="space-y-3">
                                    <div className="flex gap-2 mb-4">
                                        <Input
                                            placeholder="搜索数据集..."
                                            value={datasetSearchQuery}
                                            onChange={(e) => setDatasetSearchQuery(e.target.value)}
                                            className="flex-1"
                                        />
                                        <Button variant="outline" onClick={() => setSelectedDatasetId(null)}>
                                            重置选择
                                        </Button>
                                    </div>

                                    <div className="grid grid-cols-3 gap-4 h-80">
                                        <div className="col-span-1 border rounded-lg overflow-y-auto p-2 space-y-2">
                                            {filteredDatasets.length === 0 && (
                                                <p className="text-center text-gray-500 py-4 text-sm">无匹配数据集</p>
                                            )}
                                            {filteredDatasets.map((dataset) => (
                                                <div
                                                    key={dataset.id}
                                                    className={`flex items-center justify-between p-3 border rounded-lg cursor-pointer ${selectedDatasetId === dataset.id ? "bg-blue-50 border-blue-500" : "hover:bg-gray-50"
                                                        }`}
                                                    onClick={() => setSelectedDatasetId(dataset.id)}
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <Folder className="w-5 h-5 text-blue-400" />
                                                        <div>
                                                            <p className="font-medium">{dataset.name}</p>
                                                            <p className="text-xs text-gray-500">{dataset.files.length} 个文件</p>
                                                        </div>
                                                    </div>
                                                    {selectedDatasetId === dataset.id && <CheckCircle className="w-5 h-5 text-blue-600" />}
                                                </div>
                                            ))}
                                        </div>

                                        <div className="col-span-2 border rounded-lg overflow-y-auto p-2 space-y-2">
                                            {!selectedDatasetId ? (
                                                <div className="text-center py-8 text-gray-500">
                                                    <Folder className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                                                    <p className="text-sm">请选择一个数据集</p>
                                                </div>
                                            ) : (
                                                <>
                                                    <div className="flex items-center gap-2 p-2 border-b pb-2">
                                                        <Checkbox
                                                            checked={isAllDatasetFilesSelected(
                                                                mockDatasets.find((d) => d.id === selectedDatasetId)!,
                                                            )}
                                                            onCheckedChange={(checked) =>
                                                                handleSelectAllDatasetFiles(
                                                                    mockDatasets.find((d) => d.id === selectedDatasetId)!,
                                                                    checked as boolean,
                                                                )
                                                            }
                                                        />
                                                        <Label className="font-medium">
                                                            全选 ({mockDatasets.find((d) => d.id === selectedDatasetId)?.files.length} 个文件)
                                                        </Label>
                                                    </div>
                                                    {mockDatasets
                                                        .find((d) => d.id === selectedDatasetId)
                                                        ?.files.map((file) => (
                                                            <div
                                                                key={file.id}
                                                                className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                                                            >
                                                                <div className="flex items-center gap-3">
                                                                    <Checkbox
                                                                        checked={isDatasetFileSelected(selectedDatasetId, file.id)}
                                                                        onCheckedChange={(checked) => handleDatasetFileToggle(selectedDatasetId, file)}
                                                                    />
                                                                    <File className="w-5 h-5 text-gray-400" />
                                                                    <div>
                                                                        <p className="font-medium">{file.name}</p>
                                                                        <p className="text-sm text-gray-500">
                                                                            {file.size} • {file.type}
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        ))}
                                                </>
                                            )}
                                        </div>
                                    </div>
                                    {createForm.selectedDatasetFiles.length > 0 && (
                                        <div className="mt-4 text-sm font-medium text-gray-700">
                                            已选择数据集文件总数: {createForm.selectedDatasetFiles.length}
                                        </div>
                                    )}
                                </TabsContent>
                            </Tabs>
                        </div>

                        <div className="flex gap-3 pt-4">
                            <Button
                                onClick={handleCreateKB}
                                disabled={!createForm.name || !createForm.description}
                                className="flex-1"
                            >
                                创建知识库
                            </Button>
                            <Button variant="outline" onClick={() => setCurrentView("list")}>
                                取消
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}