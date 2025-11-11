import {Steps} from "antd";
import {CleansingTask} from "@/pages/DataCleansing/cleansing.model.ts";

export default function OperatorTable({ task }: { task: CleansingTask }) {

  return (
    <>
        <Steps
          progressDot
          current={task?.instance.length}
          direction="vertical"
          items={Object.values(task?.instance).map((item) => ({
            title: item.name,
            description: item.description
          }))}
          className="overflow-auto"
        />
    </>
  );
}
