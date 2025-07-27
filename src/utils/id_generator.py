import time
import random
import string

class IDGenerator:
    """ID生成器，生成简短且唯一的ID"""
    
    @staticmethod
    def _generate_random_string(length=4):
        """生成指定长度的随机字符串"""
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choices(chars, k=length))
    
    @classmethod
    def generate_task_id(cls):
        """生成任务ID: t-时间戳后4位-4位随机字符"""
        timestamp = str(int(time.time()))[-4:]
        random_str = cls._generate_random_string(4)
        return f"t{timestamp}-{random_str}"
    
    @classmethod
    def generate_report_id(cls):
        """生成报告ID: r-时间戳后4位-4位随机字符"""
        timestamp = str(int(time.time()))[-4:]
        random_str = cls._generate_random_string(4)
        return f"r{timestamp}-{random_str}"
    
    @classmethod
    def generate_lease_id(cls):
        """生成租约ID: l-时间戳后4位-4位随机字符"""
        timestamp = str(int(time.time()))[-4:]
        random_str = cls._generate_random_string(4)
        return f"l{timestamp}-{random_str}"
