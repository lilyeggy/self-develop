from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from spirit.core.config import settings
from spirit.api import api_router
from spirit.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="个人成长Agent系统 - 支持即时思考记录、思路展开、复盘回顾和认知提升",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Spirit - 个人成长Agent</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                max-width: 600px;
                width: 100%;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
                font-size: 2.5em;
            }
            .subtitle {
                color: #666;
                margin-bottom: 30px;
                font-size: 1.1em;
            }
            .feature {
                display: flex;
                align-items: center;
                padding: 15px;
                margin: 10px 0;
                background: #f8f9fa;
                border-radius: 10px;
                transition: transform 0.2s;
            }
            .feature:hover {
                transform: translateX(10px);
            }
            .feature-icon {
                font-size: 2em;
                margin-right: 15px;
            }
            .feature-text h3 {
                color: #333;
                margin-bottom: 5px;
            }
            .feature-text p {
                color: #666;
                font-size: 0.9em;
            }
            .btn {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 30px;
                border-radius: 10px;
                text-decoration: none;
                margin-top: 20px;
                font-weight: 600;
                transition: transform 0.2s;
            }
            .btn:hover {
                transform: scale(1.05);
            }
            .api-link {
                display: block;
                margin-top: 15px;
                color: #667eea;
                text-decoration: none;
            }
            .api-link:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Spirit</h1>
            <p class="subtitle">个人成长Agent系统</p>
            
            <div class="feature">
                <span class="feature-icon">💭</span>
                <div class="feature-text">
                    <h3>即时思考记录</h3>
                    <p>快速记录碎片化思考，保留时间维度信息</p>
                </div>
            </div>
            
            <div class="feature">
                <span class="feature-icon">🌟</span>
                <div class="feature-text">
                    <h3>思路展开</h3>
                    <p>AI辅助提供问题延伸和相关思考方向</p>
                </div>
            </div>
            
            <div class="feature">
                <span class="feature-icon">🔄</span>
                <div class="feature-text">
                    <h3>复盘回顾</h3>
                    <p>周期性自动生成思考总结和洞察</p>
                </div>
            </div>
            
            <div class="feature">
                <span class="feature-icon">📈</span>
                <div class="feature-text">
                    <h3>认知提升</h3>
                    <p>识别认知模式，提供成长建议</p>
                </div>
            </div>
            
            <a href="/docs" class="btn">打开API文档</a>
            <a href="/docs" class="api-link">查看Swagger API文档 →</a>
        </div>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("spirit.main:app", host="0.0.0.0", port=8000, reload=True)
