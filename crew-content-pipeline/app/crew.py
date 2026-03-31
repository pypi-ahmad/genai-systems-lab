"""Crew assembly and execution for the Content Creation Pipeline."""

from crewai import Crew, Process

from app.agents import build_editor, build_researcher, build_seo_expert, build_writer
from app.tasks import (
    build_editing_task,
    build_research_task,
    build_seo_task,
    build_writing_task,
)


def build_crew(topic: str) -> Crew:
    researcher = build_researcher()
    writer = build_writer()
    editor = build_editor()
    seo_expert = build_seo_expert()

    research_task = build_research_task(researcher, topic)
    writing_task = build_writing_task(writer, research_task)
    editing_task = build_editing_task(editor, writing_task)
    seo_task = build_seo_task(seo_expert, editing_task)

    return Crew(
        agents=[researcher, writer, editor, seo_expert],
        tasks=[research_task, writing_task, editing_task, seo_task],
        process=Process.sequential,
        verbose=True,
    )


def run_pipeline(topic: str) -> str:
    crew = build_crew(topic)
    result = crew.kickoff(inputs={"topic": topic})
    return str(result)
