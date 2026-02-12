import { Button } from "antd";
import { useTranslation } from "react-i18next";
const DevelopmentInProgress = ({ showHome = true, showTime = "" }) => {
  const { t } = useTranslation();
  return (
    <div className="mt-40 flex flex-col items-center justify-center">
      <div className="hero-icon">🚧</div>
      <h1 className="text-2xl font-bold">{t('components.developmentInProgress.title')}</h1>
      {showTime && (
        <p className="mt-4">
          {t('components.developmentInProgress.description', { time: `<b>${showTime}</b>` })}
        </p>
      )}
      {showHome && (
        <Button
          type="primary"
          className="mt-6"
          onClick={() => {
            window.location.href = "/";
          }}
        >
          {t('components.developmentInProgress.goHome')}
        </Button>
      )}
    </div>
  );
};

export default DevelopmentInProgress;
