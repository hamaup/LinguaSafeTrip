"""
検索半径設定の統一管理
各種検索機能で使用する半径設定を一元管理
"""
from typing import Dict
from enum import Enum


class SearchType(str, Enum):
    """検索タイプ"""
    SHELTER = "shelter"           # 避難所検索
    DISASTER = "disaster"         # 災害情報検索
    GENERAL = "general"           # 一般検索
    EMERGENCY = "emergency"       # 緊急時検索
    EXTENDED = "extended"         # 拡張検索


class DefaultRadiusConfig:
    """検索半径設定"""
    
    # 基本検索半径（km）
    SHELTER_DEFAULT = 3.0         # 避難所検索：3km
    SHELTER_EMERGENCY = 5.0       # 緊急時避難所検索：5km
    SHELTER_EXTENDED = 10.0       # 拡張避難所検索：10km
    
    DISASTER_DEFAULT = 10.0       # 災害情報検索：10km
    DISASTER_EXTENDED = 50.0      # 拡張災害情報検索：50km
    
    GENERAL_DEFAULT = 10.0        # 一般検索：10km
    EMERGENCY_DEFAULT = 100.0     # 緊急時検索：100km
    
    @classmethod
    def get_radius(cls, search_type: SearchType, is_emergency: bool = False, is_extended: bool = False) -> float:
        """
        検索タイプと状況に応じた半径を取得
        
        Args:
            search_type: 検索タイプ
            is_emergency: 緊急時フラグ
            is_extended: 拡張検索フラグ
            
        Returns:
            float: 検索半径（km）
        """
        if search_type == SearchType.SHELTER:
            if is_emergency:
                return cls.SHELTER_EMERGENCY
            elif is_extended:
                return cls.SHELTER_EXTENDED
            else:
                return cls.SHELTER_DEFAULT
                
        elif search_type == SearchType.DISASTER:
            if is_extended:
                return cls.DISASTER_EXTENDED
            else:
                return cls.DISASTER_DEFAULT
                
        elif search_type == SearchType.EMERGENCY:
            return cls.EMERGENCY_DEFAULT
            
        else:  # GENERAL
            return cls.GENERAL_DEFAULT
    
    @classmethod
    def get_all_radii(cls) -> Dict[str, float]:
        """全ての半径設定を辞書で取得"""
        return {
            "shelter_default": cls.SHELTER_DEFAULT,
            "shelter_emergency": cls.SHELTER_EMERGENCY,
            "shelter_extended": cls.SHELTER_EXTENDED,
            "disaster_default": cls.DISASTER_DEFAULT,
            "disaster_extended": cls.DISASTER_EXTENDED,
            "general_default": cls.GENERAL_DEFAULT,
            "emergency_default": cls.EMERGENCY_DEFAULT,
        }