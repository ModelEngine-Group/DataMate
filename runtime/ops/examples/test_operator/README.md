# Markdown 功能全展示 (H1)

这是一个用于测试 **React Markdown 渲染器** 的综合示例文件。
如果你能看到 **表格**、**任务列表** 和 **代码高亮**，说明你的 `remark-gfm` 和 `syntax-highlighter` 配置完美！

---

## 1. 文本格式 (Typography)

这里展示常见的文本样式：
* **加粗文本 (Bold)**
* *倾斜文本 (Italic)*
* ***加粗并倾斜 (Bold & Italic)***
* ~~删除线文本 (Strikethrough)~~ (需要 remark-gfm)
* `Inline Code` (行内代码)

---

## 2. 扩展列表 (Lists)

### 无序列表与嵌套
- 第一层列表项
  - 第二层列表项
    - 第三层列表项

### 有序列表
1. 第一步
2. 第二步
3. 第三步

### 任务列表 (Task Lists - 需要 remark-gfm)
- [x] 已完成的任务 (Finished)
- [ ] 待办任务 (Todo)
- [ ] 正在进行的任务

---

## 3. 表格 (Tables - 需要 remark-gfm)

测试表格的对齐方式（左对齐、居中、右对齐）：

| 算子名称 (Left) | 状态 (Center) | 处理速度 (Right) |
| :--- | :---: | ---: |
| MineruFormatter | ✅ 正常 | 150 ms |
| ImgDenoise | ⚠️ 警告 | 1200 ms |
| PiiDetector | ❌ 错误 | 0 ms |

---

## 4. 代码高亮 (Syntax Highlighting)

测试 `react-syntax-highlighter` 是否生效。

### Python
```python
def calculate_area(radius):
    import math
    if radius < 0:
        return None
    return math.pi * (radius ** 2)

print(f"Area: {calculate_area(5)}")
```