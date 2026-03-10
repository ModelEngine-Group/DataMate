#!/bin/bash
# 遇到错误即退出
set -e

# 使用 -n 判断环境变量 HOME_PAGE_URL 是否非空（即已设置且有值）
if [ -n "$HOME_PAGE_URL" ]; then
    echo "检测到 HOME_PAGE_URL 环境变量已配置，值为: $HOME_PAGE_URL。准备更新数据库..."

    # 只有变量非空时，才会进入这里执行 SQL
    psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "datamate" -v my_url="$HOME_PAGE_URL" <<-EOSQL

        UPDATE t_sys_param
        SET param_value = :'my_url'
        WHERE id = 'sys.home.page.url';

EOSQL

    echo "sys.home.page.url 更新完成！"
else
    # 如果变量为空或未设置，打印提示并直接跳过
    echo "未配置 HOME_PAGE_URL 环境变量或值为空，跳过 sys.home.page.url 的更新操作。"
fi