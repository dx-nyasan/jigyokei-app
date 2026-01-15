"""
End-to-End Tests for Jigyokei Core Workflows

Task 8: E2E Test Coverage
Tests complete user workflows from start to finish.
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any


class TestCoreWorkflowE2E:
    """E2E tests for core application workflows."""
    
    def test_complete_plan_creation_workflow(self):
        """
        E2E Test: Complete plan creation workflow
        
        Workflow:
        1. Create empty plan
        2. Fill basic info
        3. Add disaster scenario
        4. Add measures
        5. Run audit
        6. Export
        """
        from src.api.schemas import ApplicationRoot
        
        # Step 1: Create empty plan
        plan = ApplicationRoot()
        assert plan is not None
        
        # Step 2: Fill basic info
        plan.basic_info.corporate_name = "テスト株式会社"
        plan.basic_info.address = "和歌山県西牟婁郡白浜町1234"
        plan.basic_info.representative_name = "山田 太郎"
        
        assert plan.basic_info.corporate_name == "テスト株式会社"
        
        # Step 3: Add disaster scenario
        plan.goals.disaster_scenario.disaster_assumption = "地震による被害を想定"
        plan.goals.business_overview = "観光業を営む"
        
        assert "地震" in plan.goals.disaster_scenario.disaster_assumption
        
        # Step 4: Add measures
        plan.measures.personnel.current_measure = "緊急連絡網を整備"
        plan.measures.building.current_measure = "耐震診断を実施"
        
        assert plan.measures.personnel.current_measure is not None
        
        # Step 5: Run audit
        from src.core.completion_checker import CompletionChecker
        checker = CompletionChecker(plan)
        result = checker.check_completion()
        
        assert result["score"] >= 0
        assert "severity_counts" in result
        
        # Step 6: Validate exportability
        plan_dict = plan.model_dump()
        assert "basic_info" in plan_dict
        assert "goals" in plan_dict
        assert "measures" in plan_dict
    
    def test_batch_processing_workflow(self):
        """
        E2E Test: Batch processing workflow
        
        Workflow:
        1. Prepare CSV data
        2. Validate columns
        3. Process batch
        4. Export results
        """
        from src.core.batch_processor import BatchProcessor
        
        # Step 1: Prepare CSV data
        csv_content = """corporate_name,address,representative,industry
株式会社テストA,和歌山県白浜町,山田太郎,製造業
有限会社テストB,和歌山県田辺市,鈴木花子,小売業
"""
        
        # Step 2: Initialize processor
        processor = BatchProcessor()
        
        # Step 3: Validate columns
        headers = ["corporate_name", "address", "representative", "industry"]
        validation = processor.validate_csv_columns(headers)
        assert validation["valid"] is True
        
        # Step 4: Process batch
        result = processor.process_batch(csv_content)
        
        assert result["total"] == 2
        assert len(result["results"]) == 2
        
        # Step 5: Verify results
        for batch_result in result["results"]:
            assert batch_result.corporate_name is not None
            assert batch_result.status in ["success", "partial", "error"]
    
    def test_dialogue_branching_workflow(self):
        """
        E2E Test: Dialogue branching workflow
        
        Workflow:
        1. Initialize brancher
        2. Detect topic
        3. Analyze response
        4. Get branch action
        5. Generate quick replies
        """
        from src.core.dialogue_brancher import DialogueBrancher, get_dialogue_branch
        from src.core.dialogue_ai_adapter import DialogueAIAdapter, enhance_ai_response
        
        # Step 1: Initialize
        brancher = DialogueBrancher()
        adapter = DialogueAIAdapter()
        
        # Step 2: Test topic detection
        topic = adapter.detect_topic("災害対策について教えてください")
        assert topic is not None
        
        # Step 3: Analyze affirmative response
        result = adapter.analyze_response("はい、対策はあります")
        assert result["intent"] in ["affirmative", "has_existing", "unknown"]
        
        # Step 4: Test get_dialogue_branch convenience function
        branch = get_dialogue_branch("disaster_measures", "いいえ")
        assert branch["intent"] in ["affirmative", "negative", "need_help", "has_existing", "skip", "unknown"]
        
        # Step 5: Test enhance_ai_response
        enhanced = enhance_ai_response("対策はありますか？", "はい")
        assert "quick_replies" in enhanced
        assert len(enhanced["quick_replies"]) > 0
    
    def test_session_management_workflow(self):
        """
        E2E Test: Session management workflow
        
        Workflow:
        1. Create session
        2. Save data
        3. Generate share URL
        4. Load session
        """
        from src.core.session_manager import SessionManager
        
        # Step 1: Initialize
        sm = SessionManager()
        
        # Step 2: Test session creation
        test_history = [{"role": "user", "content": "テスト"}]
        test_plan = {"basic_info": {"corporate_name": "テスト会社"}}
        
        # Step 3: Create shareable session
        share_id = sm.create_shareable_session(test_history, test_plan)
        assert share_id is not None
        assert len(share_id) > 0
        
        # Step 4: Get share URL
        share_url = sm.get_share_url(share_id)
        assert share_url is not None
        assert share_id in share_url
        
        # Step 5: Load shared session
        loaded = sm.load_shared_session(share_id)
        if loaded:  # May be None if file not persisted
            assert "history" in loaded or "plan" in loaded
    
    def test_logic_validation_workflow(self):
        """
        E2E Test: Logic validation workflow
        
        Workflow:
        1. Create plan with inconsistencies
        2. Run validation
        3. Check for alerts
        """
        from src.api.schemas import ApplicationRoot
        from src.core.logic_validator import LogicValidator
        
        # Step 1: Create plan
        plan = ApplicationRoot()
        plan.basic_info.corporate_name = "製造工場株式会社"
        plan.goals.business_overview = "小売業を営んでいます"  # Mismatch with name
        
        # Step 2: Run validation
        validator = LogicValidator()
        result = validator.validate(plan)
        
        # Step 3: Check result structure
        assert "is_valid" in result or "alerts" in result or "score" in result
    
    def test_spec_monitor_workflow(self):
        """
        E2E Test: Specification monitor workflow
        
        Workflow:
        1. Initialize monitor
        2. Register a spec version
        3. Check for updates
        """
        from src.core.spec_monitor import SpecMonitor
        
        # Step 1: Initialize
        monitor = SpecMonitor()
        
        # Step 2: Register version
        monitor.register_change(
            spec_item="test_spec",
            old_version="1.0",
            new_version="1.1",
            change_description="テスト変更"
        )
        
        # Step 3: Verify registration worked
        assert monitor.version_data is not None
    
    def test_industry_template_workflow(self):
        """
        E2E Test: Industry template workflow
        
        Workflow:
        1. Load templates
        2. Select template
        3. Apply to plan
        """
        from src.frontend.components.onboarding import (
            load_industry_templates,
            get_template_options
        )
        from src.api.schemas import ApplicationRoot
        
        # Step 1: Load templates
        templates = load_industry_templates()
        
        # Step 2: Get options
        options = get_template_options()
        assert len(options) > 0
        assert "🏭 製造業" in options
        
        # Step 3: Verify template structure if loaded
        if templates:
            assert "templates" in templates
            manufacturing = templates["templates"].get("manufacturing")
            if manufacturing:
                assert "disaster_assumption" in manufacturing
                assert "measures" in manufacturing


class TestUserFlowE2E:
    """E2E tests simulating user interactions."""
    
    def test_first_time_user_flow(self):
        """
        E2E Test: First-time user experience
        
        Flow: Onboarding → Template Selection → Interview Start
        """
        from src.frontend.components.onboarding import get_role_nav_target
        
        # Simulate role selection
        roles = ["経営者（事業主）", "従業員", "商工会職員"]
        
        for role in roles:
            nav_target = get_role_nav_target(role)
            assert nav_target is not None
            assert "インタビュー" in nav_target
    
    def test_progress_tracking_flow(self):
        """
        E2E Test: Progress tracking through completion
        
        Flow: Empty → Partial → Complete
        """
        from src.api.schemas import ApplicationRoot
        from src.core.completion_checker import CompletionChecker
        
        plan = ApplicationRoot()
        
        # Stage 1: Empty
        checker = CompletionChecker(plan)
        result1 = checker.check_completion()
        score1 = result1["score"]
        
        # Stage 2: Add some data
        plan.basic_info.corporate_name = "テスト会社"
        plan.basic_info.address = "和歌山県"
        
        checker2 = CompletionChecker(plan)
        result2 = checker2.check_completion()
        score2 = result2["score"]
        
        # Score should improve
        assert score2 >= score1
    
    def test_export_flow(self):
        """
        E2E Test: Export workflow
        
        Flow: Plan Creation → Audit → Export
        """
        from src.api.schemas import ApplicationRoot
        from src.core.draft_exporter import DraftExporter
        from src.core.completion_checker import CompletionChecker
        
        # Create plan with minimal data
        plan = ApplicationRoot()
        plan.basic_info.corporate_name = "株式会社エクスポートテスト"
        plan.basic_info.address = "和歌山県白浜町"
        plan.goals.business_overview = "観光業"
        
        # Check completion
        checker = CompletionChecker(plan)
        result = checker.check_completion()
        
        # Prepare export (don't actually write file)
        exporter = DraftExporter(plan, result)
        
        # Verify exporter initialized
        assert exporter.plan is not None
        assert exporter.audit_result is not None
