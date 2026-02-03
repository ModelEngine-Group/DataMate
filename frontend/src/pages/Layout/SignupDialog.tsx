import { Button, Form, Input, Modal } from "antd"
import { UserPlus } from "lucide-react"
import { useTranslation } from "react-i18next"

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
  const { t } = useTranslation()
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
          <span>{t('user.signupDialog.title')}</span>
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
      <div className="text-gray-500 mb-6">{t('user.signupDialog.description')}</div>

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
          name="email"
          label={t('user.fields.email')}
          rules={[
            { required: true, message: t('user.validations.emailRequired') },
            { type: "email", message: t('user.validations.emailInvalid') },
          ]}
        >
          <Input placeholder={t('user.placeholders.email')} type="email" />
        </Form.Item>

        <Form.Item
          name="password"
          label={t('user.fields.password')}
          rules={[
            { required: true, message: t('user.validations.passwordRequired') },
            { min: 6, message: t('user.validations.passwordTooShort') },
          ]}
        >
          <Input.Password placeholder={t('user.placeholders.password')} />
        </Form.Item>

        <Form.Item
          name="confirmPassword"
          label={t('user.fields.confirmPassword')}
          dependencies={["password"]}
          rules={[
            { required: true, message: t('user.validations.confirmPasswordRequired') },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue("password") === value) {
                  return Promise.resolve()
                }
                return Promise.reject(new Error(t('user.validations.passwordMismatch')))
              },
            }),
          ]}
        >
          <Input.Password placeholder={t('user.placeholders.confirmPassword')} />
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            block
          >
            {t('user.signupDialog.submitButton')}
          </Button>
          <div className="mt-4 text-center text-sm">
            {t('user.signupDialog.hasAccount')}
            <a 
              className="text-blue-500 hover:text-blue-600 ml-1 cursor-pointer"
              onClick={(e) => {
                e.preventDefault();
                onOpenChange(false);
                onLoginClick && onLoginClick();
              }}
            >
              {t('user.signupDialog.loginNow')}
            </a>
          </div>
        </Form.Item>
      </Form>
    </Modal>
  )
}