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
  Scissors,
  Save,
  CheckCircle,
  Trash2,
  Edit,
  Mic,
  AudioWaveformIcon as Waveform,
} from "lucide-react";

interface AudioSegment {
  id: string;
  startTime: number;
  endTime: number;
  transcription: string;
  label: string;
  confidence?: number;
  speaker?: string;
}

interface AudioAnnotationWorkspaceProps {
  task: any;
  currentFileIndex: number;
  onSaveAndNext: () => void;
  onSkipAndNext: () => void;
}

// 模拟音频数据
const mockAudioFiles = [
  {
    id: "1",
    name: "interview_001.wav",
    url: "/placeholder-audio.mp3", // 这里应该是实际的音频文件URL
    duration: 180, // 3分钟
    segments: [
      {
        id: "1",
        startTime: 0,
        endTime: 15,
        transcription: "你好，欢迎参加今天的访谈。请先介绍一下自己。",
        label: "问题",
        confidence: 0.95,
        speaker: "主持人",
      },
      {
        id: "2",
        startTime: 15,
        endTime: 45,
        transcription:
          "大家好，我是张三，目前在一家科技公司担任产品经理，有五年的工作经验。",
        label: "回答",
        confidence: 0.88,
        speaker: "受访者",
      },
      {
        id: "3",
        startTime: 45,
        endTime: 60,
        transcription: "很好，那么请谈谈你对人工智能发展的看法。",
        label: "问题",
        confidence: 0.92,
        speaker: "主持人",
      },
    ],
  },
];

// 预定义标签
const audioLabels = [
  { name: "问题", color: "#3B82F6" },
  { name: "回答", color: "#10B981" },
  { name: "讨论", color: "#F59E0B" },
  { name: "总结", color: "#EF4444" },
  { name: "背景音", color: "#8B5CF6" },
  { name: "其他", color: "#6B7280" },
];

export default function AudioAnnotationWorkspace({
  task,
  currentFileIndex,
  onSaveAndNext,
  onSkipAndNext,
}: AudioAnnotationWorkspaceProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [currentAudio] = useState(mockAudioFiles[0]);
  const [segments, setSegments] = useState<AudioSegment[]>(
    currentAudio.segments
  );
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(currentAudio.duration);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [selectedSegment, setSelectedSegment] = useState<string | null>(null);
  const [isCreatingSegment, setIsCreatingSegment] = useState(false);
  const [newSegmentStart, setNewSegmentStart] = useState(0);
  const [editingSegment, setEditingSegment] = useState<AudioSegment | null>(
    null
  );

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => setCurrentTime(audio.currentTime);
    const updateDuration = () => setDuration(audio.duration);
    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener("timeupdate", updateTime);
    audio.addEventListener("loadedmetadata", updateDuration);
    audio.addEventListener("ended", handleEnded);

    return () => {
      audio.removeEventListener("timeupdate", updateTime);
      audio.removeEventListener("loadedmetadata", updateDuration);
      audio.removeEventListener("ended", handleEnded);
    };
  }, []);

  const togglePlayPause = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (time: number) => {
    const audio = audioRef.current;
    if (!audio) return;

    audio.currentTime = time;
    setCurrentTime(time);
  };

  const handleVolumeChange = (value: number[]) => {
    const audio = audioRef.current;
    if (!audio) return;

    const newVolume = value[0];
    audio.volume = newVolume;
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
  };

  const toggleMute = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isMuted) {
      audio.volume = volume;
      setIsMuted(false);
    } else {
      audio.volume = 0;
      setIsMuted(true);
    }
  };

  const startCreatingSegment = () => {
    setIsCreatingSegment(true);
    setNewSegmentStart(currentTime);
    toast({
      title: "开始创建片段",
      description: `片段起始时间: ${formatTime(currentTime)}`,
    });
  };

  const finishCreatingSegment = () => {
    if (!isCreatingSegment) return;

    const newSegment: AudioSegment = {
      id: Date.now().toString(),
      startTime: newSegmentStart,
      endTime: currentTime,
      transcription: "",
      label: audioLabels[0].name,
      speaker: "",
    };

    setSegments([...segments, newSegment]);
    setIsCreatingSegment(false);
    setEditingSegment(newSegment);

    toast({
      title: "片段已创建",
      description: `时长: ${formatTime(currentTime - newSegmentStart)}`,
    });
  };

  const deleteSegment = (id: string) => {
    setSegments(segments.filter((s) => s.id !== id));
    setSelectedSegment(null);
    toast({
      title: "片段已删除",
      description: "音频片段已被删除",
    });
  };

  const updateSegment = (updatedSegment: AudioSegment) => {
    setSegments(
      segments.map((s) => (s.id === updatedSegment.id ? updatedSegment : s))
    );
    setEditingSegment(null);
    toast({
      title: "片段已更新",
      description: "转录内容已保存",
    });
  };

  const playSegment = (segment: AudioSegment) => {
    handleSeek(segment.startTime);
    setSelectedSegment(segment.id);

    const audio = audioRef.current;
    if (!audio) return;

    audio.play();
    setIsPlaying(true);

    // 在片段结束时暂停
    const checkEnd = () => {
      if (audio.currentTime >= segment.endTime) {
        audio.pause();
        setIsPlaying(false);
        audio.removeEventListener("timeupdate", checkEnd);
      }
    };
    audio.addEventListener("timeupdate", checkEnd);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  };

  const getSegmentColor = (label: string) => {
    const labelConfig = audioLabels.find((l) => l.name === label);
    return labelConfig?.color || "#6B7280";
  };

  return (
    <div className="flex-1 flex flex-col">
      {/* Audio Player */}
      <div className="border-b bg-white p-4">
        <div className="space-y-4">
          {/* Audio Element */}
          <audio ref={audioRef} src={currentAudio.url} preload="metadata" />

          {/* Player Controls */}
          <div className="flex items-center justify-center space-x-4">
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
          </div>

          {/* Timeline */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
            <div className="relative">
              <Slider
                value={[currentTime]}
                max={duration}
                step={0.1}
                onValueChange={(value) => handleSeek(value[0])}
                className="w-full"
              />
              {/* Segment Visualization */}
              <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
                {segments.map((segment) => {
                  const left = (segment.startTime / duration) * 100;
                  const width =
                    ((segment.endTime - segment.startTime) / duration) * 100;
                  return (
                    <div
                      key={segment.id}
                      className="absolute top-0 h-full opacity-30 rounded"
                      style={{
                        left: `${left}%`,
                        width: `${width}%`,
                        backgroundColor: getSegmentColor(segment.label),
                      }}
                    />
                  );
                })}
              </div>
              {/* Current Creating Segment */}
              {isCreatingSegment && (
                <div
                  className="absolute top-0 h-full bg-red-400 opacity-50 rounded"
                  style={{
                    left: `${(newSegmentStart / duration) * 100}%`,
                    width: `${
                      ((currentTime - newSegmentStart) / duration) * 100
                    }%`,
                  }}
                />
              )}
            </div>
          </div>

          {/* Volume Control */}
          <div className="flex items-center justify-center space-x-2">
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

          {/* Annotation Controls */}
          <div className="flex items-center justify-center space-x-2">
            {isCreatingSegment ? (
              <Button
                onClick={finishCreatingSegment}
                className="bg-green-600 hover:bg-green-700"
              >
                <Square className="w-4 h-4 mr-2" />
                完成片段
              </Button>
            ) : (
              <Button onClick={startCreatingSegment} variant="outline">
                <Scissors className="w-4 h-4 mr-2" />
                创建片段
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Segments List */}
        <div className="w-96 border-r bg-gray-50 p-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-medium">音频片段</h3>
              <Badge variant="outline">{segments.length} 个片段</Badge>
            </div>

            <ScrollArea className="h-96">
              <div className="space-y-2">
                {segments.map((segment) => (
                  <Card
                    key={segment.id}
                    className={`cursor-pointer transition-colors ${
                      selectedSegment === segment.id
                        ? "border-blue-500 bg-blue-50"
                        : "hover:bg-gray-50"
                    }`}
                    onClick={() => setSelectedSegment(segment.id)}
                  >
                    <CardContent className="p-3">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <div
                              className="w-3 h-3 rounded"
                              style={{
                                backgroundColor: getSegmentColor(segment.label),
                              }}
                            />
                            <span className="text-sm font-medium">
                              {segment.label}
                            </span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="p-1 h-auto"
                              onClick={(e) => {
                                e.stopPropagation();
                                playSegment(segment);
                              }}
                            >
                              <Play className="w-3 h-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="p-1 h-auto"
                              onClick={(e) => {
                                e.stopPropagation();
                                setEditingSegment(segment);
                              }}
                            >
                              <Edit className="w-3 h-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="p-1 h-auto text-red-500"
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteSegment(segment.id);
                              }}
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                        <div className="text-xs text-gray-500">
                          {formatTime(segment.startTime)} -{" "}
                          {formatTime(segment.endTime)}
                          {segment.speaker && ` | ${segment.speaker}`}
                        </div>
                        <p className="text-sm text-gray-700 line-clamp-2">
                          {segment.transcription || "未转录"}
                        </p>
                        {segment.confidence && (
                          <div className="flex items-center space-x-2">
                            <span className="text-xs text-gray-500">
                              置信度:
                            </span>
                            <Badge variant="outline" className="text-xs">
                              {(segment.confidence * 100).toFixed(1)}%
                            </Badge>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </div>
        </div>

        {/* Transcription Editor */}
        <div className="flex-1 p-6">
          {editingSegment ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Mic className="w-5 h-5" />
                  <span>编辑转录</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">开始时间</label>
                    <Input
                      value={formatTime(editingSegment.startTime)}
                      readOnly
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">结束时间</label>
                    <Input
                      value={formatTime(editingSegment.endTime)}
                      readOnly
                      className="mt-1"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium">标签</label>
                  <select
                    value={editingSegment.label}
                    onChange={(e) =>
                      setEditingSegment({
                        ...editingSegment,
                        label: e.target.value,
                      })
                    }
                    className="w-full mt-1 px-3 py-2 border rounded-md"
                  >
                    {audioLabels.map((label) => (
                      <option key={label.name} value={label.name}>
                        {label.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium">说话人</label>
                  <Input
                    value={editingSegment.speaker || ""}
                    onChange={(e) =>
                      setEditingSegment({
                        ...editingSegment,
                        speaker: e.target.value,
                      })
                    }
                    placeholder="输入说话人名称"
                    className="mt-1"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium">转录内容</label>
                  <Textarea
                    value={editingSegment.transcription}
                    onChange={(e) =>
                      setEditingSegment({
                        ...editingSegment,
                        transcription: e.target.value,
                      })
                    }
                    placeholder="输入或编辑转录内容..."
                    rows={6}
                    className="mt-1"
                  />
                </div>

                <div className="flex items-center justify-end space-x-2">
                  <Button
                    variant="outline"
                    onClick={() => setEditingSegment(null)}
                  >
                    取消
                  </Button>
                  <Button
                    onClick={() => updateSegment(editingSegment)}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    保存
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : selectedSegment ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Waveform className="w-5 h-5" />
                  <span>片段详情</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {(() => {
                  const segment = segments.find(
                    (s) => s.id === selectedSegment
                  );
                  if (!segment) return null;

                  return (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <span className="text-sm text-gray-500">
                            时间范围
                          </span>
                          <p className="font-medium">
                            {formatTime(segment.startTime)} -{" "}
                            {formatTime(segment.endTime)}
                          </p>
                        </div>
                        <div>
                          <span className="text-sm text-gray-500">时长</span>
                          <p className="font-medium">
                            {formatTime(segment.endTime - segment.startTime)}
                          </p>
                        </div>
                      </div>

                      <div>
                        <span className="text-sm text-gray-500">标签</span>
                        <div className="flex items-center space-x-2 mt-1">
                          <div
                            className="w-3 h-3 rounded"
                            style={{
                              backgroundColor: getSegmentColor(segment.label),
                            }}
                          />
                          <span className="font-medium">{segment.label}</span>
                        </div>
                      </div>

                      {segment.speaker && (
                        <div>
                          <span className="text-sm text-gray-500">说话人</span>
                          <p className="font-medium">{segment.speaker}</p>
                        </div>
                      )}

                      <div>
                        <span className="text-sm text-gray-500">转录内容</span>
                        <p className="mt-1 p-3 bg-gray-50 rounded text-sm">
                          {segment.transcription || "暂无转录内容"}
                        </p>
                      </div>

                      {segment.confidence && (
                        <div>
                          <span className="text-sm text-gray-500">置信度</span>
                          <p className="font-medium">
                            {(segment.confidence * 100).toFixed(1)}%
                          </p>
                        </div>
                      )}

                      <div className="flex items-center space-x-2">
                        <Button
                          onClick={() => playSegment(segment)}
                          variant="outline"
                        >
                          <Play className="w-4 h-4 mr-2" />
                          播放片段
                        </Button>
                        <Button
                          onClick={() => setEditingSegment(segment)}
                          variant="outline"
                        >
                          <Edit className="w-4 h-4 mr-2" />
                          编辑
                        </Button>
                      </div>
                    </div>
                  );
                })()}
              </CardContent>
            </Card>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <Mic className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  音频标注工作区
                </h3>
                <p className="text-gray-500 mb-4">
                  选择一个音频片段开始编辑转录内容
                </p>
                <div className="space-y-2 text-sm text-gray-600">
                  <p>• 点击"创建片段"开始标记音频片段</p>
                  <p>• 选择片段进行转录和标注</p>
                  <p>• 使用播放控件精确定位音频位置</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="border-t bg-white p-4">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            文件: {currentAudio.name} | 片段: {segments.length} | 总时长:{" "}
            {formatTime(duration)}
          </div>
          <div className="flex items-center space-x-2">
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
  );
}
