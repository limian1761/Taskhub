import sys
import runpy
import os

# 获取当前脚本所在的目录
script_dir = os.path.dirname(os.path.abspath(__file__))
# 构建src目录的绝对路径
src_dir = os.path.join(script_dir, '..', 'src')

# 将src目录添加到Python路径中，以便可以导入taskhub模块
sys.path.insert(0, src_dir)

# 运行taskhub.server模块
runpy.run_module('taskhub.server', run_name='__main__')
