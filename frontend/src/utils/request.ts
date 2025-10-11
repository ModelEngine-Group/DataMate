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
  async handleResponse(response) {
    if (!response.ok) {
      const error = new Error(`HTTP error! status: ${response.status}`);
      error.status = response.status;
      error.statusText = response.statusText;

      try {
        const errorData = await response.json();
        error.data = errorData;
      } catch {
        // 忽略JSON解析错误
      }

      throw error;
    }

    // 检查响应是否为空
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return await response.json();
    }

    return await response.text();
  }

  /**
   * GET请求
   * @param {string} url - 请求URL
   * @param {object} params - 查询参数
   * @param {object} options - 额外的fetch选项
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

    const response = await fetch(fullURL, config);
    return this.handleResponse(response);
  }

  /**
   * POST请求
   * @param {string} url - 请求URL
   * @param {object} data - 请求体数据
   * @param {object} options - 额外的fetch选项
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
          ...options.headers,
        },
        body: data,
        ...options,
      };
    }

    const response = await fetch(this.baseURL + url, config);
    return this.handleResponse(response);
  }

  /**
   * PUT请求
   * @param {string} url - 请求URL
   * @param {object} data - 请求体数据
   * @param {object} options - 额外的fetch选项
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

    const response = await fetch(this.baseURL + url, config);
    return this.handleResponse(response);
  }

  /**
   * DELETE请求
   * @param {string} url - 请求URL
   * @param {object} params - 查询参数
   * @param {object} options - 额外的fetch选项
   */
  async delete(url, params = null, options = {}) {
    const fullURL = this.buildURL(url, params);

    const config = {
      method: "DELETE",
      redirect: "follow",
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
        "X-Requested-With": "XMLHttpRequest", // 添加此行以确保某些服务器接受请求
      },
      ...options,
      credentials: "include",
      mode: "cors", // 确保 CORS 模式
    };
    console.log(config);

    const response = await fetch(fullURL, config);
    return this.handleResponse(response);
  }

  /**
   * 下载文件
   * @param {string} url - 请求URL
   * @param {object} params - 查询参数
   * @param {string} filename - 下载文件名
   * @param {object} options - 额外的fetch选项
   */
  async download(url, params = null, filename = "download", options = {}) {
    const fullURL = this.buildURL(url, params);

    const config = {
      method: "GET",
      ...options,
    };

    const response = await fetch(fullURL, config);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const blob = await response.blob();

    // 创建下载链接
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;

    // 尝试从响应头获取文件名
    const disposition = response.headers.get("Content-Disposition");
    if (disposition && disposition.includes("filename=")) {
      const filenameMatch = disposition.match(
        /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/
      );
      if (filenameMatch) {
        filename = filenameMatch[1].replace(/['"]/g, "");
      }
    }

    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // 清理URL对象
    window.URL.revokeObjectURL(downloadUrl);

    return blob;
  }
}

// 创建默认实例
const request = new Request();

// 导出方法
export const get = request.get.bind(request);
export const post = request.post.bind(request);
export const put = request.put.bind(request);
export const del = request.delete.bind(request);
export const download = request.download.bind(request);

// 导出类，允许创建自定义实例
export { Request };

// 默认导出
export default request;
