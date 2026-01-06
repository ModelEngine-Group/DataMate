import { Card } from "antd";

export default function Documentation({ operator }) {
  const documentation = "# 图像预处理算子\n" +
    "\n" +
    "## 概述\n" +
    "这是一个高效的图像预处理算子，支持多种常用的图像处理操作。\n" +
    "\n" +
    "## 主要功能\n" +
    "- 图像缩放和裁剪\n" +
    "- 旋转和翻转\n" +
    "- 颜色空间转换\n" +
    "- 噪声添加和去除\n" +
    "- 批量处理支持\n" +
    "\n" +
    "## 性能特点\n" +
    "- 内存优化，支持大图像处理\n" +
    "- GPU加速支持\n" +
    "- 多线程并行处理\n" +
    "- 自动批处理优化"

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <div className="prose max-w-none">
          <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
            {documentation}
          </div>
        </div>
      </Card>
    </div>
  );
}
