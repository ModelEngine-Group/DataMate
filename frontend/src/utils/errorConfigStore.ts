// 定义配置文件的类型接口
export interface ErrorConfig {
  [key: string]: string;
}

class ErrorConfigStore {
  // 内部存储，默认是空对象
  private config: ErrorConfig = {};

  // 标记是否已加载，防止重复加载
  private isLoaded: boolean = false;

  /**
   * 初始化方法：从服务器拉取 JSON
   */
  public async loadConfig(): Promise<void> {
    if (this.isLoaded) return;

    try {
      // 加上时间戳防止浏览器缓存 JSON 文件，确保修改后立即生效
      const response = await fetch(`/config/error-code.json?t=${new Date().getTime()}`);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      this.config = await response.json();
      this.isLoaded = true;
      console.log('[Config] Error codes loaded successfully');
    } catch (error) {
      console.error('[Config] Failed to load error codes, using defaults.', error);
      // 加载失败时，config 保持为空对象，后续逻辑会走兜底文案
    }
  }

  /**
   * 获取错误文案
   * @param code 错误码 (支持 number 或 string)
   * @returns 对应的错误文案，如果没找到返回 undefined
   */
  public getMessage(code: string | number): string | undefined {
    return this.config[String(code)];
  }
}

// 导出单例实例
export const errorConfigStore = new ErrorConfigStore();