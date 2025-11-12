import {Steps, Typography} from "antd";
import {useNavigate} from "react-router";

export default function OperatorTable({ task }: { task: any }) {
  const navigate = useNavigate();

  return task?.instance?.length > 0 && (
    <>
        <Steps
          progressDot
          direction="vertical"
          items={Object.values(task?.instance).map((item) => ({
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
