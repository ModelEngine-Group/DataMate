import {Steps, Typography} from "antd";
import {useNavigate} from "react-router";

export default function TemplateOperatorTable({ template }: { template: any }) {
  const navigate = useNavigate();

  return template?.instance?.length > 0 && (
    <>
      <Steps
        progressDot
        direction="vertical"
        items={Object.values(template?.instance).map((item) => ({
          title: <Typography.Link
            onClick={() => navigate(`/data/operator-market/plugin-detail/${item?.id}`)}
          >
            {item?.name}
          </Typography.Link>,
          description: item?.description,
          status: "finish"
        }))}
        className="overflow-auto"
      />
    </>
  );
}