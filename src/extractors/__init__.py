"""
資料提取器模組

這個模組包含各種雲端提供商的資料提取器。
"""

from .aws_extractor import AWSExtractor

__all__ = ['AWSExtractor']
