import re
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from spirit.db.models import Thought, ThoughtExpansion, UserCategory, ThoughtCategory
from spirit.utils import parse_thought_category, extract_tags


class InputHandlerAgent:
    """
    输入处理Agent：负责接收、解析和初步处理用户输入
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def process_thought(self, thought: Thought) -> Thought:
        """处理用户输入的思考内容"""
        
        content = thought.content
        
        thought.title = self._extract_title(content)
        
        if not thought.category:
            thought.category = ThoughtCategory(parse_thought_category(content))
        
        if not thought.tags:
            thought.tags = extract_tags(content)
        
        thought.metadata = thought.metadata or {}
        thought.metadata["word_count"] = len(content)
        thought.metadata["char_count"] = len(content.replace(" ", ""))
        
        return thought
    
    def _extract_title(self, content: str) -> Optional[str]:
        """从内容中提取标题"""
        lines = content.strip().split("\n")
        first_line = lines[0].strip()
        
        if len(first_line) <= 100 and not first_line.endswith((":", "，", "，")):
            return first_line
        
        return None
    
    async def parse_notion_content(self, content: dict) -> dict:
        """解析来自Notion的内容"""
        parsed = {
            "content": "",
            "title": None,
            "tags": [],
            "created_time": None
        }
        
        if "properties" in content:
            props = content["properties"]
            
            if "Name" in props and props["Name"]["title"]:
                parsed["title"] = props["Name"]["title"][0]["plain_text"]
                parsed["content"] = parsed["title"] + "\n\n"
            
            if "Tags" in props and props["Tags"]["multi_select"]:
                parsed["tags"] = [tag["name"] for tag in props["Tags"]["multi_select"]]
        
        if "children" in content:
            for child in content["children"]:
                if child.get("type") == "paragraph":
                    text = child["paragraph"]["rich_text"]
                    if text:
                        parsed["content"] += text[0]["plain_text"] + "\n"
        
        return parsed
    
    async def parse_obsidian_content(self, content: str, metadata: dict) -> dict:
        """解析来自Obsidian的内容"""
        parsed = {
            "content": content,
            "title": None,
            "tags": []
        }
        
        frontmatter_pattern = r"^---\n(.*?)\n---\n"
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if match:
            frontmatter = match.group(1)
            parsed["content"] = content[match.end():]
            
            for line in frontmatter.split("\n"):
                if line.startswith("title:"):
                    parsed["title"] = line.split(":", 1)[1].strip().strip('"')
                elif line.startswith("tags:"):
                    tags_str = line.split(":", 1)[1].strip()
                    parsed["tags"] = re.findall(r"\[?([^\]\s,]+)\]?", tags_str)
        
        if not parsed["title"]:
            lines = content.split("\n")
            for line in lines:
                if line.strip().startswith("# "):
                    parsed["title"] = line.strip().replace("# ", "")
                    break
        
        return parsed
    
    async def parse_evernote_content(self, content: dict) -> dict:
        """解析来自印象笔记的内容"""
        parsed = {
            "content": content.get("content", ""),
            "title": content.get("title"),
            "tags": content.get("tags", []),
            "created_time": content.get("created")
        }
        
        return parsed
    
    def normalize_content(self, content: str) -> str:
        """标准化内容格式"""
        content = content.strip()
        content = re.sub(r"\r\n", "\n", content)
        content = re.sub(r"\r", "\n", content)
        content = re.sub(r"\n{3,}", "\n\n", content)
        
        return content
    
    def detect_language(self, content: str) -> str:
        """检测内容语言"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        total_chars = len(content.replace(" ", ""))
        
        if total_chars == 0:
            return "en"
        
        if chinese_chars / total_chars > 0.3:
            return "zh"
        
        return "en"
