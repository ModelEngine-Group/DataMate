import { useEffect, useRef, useState } from "react";

const TopLoadingBar = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [progress, setProgress] = useState(0);
  const intervalRef = useRef(null);

  useEffect(() => {
    // 监听全局事件
    const handleShow = () => {
      setIsVisible(true);
      setProgress(0);

      // 清除可能存在的旧interval
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }

      // 模拟进度
      let currentProgress = 0;
      intervalRef.current = setInterval(() => {
        currentProgress += Math.random() * 10;
        if (currentProgress >= 90) {
          clearInterval(intervalRef.current);
        }
        setProgress(currentProgress);
      }, 200);
    };

    const handleHide = () => {
      // 清除进度interval
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setProgress(100);
      setTimeout(() => {
        setIsVisible(false);
        setProgress(0);
      }, 300);
    };

    // 添加全局事件监听器
    window.addEventListener("loading:show", handleShow);
    window.addEventListener("loading:hide", handleHide);

    return () => {
      // 组件卸载时清理
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      window.removeEventListener("loading:show", handleShow);
      window.removeEventListener("loading:hide", handleHide);
    };
  }, []);

  if (!isVisible) return null;

  return (
    <div className="top-loading-bar">
      <div
        className="loading-bar-progress"
        style={{ width: `${progress}%` }}
      ></div>
    </div>
  );
};

export default TopLoadingBar;
