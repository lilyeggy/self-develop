import json
from typing import List
from datetime import datetime
from spirit.db.models import Thought, ReviewSummary


class ExportService:
    """导出服务"""
    
    async def export_to_markdown(
        self, 
        thoughts: List[Thought],
        include_expansions: bool = True
    ) -> str:
        """导出为Markdown格式"""
        
        md_lines = []
        md_lines.append("# 我的思考记录")
        md_lines.append("")
        md_lines.append(f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md_lines.append(f"共 {len(thoughts)} 条记录")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")
        
        category_names = {
            "idea": "💡 想法",
            "question": "❓ 问题",
            "insight": "✨ 感悟",
            "plan": "📋 计划",
            "reflection": "🔄 反思",
            "note": "📝 笔记",
            "diary": "📅 日记"
        }
        
        current_date = None
        
        for thought in sorted(thoughts, key=lambda t: t.created_at, reverse=True):
            thought_date = thought.created_at.strftime("%Y-%m-%d")
            
            if thought_date != current_date:
                current_date = thought_date
                md_lines.append(f"\n## {thought_date}")
                md_lines.append("")
            
            category_icon = category_names.get(thought.category.value, "📝")
            
            if thought.title:
                md_lines.append(f"### {category_icon} {thought.title}")
            else:
                md_lines.append(f"### {category_icon} {thought.created_at.strftime('%H:%M')}")
            
            md_lines.append("")
            md_lines.append(thought.content)
            
            if thought.tags:
                tags_str = " ".join([f"`#{tag}`" for tag in thought.tags])
                md_lines.append("")
                md_lines.append(f"_{tags_str}_")
            
            if include_expansions and thought.expansions:
                md_lines.append("")
                md_lines.append("**展开思考：**")
                for expansion in thought.expansions:
                    md_lines.append(f"- {expansion.content}")
            
            md_lines.append("")
            md_lines.append(f"_{thought.created_at.strftime('%H:%M:%S')}_")
            md_lines.append("")
            md_lines.append("---")
            md_lines.append("")
        
        return "\n".join(md_lines)
    
    async def export_to_json(
        self, 
        thoughts: List[Thought],
        include_expansions: bool = True
    ) -> str:
        """导出为JSON格式"""
        
        data = {
            "export_time": datetime.now().isoformat(),
            "total_count": len(thoughts),
            "thoughts": []
        }
        
        for thought in thoughts:
            thought_data = {
                "id": thought.id,
                "content": thought.content,
                "title": thought.title,
                "category": thought.category.value,
                "tags": thought.tags,
                "source": thought.source.value,
                "is_favorite": thought.is_favorite,
                "created_at": thought.created_at.isoformat(),
                "updated_at": thought.updated_at.isoformat()
            }
            
            if include_expansions and thought.expansions:
                thought_data["expansions"] = [
                    {
                        "type": exp.expansion_type,
                        "content": exp.content,
                        "created_at": exp.created_at.isoformat()
                    }
                    for exp in thought.expansions
                ]
            
            data["thoughts"].append(thought_data)
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    async def export_to_pdf(
        self, 
        thoughts: List[Thought],
        include_expansions: bool = True
    ) -> bytes:
        """导出为PDF格式"""
        
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.enums import TA_LEFT
            from io import BytesIO
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
            
            styles = getSampleStyleSheet()
            story = []
            
            title = Paragraph("我的思考记录", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 0.2 * inch))
            
            for thought in sorted(thoughts, key=lambda t: t.created_at, reverse=True)[:50]:
                heading = Paragraph(f"{thought.created_at.strftime('%Y-%m-%d %H:%M')} - {thought.category.value}", styles['Heading2'])
                story.append(heading)
                story.append(Spacer(1, 0.1 * inch))
                
                content = Paragraph(thought.content[:500], styles['BodyText'])
                story.append(content)
                story.append(Spacer(1, 0.2 * inch))
            
            doc.build(story)
            return buffer.getvalue()
        
        except ImportError:
            markdown_content = await self.export_to_markdown(thoughts, include_expansions)
            return markdown_content.encode('utf-8')
    
    def export_summaries_to_markdown(self, summaries: List[ReviewSummary]) -> str:
        """导出演总结为Markdown"""
        
        md_lines = []
        md_lines.append("# 回顾总结")
        md_lines.append("")
        md_lines.append(f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md_lines.append("")
        
        for summary in sorted(summaries, key=lambda s: s.period_end, reverse=True):
            md_lines.append(f"## {summary.period.value.upper()} - {summary.period_end.strftime('%Y-%m-%d')}")
            md_lines.append("")
            md_lines.append(f"**时间段**: {summary.period_start.strftime('%Y-%m-%d')} ~ {summary.period_end.strftime('%Y-%m-%d')}")
            md_lines.append("")
            md_lines.append("### 总结")
            md_lines.append(summary.summary)
            md_lines.append("")
            
            if summary.highlights:
                md_lines.append("### 亮点")
                for h in summary.highlights:
                    md_lines.append(f"- {h}")
                md_lines.append("")
            
            if summary.insights:
                md_lines.append("### 洞察")
                for insight in summary.insights:
                    md_lines.append(f"- {insight}")
                md_lines.append("")
            
            if summary.suggestions:
                md_lines.append("### 建议")
                for suggestion in summary.suggestions:
                    md_lines.append(f"- {suggestion}")
                md_lines.append("")
            
            md_lines.append("---")
            md_lines.append("")
        
        return "\n".join(md_lines)
    
    def export_summaries_to_json(self, summaries: List[ReviewSummary]) -> str:
        """导出演总结为JSON"""
        
        data = {
            "export_time": datetime.now().isoformat(),
            "total_count": len(summaries),
            "summaries": []
        }
        
        for summary in summaries:
            data["summaries"].append({
                "period": summary.period.value,
                "period_start": summary.period_start.isoformat(),
                "period_end": summary.period_end.isoformat(),
                "summary": summary.summary,
                "highlights": summary.highlights,
                "insights": summary.insights,
                "suggestions": summary.suggestions,
                "created_at": summary.created_at.isoformat()
            })
        
        return json.dumps(data, ensure_ascii=False, indent=2)
