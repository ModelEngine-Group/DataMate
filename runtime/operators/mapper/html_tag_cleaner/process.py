#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: HTML标签去除插件
Create: 2025/01/13
"""
import logging as logger
import re
import time
from typing import List, Dict, Any

from data_platform.core.base_op import Mapper


class HtmlTagCleaner(Mapper):
    """移除文档中html标签，如 <html>，<dev>，<p>等，不对xml文档做处理"""
    tag_list = [
        '<a>', '<abbr>', '<acronym>', '<address>', '<applet>', '<area>', '<article>', '<aside>',
        '<audio>', '<b>', '<base>', '<basefont>', '<bdi>', '<bdo>', '<bgsound>', '<big>', '<blink>',
        '<blockquote>', '<body>', '<br>', '<button>', '<canvas>', '<caption>', '<center>', '<cite>',
        '<code>', '<col>', '<colgroup>', '<command>', '<content>', '<data>', '<datalist>', '<dd>',
        '<del>', '<details>', '<dfn>', '<dialog>', '<dir>', '<div>', '<dl>', '<dt>', '<em>',
        '<embed>', '<fieldset>', '<figcaption>', '<figure>', '<font>', '<footer>', '<form>', '<frame>',
        '<frameset>', '<h1>', '<h2>', '<h3>', '<h4>', '<h5>', '<h6>', '<head>', '<header>', '<hgroup>',
        '<hr>', '<html>', '<i>', '<iframe>', '<image>', '<img>', '<input>', '<ins>', '<isindex>',
        '<kbd>', '<keygen>', '<label>', '<legend>', '<li>', '<link>', '<listing>', '<main>', '<map>',
        '<mark>', '<marquee>', '<menu>', '<menuitem>', '<meta>', '<meter>', '<nav>', '<nobr>', '<noembed>',
        '<noframes>', '<noscript>', '<object>', '<ol>', '<optgroup>', '<option>', '<output>', '<p>',
        '<param>', '<picture>', '<plaintext>', '<pre>', '<progress>', '<q>', '<rp>', '<rt>', '<rtc>',
        '<ruby>', '<s>', '<samp>', '<script>', '<section>', '<select>', '<shadow>', '<small>',
        '<source>', '<spacer>', '<span>', '<strike>', '<strong>', '<style>', '<sub>', '<summary>',
        '<sup>', '<template>', '<textarea>', '<tfoot>', '<thead>', '<time>', '<title>', '<track>', '<tt>', '<u>',
        '<ul>', '<var>', '<video>', '<wbr>', '<xmp>'
    ]
    preserved_attr_list = ['colspan', 'rowspan']  # 需要保留的标签属性列表

    @staticmethod
    def _remove_specified_tags(input_data: str, specified_tags: List):
        """移除指定html标签及其属性值"""
        html_tag_pattern = '|'.join(
            map(lambda tag: rf'{re.escape(tag[:-1])}(\s[^>]*)?>|</{re.escape(tag[1:-1])}>', specified_tags))
        cleaned_text = re.sub(html_tag_pattern, '', input_data, flags=re.IGNORECASE)
        return cleaned_text

    @staticmethod
    def _remove_tag_attributes(input_data: str, preserved_attrs: List):
        """移除html标签内的属性值，同时保留指定的属性"""
        tag_pattern = r'<(\w+)(\s+[^<>]*?)?>'
        attr_pattern = r'\s*(\w+)="([^"]+)"'

        def __remove_unwanted_attrs(m):
            def __remove_attrs(x):
                if x.group(1) in preserved_attrs:
                    return x.group(0)
                else:
                    return ''

            return re.sub(attr_pattern, __remove_attrs, m.group(0))

        cleaned_text = re.sub(tag_pattern, __remove_unwanted_attrs, input_data)
        return cleaned_text

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        if sample[self.filetype_key] != "xml":
            sample[self.text_key] = self._remove_html_tags(sample[self.text_key])
            logger.info("fileName: %s, method: HtmlTagCleaner costs %.6f s",
                        sample[self.filename_key], time.time() - start)
        else:
            logger.info("fileName: %s, method: HtmlTagCleaner, The file is xml!",
                        sample[self.filename_key])
        return sample

    def _remove_html_tags(self, input_data: str):
        # 去除常见的html标签及其属性值（不包括<table>、<tbody>、<tr>、<td>、<th>）
        cleaned_text = self._remove_specified_tags(input_data, self.tag_list)
        # 去除表格标签内的属性值（不包括colspan、rowspan属性），eg:<td class="td8" rowspan="3"> —> <td rowspan="3">
        cleaned_text = self._remove_tag_attributes(cleaned_text, self.preserved_attr_list)
        return cleaned_text
