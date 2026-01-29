import os
import pandas as pd
from docxtpl import DocxTemplate
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings("ignore")

DATA_NAME = "data.csv"
MAX_WORKERS = 5


def init_dirs(input_dir, output_dir):
    """初始化输入/输出目录，不存在则创建"""
    for dir_path in [input_dir, output_dir]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"📁 创建目录：{dir_path}")


def load_data(input_dir):
    """加载CSV数据"""
    data_path = os.path.join(input_dir, DATA_NAME)
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"❌ 未找到数据文件：{data_path}")

    df = pd.read_csv(data_path, encoding="utf-8-sig")
    df = df.apply(lambda x: x.str.strip("\t ") if x.dtype == "object" else x)
    df = df.fillna("无")

    print(f"📊 成功加载CSV数据，共 {len(df)} 条记录")
    return df


def load_template(template_path):
    """加载Word模板"""
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"❌ 未找到模板文件：{template_path}")

    tpl = DocxTemplate(template_path)
    print(f"✅ 成功加载Word模板：{template_path}")
    return tpl


def fill_template(row, template, output_dir):
    """填充单条数据到Word模板"""
    try:
        context = row.to_dict()
        name = context.get("姓名", f"未命名_{row.name}")
        output_filename = f"{name}.docx"
        output_path = os.path.join(output_dir, output_filename)

        template.render(context)
        template.save(output_path)

        return f"✅ 生成成功：{output_filename}"
    except Exception as e:
        return f"❌ 生成失败（行{row.name}）：{str(e)[:50]}..."


def batch_fill_templates(template_path, input_dir, output_dir):
    """批量填充Word模板"""
    init_dirs(input_dir, output_dir)
    tpl = load_template(template_path)
    df = load_data(input_dir)

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_row = {
            executor.submit(fill_template, df.iloc[i], tpl, output_dir): i
            for i in range(len(df))
        }

        for future in as_completed(future_to_row):
            row_idx = future_to_row[future]
            try:
                result = future.result()
                results.append(result)
                if (len(results) % 20 == 0) or (len(results) == len(df)):
                    print(f"进度：{len(results)}/{len(df)} | 最新：{result}")
            except Exception as e:
                results.append(f"❌ 线程执行失败（行{row_idx}）：{str(e)[:50]}...")

    success = [r for r in results if "✅" in r]
    fail = [r for r in results if "❌" in r]
    print("\n" + "-" * 50)
    print(f"📋 批量处理完成：成功 {len(success)} 条 | 失败 {len(fail)} 条")

    return output_dir, len(success)
