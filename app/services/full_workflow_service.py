"""
Full Workflow Service for Fashion AI Generation System
전체 워크플로우를 관리하는 서비스
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from app.core.logging import get_logger
from app.services.consistency_pipeline import ConsistencyPipeline
from app.services.analysis_service import AnalysisService
from crawlers.crawler_service import CrawlerService
from app.models.project import Project, Session
from app.models.crawler import CrawlJob
from app.models.analysis import TrendAnalysis
from app.models.design import DesignConcept

logger = get_logger(__name__)


class WorkflowStatus(Enum):
    """워크플로우 상태"""
    INITIATED = "initiated"
    CRAWLING = "crawling"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """워크플로우 단계"""
    step: str
    status: WorkflowStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    progress: float = 0.0
    error: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


class WorkflowSession:
    """워크플로우 세션"""
    def __init__(self, session_id: str, project_id: str):
        self.session_id = session_id
        self.project_id = project_id
        self.status = WorkflowStatus.INITIATED
        self.steps = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.metadata = {}

    def update_step(self, step: str, status: WorkflowStatus, data: Dict = None):
        """단계 업데이트"""
        self.steps[step] = WorkflowStep(
            step=step,
            status=status,
            start_time=datetime.now() if status == WorkflowStatus.CRAWLING else self.steps.get(step).start_time,
            end_time=datetime.now() if status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED] else None,
            progress=100.0 if status == WorkflowStatus.COMPLETED else 0.0,
            error=None if status != WorkflowStatus.FAILED else data.get('error') if data else None,
            data=data or {}
        )
        self.updated_at = datetime.now()

        # 전체 상태 업데이트
        self.status = self._calculate_overall_status()

    def _calculate_overall_status(self) -> WorkflowStatus:
        """전체 상태 계산"""
        if not self.steps:
            return WorkflowStatus.INITIATED

        statuses = [step.status for step in self.steps.values()]

        if all(s == WorkflowStatus.COMPLETED for s in statuses):
            return WorkflowStatus.COMPLETED
        elif any(s == WorkflowStatus.FAILED for s in statuses):
            return WorkflowStatus.FAILED
        elif any(s in [WorkflowStatus.CRAWLING, WorkflowStatus.ANALYZING, WorkflowStatus.GENERATING] for s in statuses):
            return WorkflowStatus.INITIATED
        else:
            return WorkflowStatus.INITIATED

    def get_progress(self) -> float:
        """전체 진행률 계산"""
        if not self.steps:
            return 0.0
        return sum(step.progress for step in self.steps.values()) / len(self.steps)


class FullWorkflowService:
    """전체 워크플로우 서비스"""

    def __init__(self):
        self.crawler_service = CrawlerService()
        self.analysis_service = AnalysisService()
        self.consistency_pipeline = ConsistencyPipeline()
        self.sessions: Dict[str, WorkflowSession] = {}
        self.logger = get_logger(__name__)

    # @MX:ANCHOR: [AUTO] Workflow session creation - core workflow entry point
    # @MX:REASON: Called from 5+ locations as the primary workflow initialization interface
    async def create_session(self, project_id: str, user_input: Dict[str, Any]) -> str:
        """새 워크플로우 세션 생성"""
        import uuid
        session_id = f"session_{uuid.uuid4().hex[:12]}"

        session = WorkflowSession(session_id, project_id)
        session.metadata.update(user_input)
        self.sessions[session_id] = session

        self.logger.info(f"Created workflow session: {session_id} for project: {project_id}")
        return session_id

    async def start_workflow(self, session_id: str) -> Dict[str, Any]:
        """워크플로우 시작"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        try:
            # Step 1: 크롤링
            await self._execute_crawling_phase(session)

            # Step 2: 분석
            await self._execute_analysis_phase(session)

            # Step 3: 디자인 생성
            await self._execute_generation_phase(session)

            return {
                'session_id': session_id,
                'status': session.status.value,
                'progress': session.get_progress(),
                'message': 'Workflow completed successfully'
            }

        except Exception as e:
            session.status = WorkflowStatus.FAILED
            self.logger.error(f"Workflow failed: {str(e)}")
            return {
                'session_id': session_id,
                'status': session.status.value,
                'error': str(e)
            }

    async def _execute_crawling_phase(self, session: WorkflowSession) -> None:
        """크롤링 단계 실행"""
        session.update_step('crawling', WorkflowStatus.CRAWLING, {'message': 'Starting data collection'})

        try:
            # 사용자 입력 분석으로 크롤링 대상 결정
            user_input = session.metadata
            keywords = self._extract_keywords(user_input)

            # 크롤링 작업 생성 - 실제 구현된 크롤러 사용
            crawl_job_id = await self.crawler_service.start_crawl(
                keywords=keywords,
                sources=['fashion_news', 'fashion_insta', 'musinsa', 'wgsn', 'pinterest'],
                max_pages=100
            )

            # 크롤링 진행 상태 모니터링
            last_progress = 0
            while True:
                status = await self.crawler_service.get_crawl_status(crawl_job_id)

                progress = status.get('progress', 0)
                if progress != last_progress:
                    session.update_step('crawling', WorkflowStatus.CRAWLING,
                                     {'progress': progress, 'job_id': crawl_job_id})
                    last_progress = progress

                if status.get('status') == 'completed':
                    raw_data = await self.crawler_service.get_crawl_results(crawl_job_id)
                    session.metadata['crawled_data'] = raw_data
                    session.update_step('crawling', WorkflowStatus.COMPLETED,
                                     {'items_collected': len(raw_data)})
                    break
                elif status.get('status') == 'failed':
                    raise Exception(f"Crawling failed: {status.get('error')}")

                await asyncio.sleep(5)  # 5초 간격으로 상태 확인

        except Exception as e:
            session.update_step('crawling', WorkflowStatus.FAILED, {'error': str(e)})
            raise

    async def _execute_analysis_phase(self, session: WorkflowSession) -> None:
        """분석 단계 실행"""
        session.update_step('analysis', WorkflowStatus.ANALYZING, {'message': 'Analyzing trends'})

        try:
            # 크롤링된 데이터 분석
            raw_data = session.metadata.get('crawled_data', [])

            # 3-Phase 분석 실행
            analysis_result = await self.analysis_service.analyze_trends(
                raw_data=raw_data,
                filters=session.metadata.get('filters', {}),
                user_input=session.metadata.get('prompt', '')
            )

            # 디자인 컨셉 생성
            design_concepts = await self.analysis_service.generate_design_concepts(
                analysis_result=analysis_result
            )

            # 결과 저장
            session.metadata['analysis_result'] = analysis_result
            session.metadata['design_concepts'] = design_concepts
            session.update_step('analysis', WorkflowStatus.COMPLETED,
                             {'concepts_generated': len(design_concepts)})

        except Exception as e:
            session.update_step('analysis', WorkflowStatus.FAILED, {'error': str(e)})
            raise

    async def _execute_generation_phase(self, session: WorkflowSession) -> None:
        """생성 단계 실행"""
        session.update_step('generation', WorkflowStatus.GENERATING, {'message': 'Generating designs'})

        try:
            design_concepts = session.metadata.get('design_concepts', [])
            generated_designs = []

            for i, concept in enumerate(design_concepts):
                try:
                    # 각 컨셉별 디자인 시리즈 생성
                    result = await self.consistency_pipeline.generate_design_series(concept)

                    generated_designs.append({
                        'concept_index': i,
                        'concept': concept,
                        'result': result
                    })

                    # 진행률 업데이트
                    progress = ((i + 1) / len(design_concepts)) * 100
                    session.update_step('generation', WorkflowStatus.GENERATING,
                                     {'progress': progress, 'current_concept': i + 1})

                    self.logger.info(f"Generated design series for concept {i + 1}/{len(design_concepts)}")

                except Exception as e:
                    self.logger.warning(f"Failed to generate design for concept {i}: {str(e)}")
                    # 개별 실패는 전체 실패가 아님
                    continue

            # 결과 저장
            session.metadata['generated_designs'] = generated_designs
            session.update_step('generation', WorkflowStatus.COMPLETED,
                             {'designs_generated': len(generated_designs)})

        except Exception as e:
            session.update_step('generation', WorkflowStatus.FAILED, {'error': str(e)})
            raise

    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """세션 상태 조회"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        return {
            'session_id': session_id,
            'project_id': session.project_id,
            'status': session.status.value,
            'progress': session.get_progress(),
            'steps': {
                step: {
                    'status': step.status.value,
                    'progress': step.progress,
                    'error': step.error,
                    'data': step.data
                }
                for step in session.steps.values()
            },
            'created_at': session.created_at,
            'updated_at': session.updated_at
        }

    async def cancel_session(self, session_id: str) -> Dict[str, Any]:
        """세션 취소"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        session.status = WorkflowStatus.CANCELLED

        # 진행 중인 크롤링 작업 취소
        # 실제 구현에서는 crawler_service.cancel_crawl() 호출

        return {
            'session_id': session_id,
            'status': session.status.value,
            'message': 'Session cancelled'
        }

    def _extract_keywords(self, user_input: Dict[str, Any]) -> List[str]:
        """사용자 입력에서 키워드 추출"""
        prompt = user_input.get('prompt', '')
        filters = user_input.get('filters', {})

        # 기본 키워드
        keywords = [prompt]

        # 필터에서 키워드 추가
        if filters.get('gender'):
            keywords.append(filters['gender'])
        if filters.get('season'):
            keywords.append(filters['season'])
        if filters.get('age_group'):
            keywords.append(filters['age_group'])
        if filters.get('region'):
            keywords.append(filters['region'])

        return keywords


# 전역 싱글톤 인스턴스
_workflow_service_instance: Optional[FullWorkflowService] = None


def get_workflow_service() -> FullWorkflowService:
    """워크플로우 서비스 싱글톤 인스턴스 반환"""
    global _workflow_service_instance
    if _workflow_service_instance is None:
        _workflow_service_instance = FullWorkflowService()
    return _workflow_service_instance