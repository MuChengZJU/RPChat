"""
音频处理工具模块
提供音频文件处理和格式转换功能
"""

import wave
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
from loguru import logger

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False
    logger.warning("soundfile 未安装，部分音频功能可能不可用")


class AudioProcessor:
    """音频处理器"""
    
    @staticmethod
    def get_audio_info(file_path: str) -> Optional[dict]:
        """
        获取音频文件信息
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            dict: 音频信息字典，包含采样率、通道数、时长等
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"音频文件不存在: {file_path}")
                return None
            
            if SOUNDFILE_AVAILABLE:
                with sf.SoundFile(str(file_path)) as f:
                    info = {
                        'sample_rate': f.samplerate,
                        'channels': f.channels,
                        'frames': f.frames,
                        'duration': f.frames / f.samplerate,
                        'format': f.format,
                        'subtype': f.subtype
                    }
                    return info
            else:
                # 使用wave模块处理WAV文件
                if file_path.suffix.lower() == '.wav':
                    with wave.open(str(file_path), 'rb') as w:
                        info = {
                            'sample_rate': w.getframerate(),
                            'channels': w.getnchannels(),
                            'frames': w.getnframes(),
                            'duration': w.getnframes() / w.getframerate(),
                            'format': 'WAV',
                            'sample_width': w.getsampwidth()
                        }
                        return info
                else:
                    logger.warning(f"不支持的音频格式: {file_path.suffix}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取音频信息失败: {e}")
            return None
    
    @staticmethod
    def convert_to_wav(input_path: str, output_path: str, 
                      sample_rate: int = 16000, channels: int = 1) -> bool:
        """
        转换音频文件为WAV格式
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            sample_rate: 目标采样率
            channels: 目标声道数
            
        Returns:
            bool: 转换是否成功
        """
        try:
            if not SOUNDFILE_AVAILABLE:
                logger.error("soundfile 未安装，无法进行音频格式转换")
                return False
            
            # 读取音频文件
            data, orig_sr = sf.read(input_path)
            
            # 转换为单声道
            if len(data.shape) > 1 and channels == 1:
                data = np.mean(data, axis=1)
            
            # 重采样（简化版本，实际应用中可能需要更复杂的重采样算法）
            if orig_sr != sample_rate:
                # 这里使用简单的线性插值，实际应用中建议使用更好的重采样算法
                new_length = int(len(data) * sample_rate / orig_sr)
                data = np.interp(
                    np.linspace(0, len(data) - 1, new_length),
                    np.arange(len(data)),
                    data
                )
            
            # 确保输出目录存在
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入WAV文件
            sf.write(str(output_path), data, sample_rate)
            
            logger.info(f"音频转换成功: {input_path} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"音频转换失败: {e}")
            return False
    
    @staticmethod
    def trim_silence(audio_data: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        """
        去除音频数据中的静音部分
        
        Args:
            audio_data: 音频数据数组
            threshold: 静音阈值
            
        Returns:
            np.ndarray: 去除静音后的音频数据
        """
        try:
            # 计算音频能量
            energy = np.abs(audio_data)
            
            # 找到非静音部分的开始和结束
            non_silent = energy > threshold
            
            if not np.any(non_silent):
                # 如果全是静音，返回原数据
                return audio_data
            
            # 找到第一个和最后一个非静音样本
            start_idx = np.argmax(non_silent)
            end_idx = len(non_silent) - np.argmax(non_silent[::-1]) - 1
            
            return audio_data[start_idx:end_idx + 1]
            
        except Exception as e:
            logger.error(f"去除静音失败: {e}")
            return audio_data
    
    @staticmethod
    def normalize_audio(audio_data: np.ndarray, target_db: float = -20.0) -> np.ndarray:
        """
        音频归一化
        
        Args:
            audio_data: 音频数据数组
            target_db: 目标分贝值
            
        Returns:
            np.ndarray: 归一化后的音频数据
        """
        try:
            # 计算当前RMS值
            rms = np.sqrt(np.mean(audio_data ** 2))
            
            if rms == 0:
                return audio_data
            
            # 计算目标RMS值
            target_rms = 10 ** (target_db / 20.0)
            
            # 归一化
            normalized_data = audio_data * (target_rms / rms)
            
            # 防止溢出
            normalized_data = np.clip(normalized_data, -1.0, 1.0)
            
            return normalized_data
            
        except Exception as e:
            logger.error(f"音频归一化失败: {e}")
            return audio_data
    
    @staticmethod
    def split_audio_by_silence(audio_data: np.ndarray, sample_rate: int,
                              silence_threshold: float = 0.01,
                              min_silence_duration: float = 0.5) -> list:
        """
        根据静音分割音频
        
        Args:
            audio_data: 音频数据数组
            sample_rate: 采样率
            silence_threshold: 静音阈值
            min_silence_duration: 最小静音持续时间（秒）
            
        Returns:
            list: 分割后的音频片段列表
        """
        try:
            min_silence_samples = int(min_silence_duration * sample_rate)
            
            # 找到静音区域
            energy = np.abs(audio_data)
            is_silent = energy < silence_threshold
            
            # 找到静音开始和结束位置
            silent_regions = []
            in_silence = False
            silence_start = 0
            
            for i, silent in enumerate(is_silent):
                if silent and not in_silence:
                    silence_start = i
                    in_silence = True
                elif not silent and in_silence:
                    if i - silence_start >= min_silence_samples:
                        silent_regions.append((silence_start, i))
                    in_silence = False
            
            # 处理音频结尾的静音
            if in_silence and len(audio_data) - silence_start >= min_silence_samples:
                silent_regions.append((silence_start, len(audio_data)))
            
            # 根据静音区域分割音频
            segments = []
            last_end = 0
            
            for start, end in silent_regions:
                if start > last_end:
                    segments.append(audio_data[last_end:start])
                last_end = end
            
            # 添加最后一个片段
            if last_end < len(audio_data):
                segments.append(audio_data[last_end:])
            
            # 过滤掉太短的片段
            min_segment_length = sample_rate * 0.1  # 至少0.1秒
            segments = [seg for seg in segments if len(seg) >= min_segment_length]
            
            return segments
            
        except Exception as e:
            logger.error(f"音频分割失败: {e}")
            return [audio_data]
    
    @staticmethod
    def calculate_audio_features(audio_data: np.ndarray, sample_rate: int) -> dict:
        """
        计算音频特征
        
        Args:
            audio_data: 音频数据数组
            sample_rate: 采样率
            
        Returns:
            dict: 音频特征字典
        """
        try:
            features = {}
            
            # 基本特征
            features['duration'] = len(audio_data) / sample_rate
            features['sample_rate'] = sample_rate
            features['samples'] = len(audio_data)
            
            # 幅度特征
            features['max_amplitude'] = float(np.max(np.abs(audio_data)))
            features['mean_amplitude'] = float(np.mean(np.abs(audio_data)))
            features['rms'] = float(np.sqrt(np.mean(audio_data ** 2)))
            
            # 能量特征
            features['energy'] = float(np.sum(audio_data ** 2))
            features['log_energy'] = float(np.log(features['energy'] + 1e-8))
            
            # 零交叉率
            zero_crossings = np.where(np.diff(np.sign(audio_data)))[0]
            features['zero_crossing_rate'] = len(zero_crossings) / len(audio_data)
            
            # 频域特征（简化版本）
            if len(audio_data) > 0:
                fft = np.fft.fft(audio_data)
                magnitude = np.abs(fft[:len(fft)//2])
                
                features['spectral_centroid'] = float(
                    np.sum(magnitude * np.arange(len(magnitude))) / (np.sum(magnitude) + 1e-8)
                )
                
                features['spectral_rolloff'] = float(np.percentile(magnitude, 85))
            
            return features
            
        except Exception as e:
            logger.error(f"计算音频特征失败: {e}")
            return {}
    
    @staticmethod
    def save_audio_segment(audio_data: np.ndarray, output_path: str, 
                          sample_rate: int = 16000) -> bool:
        """
        保存音频片段
        
        Args:
            audio_data: 音频数据数组
            output_path: 输出文件路径
            sample_rate: 采样率
            
        Returns:
            bool: 保存是否成功
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if SOUNDFILE_AVAILABLE:
                sf.write(str(output_path), audio_data, sample_rate)
            else:
                # 使用wave模块保存WAV文件
                with wave.open(str(output_path), 'wb') as w:
                    w.setnchannels(1)  # 单声道
                    w.setsampwidth(2)  # 16位
                    w.setframerate(sample_rate)
                    
                    # 转换为16位整数
                    audio_int16 = (audio_data * 32767).astype(np.int16)
                    w.writeframes(audio_int16.tobytes())
            
            logger.info(f"音频片段已保存: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存音频片段失败: {e}")
            return False 