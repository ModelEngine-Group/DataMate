

import type React from "react";

import { useState, useRef, useEffect } from "react";
import { Card, Button, Badge, Slider, message } from "antd";
import {
  Play,
  Pause,
  Square,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
  MousePointer,
  CheckCircle,
  Trash2,
  Eye,
  EyeOff,
  Target,
  Maximize,
} from "lucide-react";

interface VideoAnnotation {
  id: string;
  frameTime: number;
  type: "rectangle" | "point" | "polygon";
  coordinates: number[];
  label: string;
  color: string;
  trackId?: string;
  visible: boolean;
}

interface VideoTrack {
  id: string;
  label: string;
  color: string;
  annotations: VideoAnnotation[];
  startTime: number;
  endTime: number;
}

interface VideoAnnotationWorkspaceProps {
  task: any;
  currentFileIndex: number;
  onSaveAndNext: () => void;
  onSkipAndNext: () => void;
}

// 模拟视频数据
const mockVideoFiles = [
  {
    id: "1",
    name: "traffic_scene_001.mp4",
    url: "/placeholder-video.mp4", // 这里应该是实际的视频文件URL
    duration: 120, // 2分钟
    fps: 30,
    width: 1920,
    height: 1080,
  },
];

// 预定义标签
const videoLabels = [
  { name: "车辆", color: "#3B82F6" },
  { name: "行人", color: "#10B981" },
  { name: "自行车", color: "#F59E0B" },
  { name: "交通灯", color: "#EF4444" },
  { name: "路标", color: "#8B5CF6" },
  { name: "其他", color: "#6B7280" },
];

export default function VideoAnnotationWorkspace({
  task,
  currentFileIndex,
  onSaveAndNext,
  onSkipAndNext,
}: VideoAnnotationWorkspaceProps) {
  const [messageApi, contextHolder] = message.useMessage();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [currentVideo] = useState(mockVideoFiles[0]);
  const [tracks, setTracks] = useState<VideoTrack[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(currentVideo.duration);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [selectedTool, setSelectedTool] = useState<
    "select" | "rectangle" | "point"
  >("select");
  const [selectedLabel, setSelectedLabel] = useState(videoLabels[0]);
  const [selectedTrack, setSelectedTrack] = useState<string | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState({ x: 0, y: 0 });
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const updateTime = () => setCurrentTime(video.currentTime);
    const updateDuration = () => setDuration(video.duration);
    const handleEnded = () => setIsPlaying(false);

    video.addEventListener("timeupdate", updateTime);
    video.addEventListener("loadedmetadata", updateDuration);
    video.addEventListener("ended", handleEnded);

    return () => {
      video.removeEventListener("timeupdate", updateTime);
      video.removeEventListener("loadedmetadata", updateDuration);
      video.removeEventListener("ended", handleEnded);
    };
  }, []);

  useEffect(() => {
    drawCanvas();
  }, [currentTime, tracks, selectedTrack]);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 绘制当前帧的标注
    tracks.forEach((track) => {
      if (!track.annotations.length) return;

      // 找到当前时间最近的标注
      const currentAnnotation = track.annotations
        .filter((ann) => Math.abs(ann.frameTime - currentTime) < 0.1)
        .sort(
          (a, b) =>
            Math.abs(a.frameTime - currentTime) -
            Math.abs(b.frameTime - currentTime)
        )[0];

      if (!currentAnnotation || !currentAnnotation.visible) return;

      ctx.strokeStyle = track.color;
      ctx.fillStyle = track.color + "20";
      ctx.lineWidth = selectedTrack === track.id ? 3 : 2;

      if (currentAnnotation.type === "rectangle") {
        const [x, y, width, height] = currentAnnotation.coordinates;
        ctx.strokeRect(x, y, width, height);
        ctx.fillRect(x, y, width, height);

        // 绘制标签
        ctx.fillStyle = track.color;
        ctx.fillRect(x, y - 20, ctx.measureText(track.label).width + 8, 20);
        ctx.fillStyle = "white";
        ctx.font = "12px Arial";
        ctx.fillText(track.label, x + 4, y - 6);
      } else if (currentAnnotation.type === "point") {
        const [x, y] = currentAnnotation.coordinates;
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();

        // 绘制标签
        ctx.fillStyle = track.color;
        ctx.fillRect(
          x + 10,
          y - 10,
          ctx.measureText(track.label).width + 8,
          20
        );
        ctx.fillStyle = "white";
        ctx.font = "12px Arial";
        ctx.fillText(track.label, x + 14, y + 4);
      }
    });
  };

  const togglePlayPause = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.pause();
    } else {
      video.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (time: number) => {
    const video = videoRef.current;
    if (!video) return;

    video.currentTime = time;
    setCurrentTime(time);
  };

  const handleVolumeChange = (value: number[]) => {
    const video = videoRef.current;
    if (!video) return;

    const newVolume = value[0];
    video.volume = newVolume;
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
  };

  const toggleMute = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isMuted) {
      video.volume = volume;
      setIsMuted(false);
    } else {
      video.volume = 0;
      setIsMuted(true);
    }
  };

  const handleSpeedChange = (speed: number) => {
    const video = videoRef.current;
    if (!video) return;

    video.playbackRate = speed;
    setPlaybackSpeed(speed);
  };

  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (selectedTool === "select") return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (selectedTool === "point") {
      createPointAnnotation(x, y);
    } else if (selectedTool === "rectangle") {
      setIsDrawing(true);
      setStartPoint({ x, y });
    }
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || selectedTool !== "rectangle") return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // 实时预览
    drawCanvas();
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.strokeStyle = selectedLabel.color;
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.strokeRect(
      startPoint.x,
      startPoint.y,
      x - startPoint.x,
      y - startPoint.y
    );
    ctx.setLineDash([]);
  };

  const handleCanvasMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || selectedTool !== "rectangle") return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const width = x - startPoint.x;
    const height = y - startPoint.y;

    if (Math.abs(width) > 10 && Math.abs(height) > 10) {
      createRectangleAnnotation(startPoint.x, startPoint.y, width, height);
    }

    setIsDrawing(false);
  };

  const createPointAnnotation = (x: number, y: number) => {
    const newAnnotation: VideoAnnotation = {
      id: Date.now().toString(),
      frameTime: currentTime,
      type: "point",
      coordinates: [x, y],
      label: selectedLabel.name,
      color: selectedLabel.color,
      visible: true,
    };

    const newTrack: VideoTrack = {
      id: Date.now().toString(),
      label: selectedLabel.name,
      color: selectedLabel.color,
      annotations: [newAnnotation],
      startTime: currentTime,
      endTime: currentTime,
    };

    setTracks([...tracks, newTrack]);
    messageApi({
      title: "点标注已添加",
      description: `在时间 ${formatTime(currentTime)} 添加了点标注`,
    });
  };

  const createRectangleAnnotation = (
    x: number,
    y: number,
    width: number,
    height: number
  ) => {
    const newAnnotation: VideoAnnotation = {
      id: Date.now().toString(),
      frameTime: currentTime,
      type: "rectangle",
      coordinates: [x, y, width, height],
      label: selectedLabel.name,
      color: selectedLabel.color,
      visible: true,
    };

    const newTrack: VideoTrack = {
      id: Date.now().toString(),
      label: selectedLabel.name,
      color: selectedLabel.color,
      annotations: [newAnnotation],
      startTime: currentTime,
      endTime: currentTime,
    };

    setTracks([...tracks, newTrack]);
    messageApi.success(`在时间 ${formatTime(currentTime)} 添加了矩形标注`);
  };

  const deleteTrack = (trackId: string) => {
    setTracks(tracks.filter((t) => t.id !== trackId));
    setSelectedTrack(null);
    messageApi.success("标注轨迹已被删除");
  };

  const toggleTrackVisibility = (trackId: string) => {
    setTracks(
      tracks.map((track) =>
        track.id === trackId
          ? {
              ...track,
              annotations: track.annotations.map((ann) => ({
                ...ann,
                visible: !ann.visible,
              })),
            }
          : track
      )
    );
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  };

  const toggleFullscreen = () => {
    const video = videoRef.current;
    if (!video) return;

    if (!isFullscreen) {
      if (video.requestFullscreen) {
        video.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
    setIsFullscreen(!isFullscreen);
  };

  return (
    <div className="flex-1 flex">
      {/* Tools Panel */}
      <div className="w-64 border-r bg-gray-50 p-4 space-y-4">
        {/* Tool Selection */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">工具</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button
              variant={selectedTool === "select" ? "default" : "outline"}
              size="sm"
              className="w-full justify-start"
              onClick={() => setSelectedTool("select")}
            >
              <MousePointer className="w-4 h-4 mr-2" />
              选择
            </Button>
            <Button
              variant={selectedTool === "rectangle" ? "default" : "outline"}
              size="sm"
              className="w-full justify-start"
              onClick={() => setSelectedTool("rectangle")}
            >
              <Square className="w-4 h-4 mr-2" />
              矩形
            </Button>
            <Button
              variant={selectedTool === "point" ? "default" : "outline"}
              size="sm"
              className="w-full justify-start"
              onClick={() => setSelectedTool("point")}
            >
              <Target className="w-4 h-4 mr-2" />
              点标注
            </Button>
          </CardContent>
        </Card>

        {/* Labels */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">标签</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {videoLabels.map((label) => (
              <Button
                key={label.name}
                variant={
                  selectedLabel.name === label.name ? "default" : "outline"
                }
                size="sm"
                className="w-full justify-start"
                onClick={() => setSelectedLabel(label)}
              >
                <div
                  className="w-4 h-4 mr-2 rounded"
                  style={{ backgroundColor: label.color }}
                />
                {label.name}
              </Button>
            ))}
          </CardContent>
        </Card>

        {/* Playback Speed */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">播放速度</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {[0.25, 0.5, 1, 1.5, 2].map((speed) => (
              <Button
                key={speed}
                variant={playbackSpeed === speed ? "default" : "outline"}
                size="sm"
                className="w-full"
                onClick={() => handleSpeedChange(speed)}
              >
                {speed}x
              </Button>
            ))}
          </CardContent>
        </Card>

        {/* Tracks List */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">标注轨迹</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-48">
              <div className="space-y-2">
                {tracks.map((track) => (
                  <div
                    key={track.id}
                    className={`p-2 border rounded cursor-pointer ${
                      selectedTrack === track.id
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-200"
                    }`}
                    onClick={() => setSelectedTrack(track.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div
                          className="w-3 h-3 rounded"
                          style={{ backgroundColor: track.color }}
                        />
                        <span className="text-sm font-medium">
                          {track.label}
                        </span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="p-1 h-auto"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleTrackVisibility(track.id);
                          }}
                        >
                          {track.annotations[0]?.visible ? (
                            <Eye className="w-3 h-3" />
                          ) : (
                            <EyeOff className="w-3 h-3" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="p-1 h-auto text-red-500"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteTrack(track.id);
                          }}
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {track.annotations.length} 个关键帧
                    </div>
                  </div>
                ))}
                {tracks.length === 0 && (
                  <div className="text-center py-4 text-gray-500 text-sm">
                    暂无轨迹
                  </div>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Video Player and Canvas */}
      <div className="flex-1 flex flex-col">
        {/* Video Container */}
        <div className="flex-1 relative bg-black">
          <video
            ref={videoRef}
            src={currentVideo.url}
            className="w-full h-full object-contain"
            preload="metadata"
          />
          <canvas
            ref={canvasRef}
            width={800}
            height={450}
            className="absolute top-0 left-0 w-full h-full cursor-crosshair"
            onMouseDown={handleCanvasMouseDown}
            onMouseMove={handleCanvasMouseMove}
            onMouseUp={handleCanvasMouseUp}
          />

          {/* Video Info Overlay */}
          <div className="absolute top-4 left-4 bg-black bg-opacity-50 text-white px-3 py-1 rounded text-sm">
            {currentVideo.name} | {formatTime(currentTime)} /{" "}
            {formatTime(duration)}
          </div>

          {/* Tool Info Overlay */}
          <div className="absolute top-4 right-4 bg-black bg-opacity-50 text-white px-3 py-1 rounded text-sm">
            {selectedTool === "select"
              ? "选择模式"
              : selectedTool === "rectangle"
              ? "矩形标注"
              : "点标注"}{" "}
            | {selectedLabel.name}
          </div>
        </div>

        {/* Video Controls */}
        <div className="border-t bg-white p-4 space-y-4">
          {/* Timeline */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
            <Slider
              value={[currentTime]}
              max={duration}
              step={0.1}
              onValueChange={(value) => handleSeek(value[0])}
              className="w-full"
            />
          </div>

          {/* Player Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleSeek(Math.max(0, currentTime - 10))}
              >
                <SkipBack className="w-4 h-4" />
              </Button>
              <Button
                onClick={togglePlayPause}
                size="lg"
                className="bg-blue-600 hover:bg-blue-700"
              >
                {isPlaying ? (
                  <Pause className="w-6 h-6" />
                ) : (
                  <Play className="w-6 h-6" />
                )}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleSeek(Math.min(duration, currentTime + 10))}
              >
                <SkipForward className="w-4 h-4" />
              </Button>

              {/* Volume Control */}
              <div className="flex items-center space-x-2">
                <Button variant="ghost" size="sm" onClick={toggleMute}>
                  {isMuted ? (
                    <VolumeX className="w-4 h-4" />
                  ) : (
                    <Volume2 className="w-4 h-4" />
                  )}
                </Button>
                <Slider
                  value={[isMuted ? 0 : volume]}
                  max={1}
                  step={0.1}
                  onValueChange={handleVolumeChange}
                  className="w-24"
                />
              </div>

              <Button variant="outline" size="sm" onClick={toggleFullscreen}>
                <Maximize className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex items-center space-x-2">
              <Badge variant="outline">{playbackSpeed}x</Badge>
              <Badge variant="outline">{tracks.length} 轨迹</Badge>
              <Button onClick={onSkipAndNext} variant="outline">
                跳过
              </Button>
              <Button
                onClick={onSaveAndNext}
                className="bg-green-600 hover:bg-green-700"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                保存并下一个
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
