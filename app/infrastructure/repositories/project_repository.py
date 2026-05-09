"""
Repository for DesignProject.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.project import DesignProject


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        workspace_id: uuid.UUID,
        name: str,
        domain: str | None = None,
        purpose: str | None = None,
    ) -> DesignProject:
        project = DesignProject(
            workspace_id=workspace_id,
            name=name,
            domain=domain,
            purpose=purpose,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_by_id(self, project_id: uuid.UUID) -> DesignProject | None:
        return self.db.get(DesignProject, project_id)

    def list_all(self, workspace_id: uuid.UUID) -> list[DesignProject]:
        return (
            self.db.query(DesignProject)
            .filter_by(workspace_id=workspace_id)
            .order_by(DesignProject.created_at.desc())
            .all()
        )
