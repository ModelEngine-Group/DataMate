# -- encoding: utf-8 --
from collections import deque


class TrieNode:
    def __init__(self, value):
        self.value = value
        self.child = dict()
        self.fail = None
        self.word = None


class AhoCorasic:
    """AC自动机算法进行目标字符串搜索"""

    def __init__(self, words):
        self._root = add_fail_pointer(build_trie(words))

    def search(self, text: str, special_symbols: set):
        """
        匹配敏感词。

        Args:
            text: 文本
            special_symbols: 特殊字符（需跳过）
        Returns:
            匹配成功的字符串列表
        """
        seq_list = []
        node = self._root

        valid_len = 0  # 当前遍历的有效长度
        for i, s in enumerate(text):
            if s in special_symbols:  # 跳过特殊字符
                if valid_len != 0:
                    valid_len += 1
                continue

            matched = True
            while s not in node.child:  # 当node.child没有字符s
                if node == self._root:  # 当node为root（无node.fail），有效长度归0且跳出
                    valid_len = 0
                    matched = False
                    break
                elif node.fail == self._root:  # node.fail为root场景，有效长度归0，但可继续
                    valid_len = 0
                node = node.fail  # 移动到失败指针节点
            if not matched:
                continue

            node = node.child.get(s)
            valid_len += 1
            if node.word:  # node是单词尾字母
                sensitive_word = text[i - valid_len + 1:i + 1]
                seq_list.append(sensitive_word)
        seq_list = list(set(seq_list))
        return seq_list


def build_trie(words: list):
    """
    构建前缀树。

    Args:
        words: 敏感词列表。
    Returns:
        前缀树根节点。
    """
    root = TrieNode('root')
    for word in words:
        node = root
        for s in word:
            if s not in node.child:
                node.child[s] = TrieNode(s)
            node = node.child[s]
        if not node.word:
            node.word = {word}
        else:
            node.word.add(word)
    return root


def add_fail_pointer(root: TrieNode):
    """
    为前缀树添加失败指针。
    步骤：
    1. 从root开始逐层将node和node.parent以二元组存放队列。root没有fail指针，root.child的失败指针即为root。
    2. 对于root和root.child以外的node，查询node.parent.fail.child。
    3. 如果存在node.parent.fail.child.value == node.value，则构建node.fail = node.parent.fail.child.value。

    Args:
        root: 前缀树根节点。
    returns:
        添加失败指针后的前缀树根节点。
    """
    queue = deque()
    queue.appendleft((root, None))
    while len(queue) > 0:
        node_parent = queue.pop()
        curr, parent = node_parent[0], node_parent[1]
        for sub in curr.child.values():
            queue.appendleft((sub, curr))
        if parent is None:
            continue
        elif parent is root:
            curr.fail = root
        else:
            parent_fail = parent.fail
            while parent_fail and curr.value not in parent_fail.child:
                parent_fail = parent_fail.fail
            if parent_fail:
                curr.fail = parent_fail.child[curr.value]
            else:
                curr.fail = root
    return root
