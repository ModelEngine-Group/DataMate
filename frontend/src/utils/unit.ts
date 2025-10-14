// 字节数转换为更大单位的方法
export const formatBytes = (bytes: number): string => {
  if (!bytes) return "0 B";

  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  const k = 1024;
  const decimals = 3;

  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const value = bytes / Math.pow(k, i);

  // 如果是整数则不显示小数点，否则最多显示3位小数并去除末尾的0
  const formattedValue =
    value % 1 === 0
      ? value.toString()
      : parseFloat(value.toFixed(decimals)).toString();

  return `${formattedValue} ${units[i]}`;
};

export const formatDateTime = (dateString: string): string => {
  if (!dateString) return "";
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
};

export const formatDate = (dateString: string): string => {
  if (!dateString) return "";
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
};

export const formatTime = (dateString: string): string => {
  if (!dateString) return "";
  const date = new Date(dateString);
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");

  return `${hours}:${minutes}:${seconds}`;
};

export const formatDuration = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds} 秒`;
  } else if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return secs === 0 ? `${mins} 分钟` : `${mins} 分钟 ${secs} 秒`;
  } else {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return mins === 0 ? `${hrs} 小时` : `${hrs} 小时 ${mins} 分钟`;
  }
};

export const formatNumber = (num: number): string => {
  if (num >= 1e9) {
    return (num / 1e9).toFixed(2).replace(/\.?0+$/, "") + "B";
  } else if (num >= 1e6) {
    return (num / 1e6).toFixed(2).replace(/\.?0+$/, "") + "M";
  } else if (num >= 1e3) {
    return (num / 1e3).toFixed(2).replace(/\.?0+$/, "") + "K";
  } else {
    return num.toString();
  }
};

export const formatPercentage = (num: number): string => {
  return (num * 100).toFixed(2).replace(/\.?0+$/, "") + "%";
};

export const truncateString = (str: string, maxLength: number): string => {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength) + "...";
};

export const capitalizeFirstLetter = (str: string): string => {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1);
};

export const lowercaseFirstLetter = (str: string): string => {
  if (!str) return str;
  return str.charAt(0).toLowerCase() + str.slice(1);
};

export const slugify = (str: string): string => {
  return str
    .toLowerCase()
    .trim()
    .replace(/[\s\W-]+/g, "-")
    .replace(/^-+|-+$/g, "");
};

export const unslugify = (str: string): string => {
  return str.replace(/-/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
};

export const isValidEmail = (email: string): boolean => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email.toLowerCase());
};

export const isValidURL = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

export const isValidPhoneNumber = (phone: string): boolean => {
  const re = /^\+?[1-9]\d{1,14}$/; // E.164 format
  return re.test(phone);
};

export const generateRandomString = (length: number): string => {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let result = "";
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
};

export const generateUUID = (): string => {
  // 简单的UUID生成方法
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

export const sleep = (ms: number): Promise<void> => {
  return new Promise((resolve) => setTimeout(resolve, ms));
};

export const debounce = <F extends (...args: any[]) => any>(
  func: F,
  wait: number
): F => {
  let timeout: NodeJS.Timeout;
  return function (this: any, ...args: any[]) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  } as F;
};

export const throttle = <F extends (...args: any[]) => any>(
  func: F,
  limit: number
): F => {
  let inThrottle: boolean;
  return function (this: any, ...args: any[]) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  } as F;
};

export const deepClone = <T>(obj: T): T => {
  return JSON.parse(JSON.stringify(obj));
};

export const mergeObjects = <T, U>(obj1: T, obj2: U): T & U => {
  return { ...obj1, ...obj2 };
};

export const pick = <T, K extends keyof T>(obj: T, keys: K[]): Pick<T, K> => {
  const result = {} as Pick<T, K>;
  keys.forEach((key) => {
    if (key in obj) {
      result[key] = obj[key];
    }
  });
  return result;
};

export const omit = <T, K extends keyof T>(obj: T, keys: K[]): Omit<T, K> => {
  const result = { ...obj } as T;
  keys.forEach((key) => {
    if (key in result) {
      delete result[key];
    }
  });
  return result;
};

export const groupBy = <T, K extends keyof T>(
  array: T[],
  key: K
): Record<string, T[]> => {
  return array.reduce((result, currentItem) => {
    const groupKey = String(currentItem[key]);
    if (!result[groupKey]) {
      result[groupKey] = [];
    }
    result[groupKey].push(currentItem);
    return result;
  }, {} as Record<string, T[]>);
};

export const uniqueBy = <T, K extends keyof T>(array: T[], key: K): T[] => {
  const seen = new Set();
  return array.filter((item) => {
    const k = item[key];
    return seen.has(k) ? false : seen.add(k);
  });
};

export const sortBy = <T, K extends keyof T>(
  array: T[],
  key: K,
  ascending = true
): T[] => {
  return [...array].sort((a, b) => {
    if (a[key] < b[key]) return ascending ? -1 : 1;
    if (a[key] > b[key]) return ascending ? 1 : -1;
    return 0;
  });
};
export const chunkArray = <T>(array: T[], size: number): T[][] => {
  const result: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    result.push(array.slice(i, i + size));
  }
  return result;
};
export const arrayDifference = <T>(arr1: T[], arr2: T[]): T[] => {
  const set2 = new Set(arr2);
  return arr1.filter((item) => !set2.has(item));
};

export const arrayIntersection = <T>(arr1: T[], arr2: T[]): T[] => {
  const set2 = new Set(arr2);
  return arr1.filter((item) => set2.has(item));
};

export const arrayUnion = <T>(arr1: T[], arr2: T[]): T[] => {
  return Array.from(new Set([...arr1, ...arr2]));
};

export const flattenArray = <T>(array: T[][]): T[] => {
  return array.reduce((acc, val) => acc.concat(val), []);
};

export const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // 这里可以添加提示消息
  };


// 示例用法
// console.log(formatBytes(1024)); // "1 KB"
// console.log(formatDateTime("2023-10-01T12:34:56Z")); // "2023-10-01 12:34:56"
// console.log(isValidEmail("test@example.com")); // true
// console.log(generateUUID()); // "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"

// 你可以根据需要添加更多的实用函数

// 例如：深拷贝对象、合并对象、数组去重、节流、防抖等

// 这些函数可以根据你的项目需求进行调整和扩展

// 记得添加适当的类型注解以提高代码的可读性和可维护性

// 以及编写单元测试以确保函数的正确性
