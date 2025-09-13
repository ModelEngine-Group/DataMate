import { createStyles } from "antd-style";

const useStyle = createStyles(({ css, token }) => {
  const { antCls } = token;
  return {
    customTable: css`
      ${antCls}-table {
        ${antCls}-table-container {
          ${antCls}-table-body, ${antCls}-table-content {
            scrollbar-width: thin;
            scrollbar-color: ${token.colorBorder} transparent;
            scrollbar-gutter: stable;
          }
        }
      }
    `,
  };
});

export default useStyle;
