from fastapi import APIRouter

router = APIRouter()

@router.get("/script-wizard")
async def script_wizard():
    return {"message": "Script Wizard coming soon"}
