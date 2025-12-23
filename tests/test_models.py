"""
Database Models Unit Tests
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.user import User, UserRole
from app.models.project import Project, Session, Version, ProjectStatus
from app.models.crawler import CrawlJob, RawData, Comment, CrawlStatus
from app.models.analysis import TrendAnalysis, AnalysisStatus, AnalysisModel
from app.models.generation import GenerationJob, ImageAsset, GenerationStatus
from app.models.design import DesignConcept, PromptSpec
from app.models.report import Report, ReportFormat
from app.models.size import SizeStandard, SizeTable, Gender


@pytest.fixture
def db_session():
    """Create test database session"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


class TestUserModel:
    """User model tests"""

    def test_user_creation(self, db_session):
        """Test user creation"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.DESIGNER,
            language="ko",
            size_standard="KS"
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.DESIGNER
        assert user.created_at is not None

    def test_user_relationships(self, db_session):
        """Test user relationships"""
        user = User(
            username="designer1",
            email="designer@example.com",
            password_hash="hashed_password",
            role=UserRole.DESIGNER
        )
        db_session.add(user)
        db_session.commit()

        # Create project
        project = Project(
            title="Test Project",
            description="Test Description",
            prompt="Test prompt",
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()

        # Check relationship
        assert len(user.projects) == 1
        assert user.projects[0].title == "Test Project"


class TestProjectModel:
    """Project model tests"""

    def test_project_creation(self, db_session):
        """Test project creation"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.DESIGNER
        )
        db_session.add(user)
        db_session.commit()

        project = Project(
            title="Fashion Collection 2024",
            description="Spring/Summer collection",
            prompt="SS 2024 fashion prompt",
            owner_id=user.id,
            status=ProjectStatus.ACTIVE
        )
        db_session.add(project)
        db_session.commit()

        assert project.id is not None
        assert project.title == "Fashion Collection 2024"
        assert project.status == ProjectStatus.ACTIVE
        assert project.progress_percent == 0

    def test_project_sessions(self, db_session):
        """Test project sessions"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.DESIGNER
        )
        db_session.add(user)
        db_session.commit()

        project = Project(
            title="Test Project",
            prompt="Test prompt",
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()

        session = Session(
            name="Initial Design",
            description="First design session",
            project_id=project.id
        )
        db_session.add(session)
        db_session.commit()

        assert session.id is not None
        assert session.project_id == project.id
        assert len(project.sessions) == 1


class TestCrawlerModel:
    """Crawler model tests"""

    def test_crawl_job_creation(self, db_session):
        """Test crawl job creation"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.ANALYST
        )
        db_session.add(user)
        db_session.commit()

        project = Project(
            title="Crawler Project",
            prompt="Crawler prompt",
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()

        job = CrawlJob(
            project_id=project.id,
            job_name="Fashion News Crawl",
            crawler_type="fashion_news",
            keywords='["trend", "fashion"]',
            status=CrawlStatus.PENDING,
            max_pages=10
        )
        db_session.add(job)
        db_session.commit()

        assert job.id is not None
        assert job.crawler_type == "fashion_news"
        assert job.status == CrawlStatus.PENDING
        assert job.progress_percent == 0.0

    def test_raw_data_creation(self, db_session):
        """Test raw data creation"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.ANALYST
        )
        db_session.add(user)
        db_session.commit()

        project = Project(
            title="Raw Data Project",
            prompt="Raw data prompt",
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()

        job = CrawlJob(
            project_id=project.id,
            job_name="Fashion News Crawl",
            crawler_type="fashion_news",
            status=CrawlStatus.RUNNING
        )
        db_session.add(job)
        db_session.commit()

        raw_data = RawData(
            crawl_job_id=job.id,
            source="fashion_news",
            url="https://example.com/article",
            title="2024 Fashion Trends",
            content="Fashion trends for 2024 include...",
            quality_score=0.8,
            relevance_score=0.9
        )
        db_session.add(raw_data)
        db_session.commit()

        assert raw_data.id is not None
        assert raw_data.crawl_job_id == job.id
        assert raw_data.quality_score == 0.8

    def test_crawl_job_with_raw_data(self, db_session):
        """Test crawl job with raw data relationship"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.ANALYST
        )
        db_session.add(user)
        db_session.commit()

        project = Project(
            title="Instagram Crawl",
            prompt="Instagram crawl prompt",
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()

        job = CrawlJob(
            project_id=project.id,
            job_name="Instagram Crawl",
            crawler_type="fashion_insta",
            keywords='["fashion"]'
        )
        db_session.add(job)
        db_session.commit()

        # Add multiple raw data items
        for i in range(5):
            raw_data = RawData(
                crawl_job_id=job.id,
                source="fashion_insta",
                url=f"https://instagram.com/p/test{i}",
                title=f"Fashion Post {i}",
                content=f"Content {i}"
            )
            db_session.add(raw_data)

        db_session.commit()

        assert len(job.raw_data_items) == 5


class TestAnalysisModel:
    """Analysis model tests"""

    def test_trend_analysis_creation(self, db_session):
        """Test trend analysis creation"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.ANALYST
        )
        db_session.add(user)
        db_session.commit()

        project = Project(
            title="Analysis Project",
            prompt="Analysis prompt",
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()

        analysis = TrendAnalysis(
            project_id=project.id,
            analysis_name="Sustainable Fashion Analysis",
            status=AnalysisStatus.COMPLETED,
            model_used=AnalysisModel.GEMINI_2_5_FLASH,
            keywords='["sustainable", "fashion"]',
            summary="Sustainable materials are trending",
            confidence_score=0.85
        )
        db_session.add(analysis)
        db_session.commit()

        assert analysis.id is not None
        assert analysis.status == AnalysisStatus.COMPLETED
        assert analysis.model_used == AnalysisModel.GEMINI_2_5_FLASH


class TestGenerationModel:
    """Generation model tests"""

    def test_generation_job_creation(self, db_session):
        """Test generation job creation"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.DESIGNER
        )
        db_session.add(user)
        db_session.commit()

        project = Project(
            title="Generation Project",
            prompt="Generation prompt",
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()

        job = GenerationJob(
            project_id=project.id,
            job_name="Generate Summer Dress",
            model_used="zimage",
            generation_type="garment",
            parameters='{"style": "modern", "color": "blue"}',
            status=GenerationStatus.COMPLETED
        )
        db_session.add(job)
        db_session.commit()

        assert job.id is not None
        assert job.model_used == "zimage"
        assert job.status == GenerationStatus.COMPLETED

    def test_image_asset_creation(self, db_session):
        """Test image asset creation"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.DESIGNER
        )
        db_session.add(user)
        db_session.commit()

        project = Project(
            title="Image Asset Project",
            prompt="Image asset prompt",
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()

        job = GenerationJob(
            project_id=project.id,
            job_name="Test Generation Job",
            model_used="zimage",
            generation_type="garment",
            status=GenerationStatus.COMPLETED
        )
        db_session.add(job)
        db_session.commit()

        image = ImageAsset(
            generation_job_id=job.id,
            file_name="test.png",
            file_path="/images/generated/test.png",
            image_type="garment_front",
            width=1024,
            height=1024,
            file_size_bytes=1024000,
            format="PNG"
        )
        db_session.add(image)
        db_session.commit()

        assert image.id is not None
        assert image.generation_job_id == job.id
        assert image.width == 1024
        assert image.height == 1024


class TestDesignModel:
    """Design model tests"""

    def test_design_concept_creation(self, db_session):
        """Test design concept creation"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.DESIGNER
        )
        db_session.add(user)
        db_session.commit()

        project = Project(
            title="Design Concept Project",
            prompt="Design concept prompt",
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()

        concept = DesignConcept(
            project_id=project.id,
            concept_name="Minimalist Office Wear",
            concept_number=1,
            details="Clean and professional designs",
            materials='["cotton", "linen"]'
        )
        db_session.add(concept)
        db_session.commit()

        assert concept.id is not None
        assert concept.concept_name == "Minimalist Office Wear"
        assert concept.concept_number == 1

    def test_prompt_spec_creation(self, db_session):
        """Test prompt spec creation"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.DESIGNER
        )
        db_session.add(user)
        db_session.commit()

        project = Project(
            title="Prompt Spec Project",
            prompt="Prompt spec prompt",
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()

        concept = DesignConcept(
            project_id=project.id,
            concept_name="Prompt Concept",
            concept_number=1
        )
        db_session.add(concept)
        db_session.commit()

        spec = PromptSpec(
            concept_id=concept.id,
            prompt_type="garment",
            model_name="zimage",
            base_prompt="Generate a {style} {garment_type} with {color_scheme}"
        )
        db_session.add(spec)
        db_session.commit()

        assert spec.id is not None
        assert spec.model_name == "zimage"


class TestSizeStandardModel:
    """Size standard model tests"""

    def test_size_standard_creation(self, db_session):
        """Test size standard creation"""
        standard = SizeStandard(
            standard_name="KS",
            standard_title="Korean Standard",
            country="KR",
            description="Korean sizing standard"
        )
        db_session.add(standard)
        db_session.commit()

        assert standard.id is not None
        assert standard.standard_name == "KS"
        assert standard.country == "KR"


class TestReportModel:
    """Report model tests"""

    def test_report_creation(self, db_session):
        """Test report creation"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.ANALYST
        )
        db_session.add(user)
        db_session.commit()

        project = Project(
            title="Report Project",
            prompt="Report prompt",
            owner_id=user.id
        )
        db_session.add(project)
        db_session.commit()

        report = Report(
            project_id=project.id,
            report_name="Fashion Trend Analysis Report",
            report_type="trend_analysis",
            language="ko",
            format=ReportFormat.PDF
        )
        db_session.add(report)
        db_session.commit()

        assert report.id is not None
        assert report.report_type == "trend_analysis"
        assert report.language == "ko"
        assert report.format == ReportFormat.PDF
