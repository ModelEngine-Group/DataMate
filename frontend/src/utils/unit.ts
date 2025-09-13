// 字节数转换为更大单位的方法
export const formatBytes = (bytes: number): string => {
  if (bytes === 0) return "0 B";
  
  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  const k = 1024;
  const decimals = 3;
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const value = bytes / Math.pow(k, i);
  
  // 如果是整数则不显示小数点，否则最多显示3位小数并去除末尾的0
  const formattedValue = value % 1 === 0 
    ? value.toString() 
    : parseFloat(value.toFixed(decimals)).toString();
  
  return `${formattedValue} ${units[i]}`;
};