class LoadingManager {
  constructor() {
    this.isShowing = false;
    this.queue = 0; // 支持多个并发请求
  }

  show() {
    this.queue++;
    this.isShowing = true;

    // 触发全局事件
    const event = new Event("loading:show");
    window.dispatchEvent(event);
  }

  hide() {
    this.queue = Math.max(0, this.queue - 1);

    if (this.queue === 0) {
      this.isShowing = false;
      // 触发全局事件
      const event = new Event("loading:hide");
      window.dispatchEvent(event);
    }
  }

  // 强制隐藏所有加载
  hideAll() {
    this.queue = 0;
    this.isShowing = false;
    const event = new Event("loading:hide");
    window.dispatchEvent(event);
  }

  // 获取当前状态
  getStatus() {
    return {
      isShowing: this.isShowing,
      queueCount: this.queue,
    };
  }
}

// 创建单例实例
const loadingManager = new LoadingManager();

// 导出常用方法
export const Loading = {
  show: () => loadingManager.show(),
  hide: () => loadingManager.hide(),
  hideAll: () => loadingManager.hideAll(),
  getStatus: () => loadingManager.getStatus(),
};

export default Loading;
