import { Button, Form, Input, Modal } from "antd"
import { LogIn } from "lucide-react"

interface LoginDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onLogin: (values: { username: string; password: string }) => Promise<void>;
  loading: boolean
  onSignupClick?: () => void
}

export function LoginDialog({ open, onOpenChange, onLogin, loading, onSignupClick }: LoginDialogProps) {
  const [form] = Form.useForm()

  const handleSubmit = async (values: { username: string; password: string }) => {
    await onLogin(values);
    form.resetFields();
  };

  return (
    <Modal
      title={
        <div className="flex items-center gap-2">
          <LogIn className="h-5 w-5" />
          <span>登录</span>
        </div>
      }
      open={open}
      onCancel={() => onOpenChange(false)}
      footer={null}
      width={400}
      maskClosable={false}
    >
      <div className="text-gray-500 mb-6">请输入您的用户名和密码登录系统</div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        autoComplete="off"
      >
        <Form.Item
          name="username"
          label="用户名"
          rules={[{ required: true, message: '请输入用户名' }]}
        >
          <Input placeholder="请输入用户名" />
        </Form.Item>

        <Form.Item
          name="password"
          label="密码"
          rules={[{ required: true, message: '请输入密码' }]}
        >
          <Input.Password placeholder="请输入密码" />
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            block
          >
            登录
          </Button>
          <div className="mt-4 text-center text-sm">
            还没有账号？
            <a 
              className="text-blue-500 hover:text-blue-600 ml-1 cursor-pointer"
              onClick={(e) => {
                e.preventDefault();
                onOpenChange(false);
                onSignupClick && onSignupClick();
              }}
            >
              立即注册
            </a>
          </div>
        </Form.Item>
      </Form>
    </Modal>
  )
}