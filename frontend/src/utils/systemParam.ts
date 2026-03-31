/**
 * 系统参数 API 接口
 */

// localStorage 缓存 key
const HOME_PAGE_URL_CACHE_KEY = 'datamate:homePageUrl';

/**
 * 将首页URL写入缓存
 */
export function setCachedHomePageUrl(url: string | null) {
  if (url) {
    localStorage.setItem(HOME_PAGE_URL_CACHE_KEY, url);
  } else {
    localStorage.removeItem(HOME_PAGE_URL_CACHE_KEY);
  }
}

/**
 * 同步读取缓存的首页URL
 */
export function getCachedHomePageUrl(): string | null {
  return localStorage.getItem(HOME_PAGE_URL_CACHE_KEY);
}
import { get } from '@/utils/request';

export interface SysParam {
  id: string;
  paramValue: string;
  paramType: string;
  optionList?: string;
  description?: string;
  isBuiltIn: boolean;
  canModify: boolean;
  isEnabled: boolean;
  createdAt?: string;
  updatedAt?: string;
  createdBy?: string;
  updatedBy?: string;
}

/**
 * 获取所有系统参数
 */
export async function getSystemParams(): Promise<SysParam[]> {
  const response = await get<{ code: string; message: string; data: SysParam[] }>('/api/sys-param/list');
  return response.data || [];
}

/**
 * 根据ID获取系统参数
 */
export async function getSystemParamById(paramId: string): Promise<SysParam | null> {
  try {
    const response = await get<{ code: string; message: string; data: SysParam }>(`/api/sys-param/${paramId}`);
    return response.data;
  } catch (error) {
    return null;
  }
}

/**
 * 获取首页URL配置
 */
export async function getHomePageUrl(): Promise<string | null> {
  try {
    const param = await getSystemParamById('sys.home.page.url');
    return param?.paramValue?.trim() || null;
  } catch (error) {
    console.error('Failed to get home page URL:', error);
    return null;
  }
}
