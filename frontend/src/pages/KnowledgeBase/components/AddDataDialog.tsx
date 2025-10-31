export default function AddDataDialog() {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const { message } = App.useApp();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      message.error("请先选择文件");
      return;
    }

    try {
      const formData = new FormData();
      selectedFiles.forEach((file) => {
        formData.append("files", file);
      });

      await uploadDataFilesUsingPost(formData);
      message.success("文件上传成功");
      setIsOpen(false);
      setSelectedFiles([]);
    } catch (error) {
      message.error("文件上传失败");
    }
  };

  return (
    <>
      <Button type="primary" onClick={() => setIsOpen(true)}>
        添加数据
      </Button>
      <Modal
        title="添加数据文件"
        open={isOpen}
        onCancel={() => setIsOpen(false)}
        onOk={handleUpload}
        okText="上传"
      >
        <input
          type="file"
          multiple
          onChange={handleFileChange}
          accept=".txt,.pdf,.docx,.csv,.json"
        />
        {selectedFiles.length > 0 && (
          <div className="mt-4">
            <h4>已选择的文件：</h4>
            <ul>
              {selectedFiles.map((file, index) => (
                <li key={index}>
                  {file.name} - {(file.size / 1024).toFixed(2)} KB
                </li>
              ))}
            </ul>
          </div>
        )}
      </Modal>
    </>
  );
}
