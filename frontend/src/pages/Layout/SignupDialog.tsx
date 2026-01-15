import { Button, Form, Input, Modal } from "antd"
import { UserPlus } from "lucide-react"

interface SignupDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSignup: (values: {
    username: string;
    email: string;
    password: string;
    confirmPassword: string
  }) => Promise<void>
  loading: boolean
  onLoginClick?: () => void
}

export function SignupDialog({ open, onOpenChange, onSignup, loading, onLoginClick }: SignupDialogProps) {
  const [form] = Form.useForm()

  const handleSubmit = async (values: any) => {
    await onSignup(values);
    form.resetFields();
  };

  return (
    <Modal
      title={
        <div className="flex items-center gap-2">
          <UserPlus className="h-5 w-5" />
          <span>注册</span>
        </div>
      }
      open={open}
      onCancel={() => {
        onOpenChange(false)
        form.resetFields()
      }}
      footer={null}
      width={400}
      maskClosable={false}
    >
      <div className="text-gray-500 mb-6">创建您的账户以使用 DataMate 系统</div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        autoComplete="off"
      >
        <Form.Item
          name="username"
          label="用户名"
          rules={[{ required: true, message: "请输入用户名" }]}
        >
          <Input placeholder="请输入用户名" />
        </Form.Item>

        <Form.Item
          name="email"
          label="邮箱"
          rules={[
            { required: true, message: "请输入邮箱" },
            { type: "email", message: "请输入有效的邮箱地址" },
          ]}
        >
          <Input placeholder="请输入邮箱" type="email" />
        </Form.Item>

        <Form.Item
          name="password"
          label="密码"
          rules={[
            { required: true, message: "请输入密码" },
            { min: 6, message: "密码至少需要6个字符" },
          ]}
        >
          <Input.Password placeholder="请输入密码" />
        </Form.Item>

        <Form.Item
          name="confirmPassword"
          label="确认密码"
          dependencies={["password"]}
          rules={[
            { required: true, message: "请确认密码" },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue("password") === value) {
                  return Promise.resolve()
                }
                return Promise.reject(new Error("两次输入的密码不一致"))
              },
            }),
          ]}
        >
          <Input.Password placeholder="请再次输入密码" />
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            block
          >
            注册
          </Button>
          <div className="mt-4 text-center text-sm">
            已有账号？
            <a 
              className="text-blue-500 hover:text-blue-600 ml-1 cursor-pointer"
              onClick={(e) => {
                e.preventDefault();
                onOpenChange(false);
                onLoginClick && onLoginClick();
              }}
            >
              立即登录
            </a>
          </div>
        </Form.Item>
      </Form>
    </Modal>
  )
}