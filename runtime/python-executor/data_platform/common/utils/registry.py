# -*- coding: utf-8 -*-

from loguru import logger


class Registry(object):
    """注册器类，用于注册所有的算子."""

    def __init__(self, name: str):

        self._name = name
        self._modules = {}

    @property
    def name(self):
        return self._name

    @property
    def modules(self):
        return self._modules

    def list(self):
        """日志打印注册器中所有的算子"""
        for m in self._modules.keys():
            logger.info(f'{self._name}\t{m}')

    def get(self, module_key):
        return self._modules.get(module_key, None)

    def register_module(self, module_name: str = None, module_cls: type = None, module_path: str = None, force=False):
        """
        使用特定的模块名称注册模块

        :param module_name: 模块名称
        :param module_cls:  模块类定义
        :param module_path: 模块所在的路径
        :param force: 是否强行覆盖同名模块，默认值为False.

        Example:
            >>> registry = Registry()
            >>> @registry.register_module()
            >>> class TextFormatter:
            >>>     pass

            >>> class TextFormatter2:
            >>>     pass
            >>> registry.register_module( module_name='text_formatter2', module_cls=TextFormatter2)
        """
        if not (module_name is None or isinstance(module_name, str)):
            raise TypeError(f'module_name must be either of None, str,'
                            f'got {type(module_name)}')
        if module_cls is not None:
            self._register_module(module_name=module_name,
                                  module_cls=module_cls,
                                  force=force)
            return module_cls

        elif module_cls is None and isinstance(module_path, str):
            self._register_module(module_name=module_name,
                                  module_path=module_path,
                                  force=force)
            return module_path

        def _register(module_cls):
            """
            注册其中module_cls为None是，返回装饰器函数
            """
            self._register_module(module_name=module_name,
                                  module_cls=module_cls,
                                  force=force)
            return module_cls

        return _register

    def _register_module(self, module_name=None, module_cls=None, module_path=None, force=False):
        """
        注册模块到注册器中.

        :param module_name: 模块名称
        :param module_cls:  模块类定义
        :param force: 是否强行覆盖同名模块，默认值为False.
        """

        if module_name is None and module_cls is not None:
            module_name = module_cls.__name__

        if module_name in self._modules:
            if module_cls is not None and module_cls == self._modules[module_name]:
                return

            if module_path is not None and module_path == self._modules[module_name]:
                return

            if not force:
                raise KeyError(
                    f'{module_name} is already registered in {self._name}, content: {self.modules.keys()}')

        if module_cls is not None:
            self._modules[module_name] = module_cls

        elif module_path is not None:
            self._modules[module_name] = module_path
