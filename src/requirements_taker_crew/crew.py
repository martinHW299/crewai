"""
CrewAI Requirements Analysis Crew
Comprehensive requirements gathering and analysis system.
"""

import os
from pathlib import Path
from typing import List
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from .tools.google_drive_tool import GoogleDriveTool


@CrewBase
class RequirementsTakerCrew():
    """
    Comprehensive Requirements Analysis Crew
    
    This crew systematically processes project documents and answers requirements
    questionnaire questions to generate thorough project analysis reports.
    """

    def __init__(self):
        """Initialize the crew with proper configuration paths."""
        # Initialize agents and tasks lists
        self.agents: List[BaseAgent] = []
        self.tasks: List[Task] = []

    @agent
    def document_analyzer(self) -> Agent:
        """
        Document Analysis Agent
        Processes all files in Google Drive folder for comprehensive content extraction.
        """
        return Agent(
            config=self.agents_config['document_analyzer'],
            tools=[GoogleDriveTool()],
            verbose=True,
            allow_delegation=False,
            max_iter=3,  # Allow multiple iterations for complex analysis
            max_execution_time=1800  # 30 minutes timeout for large folders
        )

    @agent
    def requirements_synthesizer(self) -> Agent:
        """
        Requirements Synthesis Agent
        Analyzes extracted documents against questionnaire framework.
        """
        return Agent(
            config=self.agents_config['requirements_synthesizer'],
            verbose=True,
            allow_delegation=False,
            max_iter=2,  # Allow refinement of analysis
            max_execution_time=900  # 15 minutes timeout
        )

    @agent
    def quality_assurance_reviewer(self) -> Agent:
        """
        Quality Assurance Agent
        Reviews and validates the final requirements analysis report.
        """
        return Agent(
            role="Quality Assurance and Completeness Reviewer",
            goal=(
                "Review the requirements analysis report for completeness, accuracy, and "
                "actionability. Ensure all important aspects are covered and the report "
                "provides clear next steps for stakeholders."
            ),
            backstory=(
                "You're a senior quality assurance specialist with extensive experience "
                "in requirements engineering and project management. You excel at "
                "identifying gaps, inconsistencies, and areas for improvement in "
                "requirements documentation. Your reviews ensure that stakeholders "
                "receive comprehensive, actionable, and professional analysis reports."
            ),
            verbose=True,
            allow_delegation=False,
            max_iter=1
        )

    @task
    def document_analysis_task(self) -> Task:
        """
        Comprehensive Document Analysis Task
        Processes all files in the specified Google Drive folder.
        """
        return Task(
            config=self.tasks_config['document_analysis_task'],
            agent=self.document_analyzer(),
            expected_output=(
                "Comprehensive extraction of ALL project information from Google Drive "
                "documents, organized by the 15 requirements categories with detailed "
                "source attribution and gap identification."
            )
        )

    @task
    def requirements_synthesis_task(self) -> Task:
        """
        Requirements Analysis and Synthesis Task
        Analyzes documents against comprehensive questionnaire framework.
        """
        return Task(
            config=self.tasks_config['requirements_synthesis_task'],
            agent=self.requirements_synthesizer(),
            context=[self.document_analysis_task()],
            expected_output=(
                "A comprehensive requirements analysis report that systematically "
                "addresses each category of the requirements questionnaire, identifies "
                "gaps, and provides actionable recommendations for stakeholders."
            ),
            output_file='comprehensive_requirements_analysis.md'
        )

    @task
    def quality_review_task(self) -> Task:
        """
        Quality Assurance Review Task
        Reviews and enhances the final requirements analysis report.
        """
        return Task(
            description=(
                "Review the comprehensive requirements analysis report for completeness, "
                "accuracy, and professional quality. Ensure that:\n"
                "1. All 15 requirements categories are adequately addressed\n"
                "2. Gaps and missing information are clearly identified\n"
                "3. Recommendations are specific and actionable\n"
                "4. The report follows professional standards\n"
                "5. Executive summary provides clear key takeaways\n"
                "6. Next steps are prioritized and realistic\n"
                "\n"
                "If any issues are found, provide specific suggestions for improvement. "
                "Generate a final polished version of the report that stakeholders can "
                "immediately use for project planning and decision-making."
            ),
            agent=self.quality_assurance_reviewer(),
            context=[self.document_analysis_task(), self.requirements_synthesis_task()],
            expected_output=(
                "A polished, professional requirements analysis report that has been "
                "reviewed for completeness and quality. The report should be ready for "
                "immediate stakeholder review and project planning use."
            ),
            output_file='final_requirements_analysis_report.md'
        )

    @crew
    def crew(self) -> Crew:
        """
        Create the Requirements Analysis Crew
        
        Returns a configured crew with all agents and tasks for comprehensive
        requirements analysis.
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=bool(os.getenv('CREW_VERBOSE', 'true').lower() == 'true'),
            memory=bool(os.getenv('CREW_MEMORY', 'false').lower() == 'true'),
            planning=True,  # Enable planning for better task coordination
            planning_llm=None,  # Use default LLM for planning
            max_rpm=10,  # Rate limiting
            share_crew=False,  # Keep analysis private
            step_callback=self._log_step,  # Add step logging
            task_callback=self._log_task_completion
        )

    def _log_step(self, step):
        """Log crew execution steps with proper error handling."""
        try:
            # Handle different types of step objects
            if hasattr(step, 'get') and callable(getattr(step, 'get')):
                # Dictionary-like object
                step_info = step.get('step', 'Unknown Step')
                print(f"🔄 Crew Step: {step_info}")
            elif hasattr(step, 'result'):
                # ToolResult object
                print(f"🔧 Tool executed: {getattr(step, 'tool_name', 'Unknown Tool')}")
            elif hasattr(step, '__dict__'):
                # Object with attributes
                step_type = type(step).__name__
                print(f"🔄 Processing: {step_type}")
            else:
                # Fallback for other types
                print(f"🔄 Crew Step: {str(step)[:100]}...")
        except Exception as e:
            # Fallback logging to prevent callback errors from breaking execution
            print(f"🔄 Crew Step in progress... (callback error: {str(e)[:50]})")

    def _log_task_completion(self, task_output):
        """Log task completion with proper error handling."""
        try:
            if hasattr(task_output, 'task') and hasattr(task_output.task, 'description'):
                task_name = task_output.task.description.split('\n')[0][:100]
                print(f"✅ Task Completed: {task_name}")
            elif hasattr(task_output, 'description'):
                task_name = task_output.description.split('\n')[0][:100]
                print(f"✅ Task Completed: {task_name}")
            elif hasattr(task_output, 'raw'):
                output_preview = str(task_output.raw)[:100]
                print(f"✅ Task Completed: {output_preview}...")
            else:
                print(f"✅ Task Completed: {type(task_output).__name__}")
        except Exception as e:
            # Fallback logging to prevent callback errors from breaking execution
            print(f"✅ Task Completed (callback error: {str(e)[:50]})")