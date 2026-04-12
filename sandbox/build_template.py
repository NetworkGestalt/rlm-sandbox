"""One-time script to build the custom E2B sandbox template."""

from e2b import Template, default_build_logger

from config import SANDBOX_TEMPLATE

template = (
    Template()
    .from_template("code-interpreter-v1")
    .pip_install(["pandas", "numpy", "PyPDF2"])
)

Template.build(
    template,
    SANDBOX_TEMPLATE,
    on_build_logs=default_build_logger(),
)
