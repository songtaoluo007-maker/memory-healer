"""存档API"""
import json
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.save import SaveSlot

router = APIRouter(prefix="/api/save", tags=["save"])


class SaveRequest(BaseModel):
    slot_id: int
    slot_name: str = ""
    game_state: dict
    scene_id: str = ""
    play_time: int = 0


@router.post("/save")
def save_game(req: SaveRequest, db: Session = Depends(get_db)):
    """保存游戏"""
    existing = db.query(SaveSlot).filter(SaveSlot.slot_id == req.slot_id).first()
    if existing:
        existing.slot_name = req.slot_name
        existing.game_state = json.dumps(req.game_state, ensure_ascii=False)
        existing.scene_id = req.scene_id
        existing.play_time = req.play_time
    else:
        slot = SaveSlot(
            slot_id=req.slot_id,
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
def load_game(req: LoadRequest, db: Session = Depends(get_db)):
    """读取存档"""
    slot = db.query(SaveSlot).filter(SaveSlot.slot_id == req.slot_id).first()
    if not slot:
        return {"error": "存档不存在"}
    return {
        "slot_id": slot.slot_id,
        "slot_name": slot.slot_name,
        "game_state": json.loads(slot.game_state),
        "scene_id": slot.scene_id,
        "play_time": slot.play_time,
        "saved_at": str(slot.updated_at),
    }


@router.get("/list")
def list_saves(db: Session = Depends(get_db)):
    """获取所有存档"""
    slots = db.query(SaveSlot).order_by(SaveSlot.slot_id).all()
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
def delete_save(slot_id: int, db: Session = Depends(get_db)):
    """删除存档"""
    slot = db.query(SaveSlot).filter(SaveSlot.slot_id == slot_id).first()
    if slot:
        db.delete(slot)
        db.commit()
    return {"success": True}
