1. 转换单个音频文件

bash
python audio_convert.py input.mp3 --output output.wav
# 或指定输出目录，会自动以原文件名生成 .wav
python audio_convert.py input.mp3 --output ./cleaned_audio/

2. 批量转换多个音频文件（输出必须是一个目录）

bash
python audio_convert.py audio1.mp3 audio2.flac audio3.wav --output ./batch_output/
3. 使用索引文件批量转换
这是处理大量文件最高效的方式。首先创建一个文本文件（如 file_list.txt），每行一个音频文件路径：

text
# file_list.txt 示例
/data/sounds/recording1.mp3
/data/sounds/sample2.m4a
# 这是一行注释
/data/sounds/lecture3.flac
然后运行命令：

bash
python audio_convert.py --index_file file_list.txt --output ./converted/
4. 允许覆盖已存在的输出文件
如果输出目录已有同名文件，需要添加 --overwrite 参数：

bash
python audio_convert.py input.aac --output existing.wav --overwrite