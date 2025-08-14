'use client';

import React from 'react';
import { Layout, Menu, Avatar, Dropdown, Space, Button } from 'antd';
import {
  DashboardOutlined,
  DatabaseOutlined,
  AppstoreOutlined,
  CleaningServicesOutlined,
  ExperimentOutlined,
  TagsOutlined,
  CheckCircleOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { useRouter } from 'next/navigation';

const { Header, Sider, Content } = Layout;

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const router = useRouter();

  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: '工作台',
      onClick: () => router.push('/dashboard'),
    },
    {
      key: 'data-management',
      icon: <DatabaseOutlined />,
      label: '数据管理',
      children: [
        {
          key: 'data-sources',
          label: '数据源',
          onClick: () => router.push('/data-management/sources'),
        },
        {
          key: 'datasets',
          label: '数据集',
          onClick: () => router.push('/data-management/datasets'),
        },
        {
          key: 'metadata',
          label: '元数据',
          onClick: () => router.push('/data-management/metadata'),
        },
      ],
    },
    {
      key: 'operator-market',
      icon: <AppstoreOutlined />,
      label: '算子市场',
      onClick: () => router.push('/operator-market'),
    },
    {
      key: 'data-processing',
      icon: <CleaningServicesOutlined />,
      label: '数据处理',
      children: [
        {
          key: 'data-cleaning',
          label: '数据清洗',
          onClick: () => router.push('/data-processing/cleaning'),
        },
        {
          key: 'data-synthesis',
          label: '数据合成',
          onClick: () => router.push('/data-processing/synthesis'),
        },
        {
          key: 'data-annotation',
          label: '数据标注',
          onClick: () => router.push('/data-processing/annotation'),
        },
        {
          key: 'data-evaluation',
          label: '数据评估',
          onClick: () => router.push('/data-processing/evaluation'),
        },
      ],
    },
    {
      key: 'pipeline',
      icon: <ExperimentOutlined />,
      label: '流程编排',
      onClick: () => router.push('/pipeline'),
    },
    {
      key: 'monitoring',
      icon: <CheckCircleOutlined />,
      label: '监控中心',
      onClick: () => router.push('/monitoring'),
    },
  ];

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人设置',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={240} theme="light">
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          borderBottom: '1px solid #f0f0f0',
          fontWeight: 'bold',
          fontSize: '18px'
        }}>
          Data-Engine
        </div>
        <Menu
          mode="inline"
          defaultSelectedKeys={['dashboard']}
          style={{ height: 'calc(100vh - 64px)', borderRight: 0 }}
          items={menuItems}
        />
      </Sider>
      <Layout>
        <Header style={{ 
          background: '#fff', 
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid #f0f0f0'
        }}>
          <div />
          <Space>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Button type="text">
                <Space>
                  <Avatar size="small" icon={<UserOutlined />} />
                  <span>管理员</span>
                </Space>
              </Button>
            </Dropdown>
          </Space>
        </Header>
        <Content style={{ 
          margin: '24px',
          background: '#fff',
          borderRadius: '8px',
          overflow: 'auto'
        }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
