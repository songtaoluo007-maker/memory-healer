"""存档API"""
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.save import SaveSlot
from backend.models.user import User
from backend.api.auth import get_current_user

router = APIRouter(prefix="/api/save", tags=["save"])


class SaveRequest(BaseModel):
    slot_id: int
    slot_name: str = ""
    game_state: dict
    scene_id: str = ""
    play_time: int = 0

    @validator('slot_id')
    def validate_slot_id(cls, v):
        if v < 0 or v > 10:
            raise ValueError('slot_id必须在0-10之间')
        return v

    @validator('slot_name')
    def validate_slot_name(cls, v):
        if len(v) > 50:
            raise ValueError('存档名称长度不能超过50')
        return v.strip()

    @validator('scene_id')
    def validate_scene_id(cls, v):
        if v and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('scene_id格式无效')
        return v

    @validator('play_time')
    def validate_play_time(cls, v):
        if v < 0 or v > 86400:
            raise ValueError('游戏时间无效')
        return v


@router.post("/save")
def save_game(
    req: SaveRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """保存游戏（需要登录，存档绑定用户）"""
    existing = db.query(SaveSlot).filter(
        SaveSlot.slot_id == req.slot_id,
        SaveSlot.user_id == user.id,
    ).first()

    if existing:
        existing.slot_name = req.slot_name
        existing.game_state = json.dumps(req.game_state, ensure_ascii=False)
        existing.scene_id = req.scene_id
        existing.play_time = req.play_time
    else:
        slot = SaveSlot(
            slot_id=req.slot_id,
            user_id=user.id,
            slot_name=req.slot_name,
            game_state=json.dumps(req.game_state, ensure_ascii=False),
            scene_id=req.scene_id,
            play_time=req.play_time,
        )
        db.add(slot)
    db.commit()
    return {"success": True}


class LoadRequest(BaseModel):
    slot_id: int


@router.post("/load")
def load_game(
    req: LoadRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """读取存档（只能读自己的）"""
    slot = db.query(SaveSlot).filter(
        SaveSlot.slot_id == req.slot_id,
        SaveSlot.user_id == user.id,
    ).first()
    if not slot:
        raise HTTPException(status_code=404, detail="存档不存在")
    return {
        "slot_id": slot.slot_id,
        "slot_name": slot.slot_name,
        "game_state": json.loads(slot.game_state),
        "scene_id": slot.scene_id,
        "play_time": slot.play_time,
        "saved_at": str(slot.updated_at),
    }


@router.get("/list")
def list_saves(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取当前用户的所有存档"""
    slots = db.query(SaveSlot).filter(
        SaveSlot.user_id == user.id,
    ).order_by(SaveSlot.slot_id).all()
    return {
        "saves": [
            {
                "slot_id": s.slot_id,
                "slot_name": s.slot_name,
                "scene_id": s.scene_id,
                "play_time": s.play_time,
                "saved_at": str(s.updated_at),
            }
            for s in slots
        ]
    }


@router.delete("/delete/{slot_id}")
def delete_save(
    slot_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """删除存档（只能删自己的）"""
    slot = db.query(SaveSlot).filter(
        SaveSlot.slot_id == slot_id,
        SaveSlot.user_id == user.id,
    ).first()
    if slot:
        db.delete(slot)
        db.commit()
    return {"success": True}
