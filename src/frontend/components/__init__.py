"""
Frontend Components Package

Task 4: app_hybrid.py Refactoring
Provides modular UI components for the Jigyokei application.
"""

from src.frontend.components.onboarding import (
    load_industry_templates,
    get_template_options,
    show_template_preview,
    apply_template_to_plan,
    get_role_nav_target
)

from src.frontend.components.sidebar import (
    calculate_step_progress,
    render_step_wizard,
    render_save_button,
    render_share_button,
    render_batch_import_ui
)

from src.frontend.components.context_help import (
    CONTEXT_HELP,
    get_field_help,
    get_field_example,
    render_help_icon,
    text_input_with_help,
    text_area_with_help,
    show_example_button,
    render_quick_help_panel
)

__all__ = [
    # Onboarding
    "load_industry_templates",
    "get_template_options", 
    "show_template_preview",
    "apply_template_to_plan",
    "get_role_nav_target",
    # Sidebar
    "calculate_step_progress",
    "render_step_wizard",
    "render_save_button",
    "render_share_button",
    "render_batch_import_ui",
    # Context Help (Task 5)
    "CONTEXT_HELP",
    "get_field_help",
    "get_field_example",
    "render_help_icon",
    "text_input_with_help",
    "text_area_with_help",
    "show_example_button",
    "render_quick_help_panel",
]
