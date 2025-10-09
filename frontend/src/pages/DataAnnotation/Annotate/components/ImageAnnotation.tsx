import type React from "react";
import { useState, useRef, useEffect } from "react";
import { Button, Badge, Checkbox, message } from "antd";
import {
  Square,
  Circle,
  MousePointer,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  ArrowLeft,
  ArrowRight,
  MoreHorizontal,
} from "lucide-react";

interface Annotation {
  id: string;
  type: "rectangle" | "circle" | "polygon";
  label: string;
  color: string;
  coordinates: number[];
  visible: boolean;
}

interface ImageAnnotationWorkspaceProps {
  task: any;
  currentFileIndex: number;
  onSaveAndNext: () => void;
  onSkipAndNext: () => void;
}

// 模拟医学图像数据
const mockMedicalImages = [
  {
    id: "1",
    name: "2024-123456",
    thumbnail: "/placeholder.svg?height=60&width=60&text=Slide1",
    url: "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/img_v3_02oi_e6dd5540-9ca4-4277-ad2b-4debaa1c8ddg.jpg-oibLbUmFpZMkLTmwZB7lT1UWKFlOLA.jpeg",
  },
  {
    id: "2",
    name: "2024-234567",
    thumbnail: "/placeholder.svg?height=60&width=60&text=Slide2",
    url: "/placeholder.svg?height=600&width=800&text=Medical Image 2",
  },
  {
    id: "3",
    name: "2025-345678",
    thumbnail: "/placeholder.svg?height=60&width=60&text=Slide3",
    url: "/placeholder.svg?height=600&width=800&text=Medical Image 3",
  },
  {
    id: "4",
    name: "1234-123456",
    thumbnail: "/placeholder.svg?height=60&width=60&text=Slide4",
    url: "/placeholder.svg?height=600&width=800&text=Medical Image 4",
  },
  {
    id: "5",
    name: "2025-456789",
    thumbnail: "/placeholder.svg?height=60&width=60&text=Slide5",
    url: "/placeholder.svg?height=600&width=800&text=Medical Image 5",
  },
  {
    id: "6",
    name: "2025-567890",
    thumbnail: "/placeholder.svg?height=60&width=60&text=Slide6",
    url: "/placeholder.svg?height=600&width=800&text=Medical Image 6",
  },
  {
    id: "7",
    name: "2025-678901",
    thumbnail: "/placeholder.svg?height=60&width=60&text=Slide7",
    url: "/placeholder.svg?height=600&width=800&text=Medical Image 7",
  },
  {
    id: "8",
    name: "2025-789012",
    thumbnail: "/placeholder.svg?height=60&width=60&text=Slide8",
    url: "/placeholder.svg?height=600&width=800&text=Medical Image 8",
  },
  {
    id: "9",
    name: "2025-890123",
    thumbnail: "/placeholder.svg?height=60&width=60&text=Slide9",
    url: "/placeholder.svg?height=600&width=800&text=Medical Image 9",
  },
  {
    id: "10",
    name: "2025-901234",
    thumbnail: "/placeholder.svg?height=60&width=60&text=Slide10",
    url: "/placeholder.svg?height=600&width=800&text=Medical Image 10",
  },
];

// 医学标注选项
const medicalAnnotationOptions = [
  {
    id: "tumor_present",
    label: "是否有肿瘤",
    type: "radio",
    options: ["是", "否"],
  },
  {
    id: "tumor_type",
    label: "肿瘤形成",
    type: "checkbox",
    options: ["腺管形成"],
  },
  { id: "grade_1", label: "1级", type: "checkbox", options: ["1[x]"] },
  { id: "grade_2", label: "2级", type: "checkbox", options: ["2[x]"] },
  { id: "remarks", label: "备注", type: "textarea" },
  {
    id: "nuclear_polymorphism",
    label: "核多形性",
    type: "checkbox",
    options: ["核分裂象"],
  },
  {
    id: "histological_type",
    label: "组织学类型",
    type: "checkbox",
    options: ["1[b]", "2[y]", "3[t]"],
  },
  {
    id: "small_time_lesion",
    label: "小时病位置[3]",
    type: "checkbox",
    options: ["1[b]", "2[y]", "3[t]"],
  },
  {
    id: "ductal_position",
    label: "导管原位置[4]",
    type: "checkbox",
    options: ["1[o]", "2[p]", "3[t]"],
  },
  {
    id: "ductal_position_large",
    label: "导管原位置件大于腺分",
    type: "checkbox",
    options: ["腺分裂象"],
  },
  {
    id: "mitosis",
    label: "化[5]",
    type: "checkbox",
    options: ["1[o]", "2[p]", "3[t]"],
  },
  {
    id: "original_position",
    label: "原位实性乳头状[6]",
    type: "checkbox",
    options: ["1[o]", "2[p]", "3[t]"],
  },
  {
    id: "infiltrating_lesion",
    label: "浸润性病(非特殊型)[7]",
    type: "checkbox",
    options: ["1[o]", "2[p]", "3[t]"],
  },
  {
    id: "infiltrating_small",
    label: "浸润性小叶癌[8]",
    type: "checkbox",
    options: ["脉管侵犯"],
  },
  {
    id: "infiltrating_real",
    label: "浸润实性乳头状癌[9]",
    type: "checkbox",
    options: ["1[o]", "2[p]", "3[t]"],
  },
  {
    id: "other_lesion",
    label: "其他病[0]",
    type: "checkbox",
    options: ["+[k]"],
  },
];

export default function ImageAnnotationWorkspace({
  currentFileIndex,
}: ImageAnnotationWorkspaceProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedImageIndex, setSelectedImageIndex] = useState(
    currentFileIndex || 0
  );
  const [currentImage, setCurrentImage] = useState(
    mockMedicalImages[selectedImageIndex]
  );
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [selectedTool, setSelectedTool] = useState<
    "select" | "rectangle" | "circle"
  >("select");
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [selectedAnnotation, setSelectedAnnotation] = useState<string | null>(
    null
  );
  const [annotationValues, setAnnotationValues] = useState<Record<string, any>>(
    {}
  );

  useEffect(() => {
    setCurrentImage(mockMedicalImages[selectedImageIndex]);
    drawCanvas();
  }, [selectedImageIndex, annotations, zoom, pan]);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      ctx.save();
      ctx.scale(zoom, zoom);
      ctx.translate(pan.x, pan.y);
      ctx.drawImage(img, 0, 0, canvas.width / zoom, canvas.height / zoom);

      // 绘制标注
      annotations.forEach((annotation) => {
        if (!annotation.visible) return;

        ctx.strokeStyle = annotation.color;
        ctx.fillStyle = annotation.color + "20";
        ctx.lineWidth = 2;

        if (annotation.type === "rectangle") {
          const [x, y, width, height] = annotation.coordinates;
          ctx.strokeRect(x, y, width, height);
          ctx.fillRect(x, y, width, height);
        } else if (annotation.type === "circle") {
          const [centerX, centerY, radius] = annotation.coordinates;
          ctx.beginPath();
          ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
          ctx.stroke();
          ctx.fill();
        }

        if (selectedAnnotation === annotation.id) {
          ctx.strokeStyle = "#FF0000";
          ctx.lineWidth = 3;
          ctx.setLineDash([5, 5]);

          if (annotation.type === "rectangle") {
            const [x, y, width, height] = annotation.coordinates;
            ctx.strokeRect(x - 2, y - 2, width + 4, height + 4);
          } else if (annotation.type === "circle") {
            const [centerX, centerY, radius] = annotation.coordinates;
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius + 2, 0, 2 * Math.PI);
            ctx.stroke();
          }

          ctx.setLineDash([]);
        }
      });

      ctx.restore();
    };
    img.src = currentImage.url;
  };

  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - pan.x) / zoom;
    const y = (e.clientY - rect.top - pan.y) / zoom;

    if (selectedTool === "rectangle" || selectedTool === "circle") {
      setIsDrawing(true);
      setStartPoint({ x, y });
    } else if (selectedTool === "select") {
      const clickedAnnotation = annotations.find((annotation) => {
        if (annotation.type === "rectangle") {
          const [ax, ay, width, height] = annotation.coordinates;
          return x >= ax && x <= ax + width && y >= ay && y <= ay + height;
        } else if (annotation.type === "circle") {
          const [centerX, centerY, radius] = annotation.coordinates;
          const distance = Math.sqrt((x - centerX) ** 2 + (y - centerY) ** 2);
          return distance <= radius;
        }
        return false;
      });

      setSelectedAnnotation(clickedAnnotation?.id || null);
    }
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - pan.x) / zoom;
    const y = (e.clientY - rect.top - pan.y) / zoom;

    drawCanvas();
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.save();
    ctx.scale(zoom, zoom);
    ctx.translate(pan.x, pan.y);
    ctx.strokeStyle = "#3B82F6";
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);

    if (selectedTool === "rectangle") {
      const width = x - startPoint.x;
      const height = y - startPoint.y;
      ctx.strokeRect(startPoint.x, startPoint.y, width, height);
    } else if (selectedTool === "circle") {
      const radius = Math.sqrt(
        (x - startPoint.x) ** 2 + (y - startPoint.y) ** 2
      );
      ctx.beginPath();
      ctx.arc(startPoint.x, startPoint.y, radius, 0, 2 * Math.PI);
      ctx.stroke();
    }

    ctx.restore();
  };

  const handleCanvasMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - pan.x) / zoom;
    const y = (e.clientY - rect.top - pan.y) / zoom;

    let coordinates: number[] = [];

    if (selectedTool === "rectangle") {
      const width = x - startPoint.x;
      const height = y - startPoint.y;
      coordinates = [startPoint.x, startPoint.y, width, height];
    } else if (selectedTool === "circle") {
      const radius = Math.sqrt(
        (x - startPoint.x) ** 2 + (y - startPoint.y) ** 2
      );
      coordinates = [startPoint.x, startPoint.y, radius];
    }

    if (coordinates.length > 0) {
      const newAnnotation: Annotation = {
        id: Date.now().toString(),
        type: selectedTool as "rectangle" | "circle",
        label: "标注",
        color: "#3B82F6",
        coordinates,
        visible: true,
      };

      setAnnotations([...annotations, newAnnotation]);
    }

    setIsDrawing(false);
  };

  const handleAnnotationValueChange = (optionId: string, value: any) => {
    setAnnotationValues((prev) => ({
      ...prev,
      [optionId]: value,
    }));
  };

  const handleUpdate = () => {
    message({
      title: "标注已更新",
      description: "医学标注信息已保存",
    });
  };

  return (
    <div className="h-screen flex">
      {/* Left Sidebar - Image List */}
      <div className="w-80 border-r bg-white">
        {/* Header */}
        <div className="p-4 border-b bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Badge variant="outline">image</Badge>
              <Badge className="bg-blue-100 text-blue-800">img</Badge>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">case_id</span>
              <span className="text-sm font-mono">#13754</span>
              <Button variant="ghost" size="sm">
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </div>
          </div>
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center text-white text-xs">
                DE
              </div>
              <span className="text-sm text-gray-600">de #14803</span>
            </div>
            <span className="text-xs text-gray-500">11 days ago</span>
          </div>
        </div>

        {/* Image List */}
        <div className="p-2">
          {mockMedicalImages.map((image, index) => (
            <div
              key={image.id}
              className={`flex items-center p-3 mb-2 rounded-lg cursor-pointer transition-colors ${
                selectedImageIndex === index
                  ? "bg-blue-50 border border-blue-200"
                  : "hover:bg-gray-50"
              }`}
              onClick={() => setSelectedImageIndex(index)}
            >
              <div className="w-8 h-8 bg-gray-200 rounded flex items-center justify-center text-sm font-medium mr-3">
                {index + 1}
              </div>
              <img
                src={image.thumbnail || "/placeholder.svg"}
                alt={`Slide ${index + 1}`}
                className="w-12 h-12 rounded border mr-3"
              />
              <div className="flex-1">
                <div className="font-medium text-sm">{image.name}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Main Image Display */}
        <div className="flex-1 p-4">
          <div className="h-full flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">WSI图像预览</h2>
              <div className="flex items-center space-x-2">
                <div className="text-sm text-gray-600">
                  病理号: <span className="font-mono">1234-123456</span>
                </div>
                <div className="text-sm text-gray-600">
                  取材部位: <span>余乳</span>
                </div>
              </div>
            </div>

            <div className="flex-1 border rounded-lg overflow-hidden bg-gray-100 relative">
              <canvas
                ref={canvasRef}
                width={800}
                height={600}
                className="w-full h-full object-contain cursor-crosshair"
                onMouseDown={handleCanvasMouseDown}
                onMouseMove={handleCanvasMouseMove}
                onMouseUp={handleCanvasMouseUp}
              />

              {/* Zoom Controls */}
              <div className="absolute bottom-4 left-4 flex items-center space-x-2 bg-white rounded-lg shadow-lg p-2">
                <Button onClick={() => setZoom(Math.max(zoom / 1.2, 0.1))}>
                  <ZoomOut className="w-4 h-4" />
                </Button>
                <span className="text-sm px-2">{Math.round(zoom * 100)}%</span>
                <Button onClick={() => setZoom(Math.min(zoom * 1.2, 5))}>
                  <ZoomIn className="w-4 h-4" />
                </Button>
                <Button
                  onClick={() => {
                    setZoom(1);
                    setPan({ x: 0, y: 0 });
                  }}
                >
                  <RotateCcw className="w-4 h-4" />
                </Button>
              </div>

              {/* Tool Selection */}
              <div className="absolute top-4 left-4 flex items-center space-x-2 bg-white rounded-lg shadow-lg p-2">
                <Button
                  variant={selectedTool === "select" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedTool("select")}
                >
                  <MousePointer className="w-4 h-4" />
                </Button>
                <Button
                  variant={selectedTool === "rectangle" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedTool("rectangle")}
                >
                  <Square className="w-4 h-4" />
                </Button>
                <Button
                  variant={selectedTool === "circle" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedTool("circle")}
                >
                  <Circle className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Navigation Controls */}
            <div className="flex items-center justify-center mt-4 space-x-2">
              <Button>
                <ArrowLeft className="w-4 h-4" />
              </Button>
              <Button>
                <ArrowRight className="w-4 h-4" />
              </Button>
              <span className="text-sm text-gray-600 mx-4">手</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Sidebar - Annotation Panel */}
      <div className="w-80 border-l bg-gray-50 p-4">
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold text-lg mb-4">标注</h3>

            <div className="space-y-4">
              {medicalAnnotationOptions.map((option) => (
                <div key={option.id} className="space-y-2">
                  <span className="text-sm font-medium">{option.label}</span>

                  {option.type === "radio" && (
                    <div className="space-y-1">
                      {option.options?.map((opt) => (
                        <div key={opt} className="flex items-center space-x-2">
                          <input
                            type="radio"
                            name={option.id}
                            value={opt}
                            onChange={(e) =>
                              handleAnnotationValueChange(
                                option.id,
                                e.target.value
                              )
                            }
                            className="w-4 h-4"
                          />
                          <span className="text-sm">{opt}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {option.type === "checkbox" && (
                    <div className="space-y-1">
                      {option.options?.map((opt) => (
                        <div key={opt} className="flex items-center space-x-2">
                          <Checkbox
                            checked={
                              annotationValues[`${option.id}_${opt}`] || false
                            }
                            onChange={(checked) =>
                              handleAnnotationValueChange(
                                `${option.id}_${opt}`,
                                checked
                              )
                            }
                          />
                          <span className="text-sm">{opt}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {option.type === "textarea" && (
                    <textarea
                      className="w-full p-2 border rounded-md text-sm resize-none"
                      rows={3}
                      placeholder={`请输入${option.label}`}
                      value={annotationValues[option.id] || ""}
                      onChange={(e) =>
                        handleAnnotationValueChange(option.id, e.target.value)
                      }
                    />
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t">
            <Button
              onClick={handleUpdate}
              className="w-full bg-amber-600 hover:bg-amber-700"
            >
              Update
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
