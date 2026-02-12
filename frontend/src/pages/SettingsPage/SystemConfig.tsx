import { Input, Select, Switch, Button, Table, Spin } from "antd";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getSysParamList, updateSysParamValue } from './settings.apis';

interface SystemParam {
  id: string;
  paramValue: string;
  description: string;
  isEnabled: boolean;
  paramType?: string;
  optionList?: string;
  isBuiltIn?: boolean;
  canModify?: boolean;
}

export default function SystemConfig() {
  const { t } = useTranslation();
  const [sysParams, setSysParams] = useState<SystemParam[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingParams, setEditingParams] = useState<Record<string, string>>({});
  const [tempEditingValues, setTempEditingValues] = useState<Record<string, string>>({});

  // 获取系统参数列表
  const fetchSysParams = async () => {
    try {
      setLoading(true);
      const response = await getSysParamList();
      setSysParams(response.data || []);
      // 初始化编辑状态
      const initialEditState: Record<string, string> = {};
      response.data?.forEach((param: SystemParam) => {
        initialEditState[param.id] = param.paramValue;
      });
      setEditingParams(initialEditState);
    } catch (error) {
      console.error('获取系统参数失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 组件加载时获取数据
  useEffect(() => {
    fetchSysParams();
  }, []);

  // 处理参数值更新 - 立即更新（用于开关和下拉框）
  const handleImmediateUpdate = async (param: SystemParam, newValue: string | boolean) => {
    try {
      const stringValue = typeof newValue === 'boolean' ? newValue.toString() : newValue;
      // 更新本地临时状态
      setTempEditingValues(prev => ({ ...prev, [param.id]: stringValue }));
      setEditingParams(prev => ({ ...prev, [param.id]: stringValue }));
      
      // 调用后端更新接口 - 修改为适应新的接口格式
      await updateSysParamValue({
        id: param.id,
        paramValue: stringValue
      });
      
      // 更新本地状态
      setSysParams(prev => prev.map(p => 
        p.id === param.id ? { ...p, paramValue: stringValue } : p
      ));
    } catch (error) {
      console.error('更新参数失败:', error);
      // 恢复原始值
      setEditingParams(prev => ({ ...prev, [param.id]: param.paramValue }));
      setTempEditingValues(prev => ({ ...prev, [param.id]: param.paramValue }));
    }
  };
  
  // 处理输入框值变化 - 仅更新临时状态
  const handleInputChange = (param: SystemParam, newValue: string) => {
    setTempEditingValues(prev => ({ ...prev, [param.id]: newValue }));
  };
  
  // 处理输入框失焦 - 发起后端请求
  const handleInputBlur = async (param: SystemParam) => {
    const newValue = tempEditingValues[param.id];
    if (newValue !== undefined && newValue !== param.paramValue) {
      try {
        // 调用后端更新接口
        await updateSysParamValue({
          id: param.id,
          paramValue: newValue
        });
        
        // 更新本地状态
        setSysParams(prev => prev.map(p => 
          p.id === param.id ? { ...p, paramValue: newValue } : p
        ));
        setEditingParams(prev => ({ ...prev, [param.id]: newValue }));
      } catch (error) {
        console.error('更新参数失败:', error);
        // 恢复原始值
        setTempEditingValues(prev => ({ ...prev, [param.id]: param.paramValue }));
        setEditingParams(prev => ({ ...prev, [param.id]: param.paramValue }));
      }
    }
  };


  // 获取选项列表 - 解析逗号分隔的字符串
  const getOptionList = (optionListStr?: string) => {
    if (!optionListStr) return [];
    try {
      // 按逗号分割字符串并去除首尾空格
      return optionListStr.split(',').map(option => ({
        value: option.trim(),
        label: option.trim()
      }));
    } catch (error) {
      console.error('解析选项列表失败:', error);
      return [];
    }
  };

  // 表格列定义
  const columns = [
    {
      title: t('settings.systemConfig.columns.paramName'),
      dataIndex: "id",
      key: "id",
      width: 180,
    },
    {
      title: t('settings.systemConfig.columns.paramValue'),
      dataIndex: "paramValue",
      key: "paramValue",
      width: 200,
      render: (value: string, record: SystemParam) => {
        // 使用临时编辑值或当前值
        const displayValue = tempEditingValues[record.id] ?? editingParams[record.id] ?? value;
        
        // 对于boolean类型，使用开关按钮
        if (record.paramType === 'boolean') {
          const isChecked = displayValue.toLowerCase() === 'true';
          return (
            <Switch
              checked={isChecked}
              onChange={(checked) => handleImmediateUpdate(record, checked)}
              disabled={!record.canModify}
            />
          );
        }
        
        // 对于有选项列表的参数，强制使用下拉框
        if (record.optionList && record.optionList.trim()) {
          const options = getOptionList(record.optionList);
          return (
            <Select
              value={displayValue}
              onChange={(newValue) => handleImmediateUpdate(record, newValue)}
              options={options}
              disabled={!record.canModify}
              style={{ width: '150px' }}
              placeholder={t('settings.systemConfig.placeholders.selectValue')}
            />
          );
        }
        
        // 对于数字类型
        if (record.paramType === 'integer' || record.paramType === 'number') {
          return (
            <Input
              type="number"
              value={displayValue}
              onChange={(e) => handleInputChange(record, e.target.value)}
              onBlur={() => handleInputBlur(record)}
              disabled={!record.canModify}
              style={{ width: '150px' }}
            />
          );
        }
        
        // 默认为文本输入
        return (
          <Input
            value={displayValue}
            onChange={(e) => handleInputChange(record, e.target.value)}
            onBlur={() => handleInputBlur(record)}
            disabled={!record.canModify}
            style={{ width: '150px' }}
          />
        );
      },
    },
    {
      title: t('settings.systemConfig.columns.description'),
      dataIndex: "description",
      key: "description",
      width: 300,
    },
    {
      title: t('settings.systemConfig.columns.isEnabled'),
      dataIndex: "isEnabled",
      key: "isEnabled",
      width: 100,
      render: (isEnabled: boolean) => (
        <Switch checked={isEnabled} disabled={true} />
      ),
    }
  ];

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-top justify-between">
        <h2 className="text-lg font-medium mb-4">{t('settings.systemConfig.title')}</h2>
        <Button onClick={fetchSysParams}>{t('settings.systemConfig.refresh')}</Button>
      </div>
      <div className="flex-1 border-card overflow-auto p-6">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <Spin size="large" />
          </div>
        ) : (
          <Table 
            columns={columns} 
            dataSource={sysParams} 
            pagination={false}
            size="middle"
            rowKey="id"
          />
        )}
      </div>
    </div>
  );
}