'''
为整个项目提供绝对路径，保证可移植性
'''
import os

# 这里默认后续使用该函数的文件都在项目根目录的下下级
def get_project_root() -> str:
    """
    通过os包获取工程所在的根目录
    return: 字符串根目录
    """
    # 当前文件的绝对路径
    current_file = os.path.abspath(__file__)
    # 获取工程的根目录，先获取文件所在的文件夹绝对路径
    current_dir = os.path.dirname(current_file)
    # 获取工程根目录
    project_root = os.path.dirname(current_dir)

    return project_root


def get_abs_path(relative_path: str) -> str:
    """
    param: relative_path-传入相对路径
    return: 得到绝对路径
    """
    project_root = get_project_root()
    return os.path.join(project_root, relative_path)


if __name__ == '__main__':
    print(get_abs_path("config/config.txt"))