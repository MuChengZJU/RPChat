#!/usr/bin/env python3
"""
USB扬声器测试脚本
用于验证RPChat的TTS引擎是否能正确输出到USB扬声器
"""

import sys
import time
import subprocess
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.config_manager import ConfigManager
from core.tts.pyttsx3_engine import Pyttsx3Engine
from loguru import logger

def test_system_audio():
    """测试系统音频配置"""
    print("=== 系统音频设备检测 ===")
    
    try:
        # 检查可用的播放设备
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
        print("ALSA播放设备:")
        print(result.stdout)
        
        # 检查PulseAudio设备
        result = subprocess.run(['pactl', 'list', 'short', 'sinks'], capture_output=True, text=True)
        print("\nPulseAudio输出设备:")
        print(result.stdout)
        
        # 检查默认设备
        result = subprocess.run(['pactl', 'info'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'Default Sink:' in line:
                print(f"\n当前默认输出设备: {line.strip()}")
                break
                
    except Exception as e:
        print(f"系统音频检测失败: {e}")

def test_usb_speaker_directly():
    """直接测试USB扬声器"""
    print("\n=== 直接测试USB扬声器 ===")
    
    try:
        # 使用speaker-test测试USB设备
        print("正在播放测试音频到USB扬声器...")
        result = subprocess.run([
            'speaker-test', '-D', 'plughw:3,0', '-c', '2', '-t', 'wav', '-l', '1'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✓ USB扬声器直接测试成功")
        else:
            print(f"✗ USB扬声器直接测试失败: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("✓ USB扬声器测试音频播放中...")
    except Exception as e:
        print(f"✗ USB扬声器直接测试失败: {e}")

def test_pyttsx3_engine():
    """测试pyttsx3引擎"""
    print("\n=== 测试pyttsx3 TTS引擎 ===")
    
    try:
        # 创建配置管理器
        config_manager = ConfigManager()
        
        # 创建并初始化TTS引擎
        tts_engine = Pyttsx3Engine(config_manager)
        tts_engine.initialize()
        
        print("正在使用pyttsx3播放测试语音...")
        test_text = "你好，这是RPChat的USB扬声器测试。如果你能听到这段话，说明音频输出正常工作。"
        
        # 同步播放
        tts_engine.speak(test_text, async_mode=False)
        
        print("✓ pyttsx3测试完成")
        
        # 清理
        tts_engine.cleanup()
        
    except Exception as e:
        print(f"✗ pyttsx3测试失败: {e}")
        logger.error(f"pyttsx3测试失败: {e}")

def main():
    """主测试函数"""
    print("RPChat USB扬声器测试工具")
    print("=" * 50)
    
    # 1. 检测系统音频
    test_system_audio()
    
    # 2. 直接测试USB扬声器
    test_usb_speaker_directly()
    
    # 3. 测试TTS引擎
    test_pyttsx3_engine()
    
    print("\n=== 测试完成 ===")
    print("如果听到了测试语音，说明USB扬声器配置正确。")
    print("如果没有听到声音，请检查:")
    print("1. USB扬声器是否正确连接")
    print("2. 音量是否调节到合适级别")
    print("3. 系统音频配置是否正确")

if __name__ == "__main__":
    main() 