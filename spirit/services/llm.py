from typing import Optional
from openai import AsyncOpenAI

from spirit.core.config import settings


class LLMService:
    """LLM服务，用于生成思考扩展内容"""
    
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def generate(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """生成文本"""
        
        if not self.client:
            return None
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个个人成长助手，帮助用户展开思考。你应该提供有深度、有洞察力的建议。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"LLM生成失败: {e}")
            return None
    
    async def chat(self, messages: list, max_tokens: int = 2000) -> Optional[str]:
        """对话"""
        
        if not self.client:
            return None
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"LLM对话失败: {e}")
            return None
    
    async def analyze_sentiment(self, text: str) -> Optional[dict]:
        """情感分析"""
        
        prompt = f"""分析以下文本的情感：

{text}

请返回JSON格式，包含：
- sentiment: positive/negative/neutral
- intensity: 1-10
- emotions: 情绪列表"""

        try:
            result = await self.generate(prompt, max_tokens=500)
            if result:
                import json
                return json.loads(result)
        except Exception as e:
            print(f"情感分析失败: {e}")
        
        return None
    
    async def summarize(self, text: str, max_length: int = 200) -> Optional[str]:
        """文本摘要"""
        
        prompt = f"""请用{max_length}字以内的中文概括以下内容：

{text}

摘要："""
        
        result = await self.generate(prompt, max_tokens=max_length)
        return result
    
    async def expand_idea(self, idea: str) -> Optional[str]:
        """扩展想法"""
        
        prompt = f"""基于以下想法，提供更深入的思考和扩展：

{idea}

请从以下几个角度展开：
1. 这个想法的根源是什么？
2. 它可以引出哪些相关问题？
3. 有什么实际的行动建议？
"""
        
        return await self.generate(prompt, max_tokens=1500)
    
    async def suggest_reflection(self, event: str) -> Optional[str]:
        """反思建议"""
        
        prompt = f"""针对以下事件/经历，提供反思问题：

{event}

请提出3-5个帮助深入反思的问题："""
        
        return await self.generate(prompt, max_tokens=800)
