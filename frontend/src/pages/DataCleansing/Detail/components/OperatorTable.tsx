import {Steps, Typography} from "antd";
import {CleansingTask} from "@/pages/DataCleansing/cleansing.model.ts";
import {useNavigate} from "react-router";

export default function OperatorTable({ task }: { task: CleansingTask }) {
  const navigate = useNavigate();

  return (
    <>
        <Steps
          progressDot
          direction="vertical"
          items={Object.values(task?.instance).map((item) => ({
            title: <Typography.Link
              onClick={() => navigate(`/data/operator-market/plugin-detail/${item.id}`)}
            >
              {item.name}
            </Typography.Link>,
            description: item.description,
            status: "finish"
          }))}
          className="overflow-auto"
        />
    </>
  );
}
