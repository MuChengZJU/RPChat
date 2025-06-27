#!/usr/bin/env python3
"""
Fish Audio TTS 引擎测试脚本 - 直接保存模式
"""

import sys
import time
from pathlib import Path
import wave

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.config_manager import ConfigManager
from core.tts.fish_audio_engine import FishAudioEngine
from fish_audio_sdk import TTSRequest
from loguru import logger

def save_stream_to_wav(filename: str, audio_stream, channels: int, sampwidth: int, framerate: int):
    """将音频流保存到WAV文件，并确保是双声道"""
    logger.info(f"正在保存音频流到文件: {filename}")
    try:
        # 将单声道数据转换为双声道
        mono_data = b''.join(list(audio_stream))
        if not mono_data:
            logger.error("音频流为空，无法保存文件。")
            return False
        
        # 将每个采样点复制一份，从单声道变为双声道
        stereo_data = b''.join(
            mono_data[i:i+sampwidth] * 2 for i in range(0, len(mono_data), sampwidth)
        )
        
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(2)  # 强制设为双声道
            wf.setsampwidth(sampwidth)
            wf.setframerate(framerate)
            wf.writeframes(stereo_data)
            
        logger.info(f"双声道音频文件已成功保存: {filename}")
        return True
    except Exception as e:
        logger.error(f"保存WAV文件失败: {e}", exc_info=True)
        return False

def main():
    """主测试函数"""
    logger.add("test_fish_audio.log", level="INFO", rotation="1 MB", mode="w")
    logger.info("--- 开始Fish Audio TTS直接保存测试 ---")

    try:
        config_manager = ConfigManager()
        config_manager.load_config()
        tts_engine = FishAudioEngine(config_manager)
        tts_engine.initialize()
        logger.info("Fish Audio引擎初始化成功")

        # 3. 请求音频并保存
        test_text = "我是奶龙，我才是奶龙。"
        logger.info(f"即将获取测试语音: '{test_text}'")
        
        # 使用配置文件中指定的 voice_id
        reference_id = config_manager.get("audio.fish_audio.voice_id", "default_voice_id")
        logger.info(f"使用 Reference ID (音色ID): {reference_id}")
        
        request = TTSRequest(
            text=test_text, 
            reference_id=reference_id, # 使用正确的参数名
            format="wav" # 明确请求WAV格式
        )
        audio_stream = tts_engine.session.tts(request)
        
        save_success = save_stream_to_wav(
            "test_output.wav",
            audio_stream,
            channels=1, # 源是单声道
            sampwidth=2,
            framerate=tts_engine.sample_rate
        )
        
        if save_success:
            print("\n✅ 音频流已成功保存到 'test_output.wav' 文件！")
            print("\n下一步，请在终端中运行以下命令来播放它：")
            print("  aplay test_output.wav\n")
            print("如果这次声音是清晰的，我们就大功告成了！")
        else:
            print("\n❌ 保存文件失败，请检查 test_fish_audio.log 日志。")

    except Exception as e:
        logger.error(f"测试过程中出现严重错误: {e}", exc_info=True)
        print(f"\n❌ 测试失败: {e}")
    finally:
        logger.info("--- 测试结束 ---")

if __name__ == "__main__":
    main() 