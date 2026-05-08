"""Shared presentation layer utilities.

Provides common mixins and utilities for API serializers.
"""
from rest_framework import serializers


# @MX:ANCHOR: [AUTO] SessionMetaMixin provides SPEC-05-API-001 required meta fields for all session API responses
# @MX:REASON: Fan-in >= 3 (all session-related API endpoints use this mixin)
# @MX:SPEC: SPEC-05 REQ-05-API-001
class SessionMetaMixin:
    """Adds SPEC-05-API-001 required meta fields to API responses.

    This mixin provides the standard meta fields that must be included in all
    design session API responses per SPEC-05 REQ-05-API-001.

    Meta Fields:
        current_step (int): Current pipeline step (1-17)
        mode (str): Session execution mode ("guided" or "auto")
        evidence_refs (list): Citation IDs for supporting evidence
        is_hypothesis (bool): Whether current state is hypothetical
        decision_required (bool): Whether user decision is required
        next_actions (list): Available actions for next step

    Usage:
        class MySessionSerializer(SessionMetaMixin, serializers.Serializer):
            pass
    """

    # Meta fields per SPEC-05-API-001
    current_step = serializers.IntegerField(
        min_value=1,
        max_value=17,
        help_text="Current pipeline step (1-17)",
    )
    mode = serializers.ChoiceField(
        choices=["guided", "auto"],
        help_text="Session execution mode",
    )
    evidence_refs = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False,
        help_text="Citation IDs for supporting evidence",
    )
    is_hypothesis = serializers.BooleanField(
        help_text="Whether current state is hypothetical",
        required=False,
        default=False,
    )
    decision_required = serializers.BooleanField(
        help_text="Whether user decision is required",
        required=False,
        default=False,
    )
    next_actions = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        required=False,
        help_text="Available actions for next step",
    )

    def get_current_step(self, obj):
        """Extract current_step from session entity.

        Args:
            obj: DesignSession entity or dict

        Returns:
            Current step value (1-17)
        """
        if hasattr(obj, "current_step"):
            return obj.current_step.value
        if isinstance(obj, dict) and "current_step" in obj:
            step = obj["current_step"]
            return step.value if hasattr(step, "value") else step
        return 1

    def get_mode(self, obj):
        """Extract mode from session entity.

        Args:
            obj: DesignSession entity or dict

        Returns:
            Mode value ("guided" or "auto")
        """
        if hasattr(obj, "mode"):
            return obj.mode.value
        if isinstance(obj, dict) and "mode" in obj:
            mode = obj["mode"]
            return mode.value if hasattr(mode, "value") else mode
        return "guided"

    def get_evidence_refs(self, obj):
        """Extract evidence references from decision logs.

        Args:
            obj: DesignSession entity or dict

        Returns:
            List of citation IDs
        """
        if hasattr(obj, "evidence_refs"):
            return obj.evidence_refs
        if isinstance(obj, dict) and "evidence_refs" in obj:
            return obj["evidence_refs"]
        return []

    def get_is_hypothesis(self, obj):
        """Check if current state is hypothetical.

        Args:
            obj: DesignSession entity or dict

        Returns:
            True if state is hypothetical
        """
        if hasattr(obj, "is_hypothesis"):
            return obj.is_hypothesis
        if isinstance(obj, dict) and "is_hypothesis" in obj:
            return obj["is_hypothesis"]
        # Default: hypothesis if in early stages (steps 1-4)
        current_step = self.get_current_step(obj)
        return current_step <= 4

    def get_decision_required(self, obj):
        """Check if user decision is required at current step.

        Args:
            obj: DesignSession entity or dict

        Returns:
            True if decision required
        """
        if hasattr(obj, "decision_required"):
            return obj.decision_required
        if isinstance(obj, dict) and "decision_required" in obj:
            return obj["decision_required"]
        # Default: decision required in guided mode at certain steps
        mode = self.get_mode(obj)
        if mode == "guided":
            current_step = self.get_current_step(obj)
            # Decision steps: 7 (concept evaluation), 8 (concept decision),
            # 16 (spec document), 17 (review)
            return current_step in {7, 8, 16, 17}
        return False

    def get_next_actions(self, obj):
        """Get available actions for next step.

        Args:
            obj: DesignSession entity or dict

        Returns:
            List of available action strings
        """
        if hasattr(obj, "next_actions"):
            return obj.next_actions
        if isinstance(obj, dict) and "next_actions" in obj:
            return obj["next_actions"]

        # Default actions based on current step
        current_step = self.get_current_step(obj)
        actions = []

        if current_step < 17:
            actions.append("advance")

        if current_step in {7, 8, 16, 17}:
            actions.append("approve")
            actions.append("request_changes")

        if current_step > 1:
            actions.append("restart_step")

        return actions
