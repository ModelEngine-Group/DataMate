import { useDragOperators } from "./useDragOperators";
import { useOperatorOperations } from "./useOperatorOperations";
import OperatorConfig from "../components/OperatorConfig";
import OperatorLibrary from "../components/OperatorLibrary";
import OperatorOrchestration from "../components/OperatorOrchestration";

export function useCreateStepTwo() {
  const {
    operators,
    selectedOperators,
    templates,
    currentTemplate,
    configOperator,
    currentStep,
    categoryOptions,
    handlePrev,
    handleNext,
    setCurrentTemplate,
    setConfigOperator,
    setSelectedOperators,
    handleConfigChange,
    toggleOperator,
    removeOperator,
  } = useOperatorOperations();

  const {
    handleDragStart,
    handleDragEnd,
    handleContainerDragOver,
    handleContainerDragLeave,
    handleItemDragOver,
    handleItemDragLeave,
    handleItemDrop,
    handleDropToContainer,
  } = useDragOperators({
    operators: selectedOperators,
    setOperators: setSelectedOperators,
  });

  const renderStepTwo = (
    <div className="flex w-full h-full">
      {/* 左侧算子库 */}
      <OperatorLibrary
        categoryOptions={categoryOptions}
        selectedOperators={selectedOperators}
        operatorList={operators}
        toggleOperator={toggleOperator}
        handleDragStart={handleDragStart}
      />

      {/* 中间算子编排区域 */}
      <OperatorOrchestration
        selectedOperators={selectedOperators}
        configOperator={configOperator}
        templates={templates}
        currentTemplate={currentTemplate}
        setSelectedOperators={setSelectedOperators}
        setConfigOperator={setConfigOperator}
        setCurrentTemplate={setCurrentTemplate}
        removeOperator={removeOperator}
        handleDragStart={handleDragStart}
        handleContainerDragLeave={handleContainerDragLeave}
        handleContainerDragOver={handleContainerDragOver}
        handleItemDragOver={handleItemDragOver}
        handleItemDragLeave={handleItemDragLeave}
        handleItemDrop={handleItemDrop}
        handleDropToContainer={handleDropToContainer}
        handleDragEnd={handleDragEnd}
      />

      {/* 右侧参数配置面板 */}
      <OperatorConfig
        selectedOp={configOperator}
        handleConfigChange={handleConfigChange}
      />
    </div>
  );
  return {
    renderStepTwo,
    selectedOperators,
    currentStep,
    handlePrev,
    handleNext,
  };
}
