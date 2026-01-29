# -*- coding: utf-8 -*-
from datamate.core.base_op import OPERATORS

# 注册算子
# 文件夹名必须是 scene_simulator_operator
OPERATORS.register_module(
    module_name='LicenseSceneSimulatorOperator',
    module_path="ops.user.license_scene_simulator_operator.process"
)