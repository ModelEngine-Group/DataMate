import React, { Component } from "react";
import { Button, Modal } from "antd";

interface ErrorContextType {
  hasError: boolean;
  error: Error | null;
  errorInfo: { componentStack: string } | null;
}

const ErrorContext = React.createContext<ErrorContextType>({
  hasError: false,
  error: null,
  errorInfo: null,
});

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: { componentStack: string } | null;
  errorTimestamp: string | null;
}

interface ErrorBoundaryProps {
  children?: React.ReactNode;
  onReset?: () => void;
  showDetails?: boolean;
}

export default class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorTimestamp: null,
    };
  }

  static getDerivedStateFromError(error: any) {
    // 更新 state 使下一次渲染能够显示降级 UI
    return {
      hasError: true,
      error: error,
      errorTimestamp: new Date().toISOString(),
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // 错误统计
    this.setState({
      error,
      errorInfo,
      hasError: true,
    });

    // 在实际应用中，这里可以集成错误报告服务
    this.logErrorToService(error, errorInfo);

    // 开发环境下在控制台显示详细错误
    if (process.env.NODE_ENV === "development") {
      console.error("ErrorBoundary 捕获到错误:", error);
      console.error("错误详情:", errorInfo);
    }
  }

  logErrorToService = (error: Error, errorInfo: React.ErrorInfo) => {
    // 这里可以集成 Sentry、LogRocket 等错误监控服务
    const errorData = {
      error: error.toString(),
      errorInfo: errorInfo.componentStack,
      timestamp: this.state.errorTimestamp,
      url: window.location.href,
      userAgent: navigator.userAgent,
    };

    // 模拟发送错误日志
    console.log("发送错误日志到监控服务:", errorData);

    // 实际使用时取消注释并配置您的错误监控服务
    /*
    if (window.Sentry) {
      window.Sentry.captureException(error, { extra: errorInfo });
    }
    */
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorTimestamp: null,
    });

    // 可选：重新加载页面或执行其他恢复操作
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = "/";
  };

  renderErrorDetails = () => {
    const { error, errorInfo } = this.state;

    if (!this.props.showDetails) return null;

    return (
      <div className="bg-gray-100 p-4 mt-4 text-left rounded">
        <div className="mt-2">
          <strong>错误信息:</strong>
          <pre className="bg-gray-600 px-4 py-2 rounded text-white overflow-auto">
            {error?.toString()}
          </pre>
        </div>
        {errorInfo && (
          <div className="mt-2">
            <strong>组件堆栈:</strong>
            <pre className="bg-gray-600 px-4 py-2 rounded text-white overflow-auto">
              {errorInfo.componentStack}
            </pre>
          </div>
        )}
      </div>
    );
  };

  render() {
    if (this.state.hasError) {
      return (
        <Modal visible width={1000} footer={null} closable={false}>
          <div className="text-center p-6">
            <div className="text-3xl">⚠️</div>
            <h1 className="text-xl p-2">出了点问题</h1>
            <p className="text-sm text-gray-400">应用程序遇到了意外错误。</p>

            <div className="flex justify-center gap-4 my-4">
              <Button onClick={this.handleReload}>刷新页面</Button>
              <Button type="primary" onClick={this.handleGoHome}>
                返回首页
              </Button>
            </div>

            {this.renderErrorDetails()}

            <div className="mt-4 border-t border-gray-100 pt-4 text-center">
              <p className="text-sm text-gray-500">
                如果问题持续存在，请联系技术支持
              </p>
              <small className="text-xs text-gray-400">
                错误 ID: {this.state.errorTimestamp}
              </small>
            </div>
          </div>
        </Modal>
      );
    }

    return (
      <ErrorContext.Provider
        value={{
          hasError: this.state.hasError,
          error: this.state.error,
          errorInfo: this.state.errorInfo,
        }}
      >
        {this.props.children}
      </ErrorContext.Provider>
    );
  }
}

export function withErrorBoundary(
  Component: React.ComponentType
): React.ComponentType {
  return (props) => (
    <ErrorBoundary showDetails={process.env.NODE_ENV === "development"}>
      <Component {...props} />
    </ErrorBoundary>
  );
}
