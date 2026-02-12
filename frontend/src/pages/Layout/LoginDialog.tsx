import { Button, Form, Input, Modal } from "antd"
import { LogIn } from "lucide-react"
import { useTranslation } from "react-i18next"

interface LoginDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onLogin: (values: { username: string; password: string }) => Promise<void>;
  loading: boolean
  onSignupClick?: () => void
}

export function LoginDialog({ open, onOpenChange, onLogin, loading, onSignupClick }: LoginDialogProps) {
  const { t } = useTranslation()
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
          <span>{t('user.loginDialog.title')}</span>
        </div>
      }
      open={open}
      onCancel={() => onOpenChange(false)}
      footer={null}
      width={400}
      maskClosable={false}
    >
      <div className="text-gray-500 mb-6">{t('user.loginDialog.description')}</div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        autoComplete="off"
      >
        <Form.Item
          name="username"
          label={t('user.fields.username')}
          rules={[{ required: true, message: t('user.validations.usernameRequired') }]}
        >
          <Input placeholder={t('user.placeholders.username')} />
        </Form.Item>

        <Form.Item
          name="password"
          label={t('user.fields.password')}
          rules={[{ required: true, message: t('user.validations.passwordRequired') }]}
        >
          <Input.Password placeholder={t('user.placeholders.password')} />
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            block
          >
            {t('user.loginDialog.submitButton')}
          </Button>
          <div className="mt-4 text-center text-sm">
            {t('user.loginDialog.noAccount')}
            <a 
              className="text-blue-500 hover:text-blue-600 ml-1 cursor-pointer"
              onClick={(e) => {
                e.preventDefault();
                onOpenChange(false);
                onSignupClick && onSignupClick();
              }}
            >
              {t('user.loginDialog.registerNow')}
            </a>
          </div>
        </Form.Item>
      </Form>
    </Modal>
  )
}