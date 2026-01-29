"""API层：FastAPI应用"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger
import json
import uuid

from src.services import Stage0Service, Stage1Service, Stage2Service, Stage3Service
from src.utils import LLMClient


class GenerationRequest(BaseModel):
    """生成请求"""
    judgment_text: str
    stages: Optional[list[str]] = None  # ["0", "1", "2", "3"]
    api_key: Optional[str] = None


class GenerationResponse(BaseModel):
    """生成响应"""
    task_id: str
    status: str
    message: str
    output_path: Optional[str] = None


class TaskStatus(BaseModel):
    """任务状态"""
    task_id: str
    status: str
    stages_completed: list[str]
    current_stage: Optional[str] = None
    error: Optional[str] = None


# 全局任务存储
tasks: Dict[str, TaskStatus] = {}


app = FastAPI(
    title="金融案件测试数据生成系统",
    description="基于大模型自动生成金融案件测试卷宗",
    version="1.0.0-alpha"
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "金融案件测试数据生成系统",
        "version": "1.0.0-alpha",
        "docs": "/docs"
    }


@app.post("/api/v1/generate", response_model=GenerationResponse)
async def generate_case_data(request: GenerationRequest, background_tasks: BackgroundTasks):
    """
    生成金融案件测试数据
    
    支持的阶段：
    - 0: 判决书解析与全局规划
    - 1: 原告起诉包生成
    - 2: 被告答辩包生成
    - 3: 法院审理包生成
    """
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 默认执行所有阶段
    stages = request.stages if request.stages else ["0", "1", "2", "3"]
    
    # 初始化任务状态
    tasks[task_id] = TaskStatus(
        task_id=task_id,
        status="pending",
        stages_completed=[],
        current_stage=None
    )
    
    # 后台任务
    background_tasks.add_task(
        run_generation,
        task_id,
        request.judgment_text,
        stages,
        request.api_key
    )
    
    return GenerationResponse(
        task_id=task_id,
        status="pending",
        message="任务已提交，正在处理中"
    )


@app.get("/api/v1/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return tasks[task_id]


@app.get("/api/v1/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    """获取任务结果"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail=f"任务尚未完成，当前状态: {task.status}")
    
    # 返回完整结果文件
    output_path = Path("outputs") / f"task_{task_id}.json"
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="结果文件不存在")
    
    return FileResponse(
        path=output_path,
        media_type="application/json",
        filename=f"result_{task_id}.json"
    )


@app.get("/api/v1/tasks/{task_id}/files/{file_path:path}")
async def get_task_file(task_id: str, file_path: str):
    """获取任务生成的特定文件"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail=f"任务尚未完成，当前状态: {task.status}")
    
    # 返回指定文件
    output_path = Path("outputs") / file_path
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(path=output_path)


@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0-alpha"
    }


async def run_generation(
    task_id: str,
    judgment_text: str,
    stages: list[str],
    api_key: Optional[str]
):
    """后台执行生成任务"""
    try:
        # 更新任务状态
        tasks[task_id].status = "running"
        
        # 初始化大模型客户端
        llm_client = LLMClient(api_key=api_key) if api_key else LLMClient()
        
        # 执行阶段0
        if "0" in stages:
            tasks[task_id].current_stage = "0"
            logger.info(f"任务 {task_id}: 开始执行阶段0")
            
            stage0_service = Stage0Service(llm_client=llm_client)
            stage0_result = stage0_service.run_all(judgment_text)
            
            tasks[task_id].stages_completed.append("0")
            logger.info(f"任务 {task_id}: 阶段0完成")
        
        # 执行阶段1
        if "1" in stages:
            tasks[task_id].current_stage = "1"
            logger.info(f"任务 {task_id}: 开始执行阶段1")
            
            stage1_service = Stage1Service(llm_client=llm_client)
            stage1_result = stage1_service.run_all(stage0_result)
            
            tasks[task_id].stages_completed.append("1")
            logger.info(f"任务 {task_id}: 阶段1完成")
        
        # 执行阶段2
        if "2" in stages:
            tasks[task_id].current_stage = "2"
            logger.info(f"任务 {task_id}: 开始执行阶段2")
            
            stage2_service = Stage2Service(llm_client=llm_client)
            stage2_result = stage2_service.run_all(stage0_result)
            
            tasks[task_id].stages_completed.append("2")
            logger.info(f"任务 {task_id}: 阶段2完成")
        
        # 执行阶段3
        if "3" in stages:
            tasks[task_id].current_stage = "3"
            logger.info(f"任务 {task_id}: 开始执行阶段3")
            
            stage3_service = Stage3Service(llm_client=llm_client)
            stage3_result = stage3_service.run_all(judgment_text, stage0_result)
            
            tasks[task_id].stages_completed.append("3")
            logger.info(f"任务 {task_id}: 阶段3完成")
        
        # 整合所有结果
        final_result = {
            "task_id": task_id,
            "stages_completed": tasks[task_id].stages_completed,
            "stage0": stage0_result if "0" in stages else None,
            "stage1": stage1_result if "1" in stages else None,
            "stage2": stage2_result if "2" in stages else None,
            "stage3": stage3_result if "3" in stages else None
        }
        
        # 保存最终结果
        output_path = Path("outputs") / f"task_{task_id}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        
        # 更新任务状态
        tasks[task_id].status = "completed"
        tasks[task_id].current_stage = None
        logger.info(f"任务 {task_id}: 全部完成")
        
    except Exception as e:
        logger.error(f"任务 {task_id} 执行失败: {e}")
        tasks[task_id].status = "failed"
        tasks[task_id].current_stage = None
        tasks[task_id].error = str(e)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
