import {message} from "antd";
import Loading from "./loading";
import {errorConfigStore} from "@/utils/errorConfigStore.ts";

/**
 * 通用请求工具类
 */
class Request {
  constructor(baseURL = "") {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      "Content-Type": "application/json",
      Accept: "*/*",
    };
    // 请求拦截器列表
    this.requestInterceptors = [];
    // 响应拦截器列表
    this.responseInterceptors = [];
  }

  _count = 0;
  $interval;

  get count() {
    return this._count;
  }

  set count(value) {
    clearTimeout(this.$interval);
    if (value > 0) {
      Loading.show();
    }
    if (value <= 0) {
      this.$interval = setTimeout(() => {
        Loading.hide();
      }, 300);
    }
    this._count = value >= 0 ? value : 0;
  }

  /**
   * 添加请求拦截器
   */
  addRequestInterceptor(interceptor) {
    this.requestInterceptors.push(interceptor);
  }

  /**
   * 添加响应拦截器
   */
  addResponseInterceptor(interceptor) {
    this.responseInterceptors.push(interceptor);
  }

  /**
   * 执行请求拦截器
   */
  async executeRequestInterceptors(config) {
    let processedConfig = { ...config };
    for (const interceptor of this.requestInterceptors) {
      processedConfig = (await interceptor(processedConfig)) || processedConfig;
    }

    return processedConfig;
  }

  /**
   * 执行响应拦截器
   */
  async executeResponseInterceptors(response, config) {
    let processedResponse = response;

    for (const interceptor of this.responseInterceptors) {
      processedResponse =
        (await interceptor(processedResponse, config)) || processedResponse;
    }

    return processedResponse;
  }

  /**
   * 创建支持进度监听的XMLHttpRequest
   */
  createXHRWithProgress(url, config, onProgress, onDownloadProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", url);

      // 设置请求头
      if (config.headers) {
        Object.keys(config.headers).forEach((key) => {
          xhr.setRequestHeader(key, config.headers[key]);
        });
      }

      // 监听上传进度
      xhr.upload.addEventListener("progress", function (event) {
        if (event.lengthComputable) {
          if (onProgress) {
            onProgress(event);
          }
          if (onDownloadProgress) {
            onDownloadProgress(event);
          }
        }
      });

      // 请求完成处理
      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          let response;
          try {
            // 尝试解析JSON
            const contentType = xhr.getResponseHeader("content-type");
            if (contentType && contentType.includes("application/json")) {
              response = JSON.parse(xhr.responseText);
            } else {
              response = xhr.responseText;
            }
          } catch (e) {
            response = xhr.responseText;
          }

          resolve({
            data: response,
            status: xhr.status,
            statusText: xhr.statusText,
            headers: xhr.getAllResponseHeaders(),
            xhr: xhr,
          });
        } else {
          reject(new Error(`HTTP error! status: ${xhr.status}`));
        }
      });

      // 请求错误
      xhr.addEventListener("error", function () {
        console.error("网络错误");
        if (onError) onError(new Error("网络错误"));
      });

      // 请求中止
      xhr.addEventListener("abort", function () {
        console.log("上传已取消");
        if (onError) onError(new Error("上传已取消"));
      });

      xhr.send(config.body);

      return xhr; // 返回 xhr 对象以便后续控制
    });
  }

  /**
   * 构建完整URL
   */
  buildURL(url, params) {
    const fullURL = this.baseURL + url;
    if (!params) return fullURL;

    const searchParams = new URLSearchParams();
    Object.keys(params).forEach((key) => {
      if (params[key] !== undefined && params[key] !== null) {
        searchParams.append(key, params[key]);
      }
    });

    const queryString = searchParams.toString();
    return queryString ? `${fullURL}?${queryString}` : fullURL;
  }

  /**
   * 处理响应
   */
  async handleResponse(response, config) {
    // 如果显示了loading，需要隐藏
    if (config.showLoading) {
      this.count--;
    }

    // 执行响应拦截器
    const processedResponse = await this.executeResponseInterceptors(
      response,
      config
    );

    if (!processedResponse.ok) {
      const error = new Error(
        `HTTP error! status: ${processedResponse.status}`
      );
      error.status = processedResponse.status;
      error.statusText = processedResponse.statusText;

      try {
        error.data = await processedResponse.json();
        // message.error(`请求失败，错误信息: ${errorData.message}`);
      } catch {
        // 忽略JSON解析错误
      }

      throw error;
    }

    // 检查响应是否为空
    const contentType = processedResponse.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return await processedResponse.json();
    }

    return await processedResponse.text();
  }

  /**
   * 处理XHR响应
   */
  async handleXHRResponse(xhrResponse, config) {
    // 模拟fetch响应格式用于拦截器
    const mockResponse = {
      ok: xhrResponse.status >= 200 && xhrResponse.status < 300,
      status: xhrResponse.status,
      statusText: xhrResponse.statusText,
      headers: {
        get: (key) => xhrResponse.xhr.getResponseHeader(key),
      },
    };

    // 执行响应拦截器
    await this.executeResponseInterceptors(mockResponse, config);

    if (!mockResponse.ok) {
      const error = new Error(`HTTP error! status: ${xhrResponse.status}`);
      error.status = xhrResponse.status;
      error.statusText = xhrResponse.statusText;
      error.data = xhrResponse.data;
      message.error(`请求失败，错误信息: ${xhrResponse.statusText}`);
      throw error;
    }

    return xhrResponse.data;
  }

  /**
   * 通用请求方法
   */
  async request(url, config) {
    // 处理showLoading参数
    if (config.showLoading) {
      this.count++;
    }

    // 执行请求拦截器
    const processedConfig = await this.executeRequestInterceptors(config);

    // 如果需要进度监听，使用XMLHttpRequest
    if (config.onUploadProgress || config.onDownloadProgress) {
      const xhrResponse = await this.createXHRWithProgress(
        url,
        processedConfig,
        config.onUploadProgress,
        config.onDownloadProgress
      );
      return await this.handleXHRResponse(xhrResponse, processedConfig);
    }
    // 否则使用fetch
    if (processedConfig.body instanceof FormData) {
    }
    const response = await fetch(url, processedConfig);
    return await this.handleResponse(response, processedConfig);
  }

  /**
   * GET请求
   * @param {string} url - 请求URL
   * @param {object} params - 查询参数
   * @param {object} options - 额外的fetch选项，包括showLoading, onDownloadProgress
   */
  async get(url, params = null, options = {}) {
    const fullURL = this.buildURL(url, params);

    const config = {
      method: "GET",
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
      ...options,
    };

    return this.request(fullURL, config);
  }

  /**
   * POST请求
   * @param {string} url - 请求URL
   * @param {object} data - 请求体数据
   * @param {object} options - 额外的fetch选项，包括showLoading, onUploadProgress, onDownloadProgress
   */
  async post(url, data = {}, options = {}) {
    let config = {
      method: "POST",
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    };

    const isFormData = data instanceof FormData;
    if (isFormData) {
      config = {
        method: "POST",
        headers: {
          ...options.headers, // FormData不需要Content-Type
        },
        body: data,
        ...options,
      };
    }
    return this.request(this.baseURL + url, config);
  }

  /**
   * PUT请求
   * @param {string} url - 请求URL
   * @param {object} data - 请求体数据
   * @param {object} options - 额外的fetch选项，包括showLoading, onUploadProgress, onDownloadProgress
   */
  async put(url, data = null, options = {}) {
    const config = {
      method: "PUT",
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    };

    return this.request(this.baseURL + url, config);
  }

  /**
   * DELETE请求
   * @param {string} url - 请求URL
   * @param {object} params - 查询参数或请求体数据
   * @param {object} options - 额外的fetch选项，包括showLoading
   */
  async delete(url, params = null, options = {}) {
    let fullURL = this.baseURL + url;
    let config = {
      method: "DELETE",
      redirect: "follow",
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "include",
      mode: "cors",
      body: params ? JSON.stringify(params) : undefined,
      ...options,
    };

    // 判断params是否应该作为查询参数或请求体
    if (params && typeof params === "object" && !Array.isArray(params)) {
      // 如果params是普通对象，检查是否应该作为查询参数
      const isQueryParams =
        Object.keys(params).length === 1 &&
        (Object.prototype.hasOwnProperty.call(params, "id") ||
          Object.prototype.hasOwnProperty.call(params, "ids") ||
          Object.prototype.hasOwnProperty.call(params, "prefix"));

      if (isQueryParams) {
        fullURL = this.buildURL(url, params);
      } else {
        // 作为请求体发送
        config.body = JSON.stringify(params);
      }
    } else if (Array.isArray(params)) {
      // 数组形式的数据作为请求体发送
      config.body = JSON.stringify(params);
    } else if (params) {
      // 其他情况作为查询参数
      fullURL = this.buildURL(url, { id: params });
    }

    return this.request(fullURL, config);
  }

  /**
   * 下载文件
   * @param {string} url - 请求URL
   * @param {object} params - 查询参数
   * @param {string} filename - 下载文件名
   * @param {string} action - 行为，包括下载文件和预览文件
   * @param {object} options - 额外的fetch选项，包括showLoading, onDownloadProgress
   */
  async download(url, params = null, filename = "", action = "download", options = {}) {
    const fullURL = this.buildURL(url, params);

    const config = {
      method: "GET",
      responseType: "blob",
      ...options,
    };

    // 执行请求拦截器
    const processedConfig = await this.executeRequestInterceptors(config);

    let blob;
    let name = filename;

    // 如果需要下载进度监听，使用XMLHttpRequest
    if (config.onDownloadProgress) {
      const xhrResponse = await this.createXHRWithProgress(
        fullURL,
        { ...processedConfig, responseType: "blob" },
        null,
        config.onDownloadProgress
      );

      if (xhrResponse.status < 200 || xhrResponse.status >= 300) {
        throw new Error(`HTTP error! status: ${xhrResponse.status}`);
      }

      blob = xhrResponse.xhr.response;
      name =
        name ||
        xhrResponse.headers.get("Content-Disposition")?.split("filename=")[1] ||
        "download";
    } else {
      // 使用fetch
      const response = await fetch(fullURL, processedConfig);

      // 执行响应拦截器
      const processedResponse = await this.executeResponseInterceptors(
        response,
        processedConfig
      );

      if (!processedResponse.ok) {
        throw new Error(`HTTP error! status: ${processedResponse.status}`);
      }

      blob = await processedResponse.blob();
      name =
        name ||
        response.headers.get("Content-Disposition")?.split("filename=")[1] ||
        `download_${Date.now()}`;
    }

    if (action === "download") {
      // 创建下载链接
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = filename ?? name;

      // 添加到DOM并触发下载
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // 清理URL对象
      window.URL.revokeObjectURL(downloadUrl);
    } else if (action === "preview") {
      // 预览逻辑 - 返回Blob URL和相关信息
      const blobUrl = window.URL.createObjectURL(blob);

      // 可以返回更多信息用于预览
      return {
        blob,
        blobUrl,
        filename: name,
        size: blob.size,
        // 自动清理的钩子
        revoke: () => window.URL.revokeObjectURL(blobUrl)
      };
    }

    return blob;
  }

  /**
   * 上传文件（专门的上传方法）
   * @param {string} url - 上传URL
   * @param {FormData|File} data - 文件数据
   * @param {object} options - 选项，包括onUploadProgress回调
   */
  async upload(url, data, options = {}) {
    let formData = data;

    // 如果传入的是File对象，包装成FormData
    if (data instanceof File) {
      formData = new FormData();
      formData.append("file", data);
    }

    return this.post(url, formData, {
      ...options,
      showLoading: options.showLoading !== false, // 上传默认显示loading
      onUploadProgress: options.onUploadProgress, // 上传进度回调
    });
  }
}

// 创建默认实例
const request = new Request();

// 添加默认请求拦截器 - Token处理
request.addRequestInterceptor((config) => {
  const session = localStorage.getItem("session");
  if (session) {
    try {
      const sessionData = JSON.parse(session);
      if (sessionData.token) {
        config.headers = {
          ...config.headers,
          Authorization: `Bearer ${sessionData.token}`,
        };
      }
    } catch (e) {
      console.error('Failed to parse session data', e);
    }
  }
  return config;
});

// --- 常量配置 ---
const DEFAULT_ERROR_MSG = '系统繁忙，请稍后重试';
// 需要触发重新登录的 Code 集合 (包含 HTTP 401 和 业务 Token 过期码)
const AUTH_ERR_CODES = [401, '401'];

// --- 辅助函数：防抖处理登录失效 ---
let isRelogging = false;
const handleLoginRedirect = () => {
  if (isRelogging) return;
  isRelogging = true;

  // 1. 清除 Session / Token
  localStorage.removeItem('session');

  // 2. 触发登录弹窗事件 (根据你的架构，这里可以是 dispatch event 或 router 跳转)
  const loginEvent = new CustomEvent('show-login');
  window.dispatchEvent(loginEvent);

  // 3. 重置标志位 (3秒后才允许再次触发)
  setTimeout(() => {
    isRelogging = false;
  }, 3000);
};

request.addResponseInterceptor(async (response, config) => {
  // 1. 基础防御：如果没有 response (比如网络直接断了)，可能需要走 reject
  if (!response) {
    return Promise.reject(new Error('网络连接异常'));
  }

  const { status } = response;

  // ------------------ 修改重点开始 ------------------

  let resData: {};

  try {
    // 关键点 1: response.data 在原生 fetch 中是不存在的，必须用 .json() 解析
    // 关键点 2: 必须用 .clone()，因为流只能读一次。读了克隆的，原版 response 还能留给外面用
    // 关键点 3: 必须 await，因为读取流是异步的
    resData = await response.clone().json();
  } catch (e) {
    // 如果后端返回的不是 JSON (比如 404 HTML 页面，或者空字符串)，json() 会报错
    // 这里捕获异常，保证 resData 至少是个空对象，不会导致后面取值 crash
    console.warn('响应体不是有效的JSON:', e);
    resData = {};
  }

  // 2. 获取统一的错误码 (转为字符串以匹配 JSON 配置的 Key)
  // 优先取后端 body 里的 business code，没有则取 HTTP status
  const code = resData.code ?? status;
  const codeStr = String(code);

  // 3. 判断成功 (根据你的后端约定：200/0 为成功)
  // 如果是成功状态，直接返回 response，不拦截
  if (status === 200 && (code === 200 || code === 0 || code === '0')) {
    return response;
  }

  // --- 进入错误处理分支 ---

  // 4. 获取错误文案 (这是我们优化的核心)
  // 优先级：Store配置文件 > 后端返回的 message > 默认文案
  const configMsg = errorConfigStore.getMessage(codeStr);
  const errorMsg = configMsg || resData.message || resData.msg || DEFAULT_ERROR_MSG;

  // 5. 打印日志 (方便开发排查)
  console.warn(`[API Error] Path: ${config?.url}, Code: ${codeStr}, Msg: ${errorMsg}`);

  // 6. 全局弹窗提示 (排除 401，因为 401 通常直接弹登录框，不需要再弹个 Toast)
  if (!AUTH_ERR_CODES.includes(code) && !AUTH_ERR_CODES.includes(codeStr)) {
    // TODO: 替换为你实际的 UI 弹窗，例如 message.error(errorMsg)
    message.error(errorMsg);
  }

  // 7. 处理 Token 过期 / 未登录
  if (AUTH_ERR_CODES.includes(code) || AUTH_ERR_CODES.includes(codeStr)) {
    handleLoginRedirect();
  }

  // 8. 返回拒绝的 Promise，中断后续业务代码的 .then() 执行
  // 将处理过的 errorMsg 塞回去，方便组件内 catch 使用
  return Promise.reject({
    ...resData,
    message: errorMsg,
    status: status
  });
});

// 导出方法
export const get = request.get.bind(request);
export const post = request.post.bind(request);
export const put = request.put.bind(request);
export const del = request.delete.bind(request);
export const download = request.download.bind(request);
export const upload = request.upload.bind(request);

// 导出类，允许创建自定义实例
export { Request };

// 默认导出
export default request;
