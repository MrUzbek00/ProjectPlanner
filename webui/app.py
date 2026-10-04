"""Flask routes. Logic lives in data.py and method.py; this file only wires pages."""

from __future__ import annotations

import re
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for
from markupsafe import Markup, escape

from . import REPO_ROOT, method, workflow_map
from .data import ProjectError, ProjectView, Registry

ID_RE = re.compile(r"\b(?:GOAL|BR|RULE|FR|NFR|DR|IR|SR|UXR|TR|ADR|TASK)-(?:[A-Z][A-Z0-9]{1,11}-)?[0-9]{3,}(?:-S[0-9]{2,})?\b")

GOOD = {"PASS", "READY", "ACCEPTED", "APPROVED", "IN_SCOPE", "COVERED", "RESOLVED", "ANSWERED", "CLOSED",
        "READY_FOR_HANDOFF", "VALID", "DECIDED", "TRUE", "DONE", "CONFIRMED_LINK", "CURRENT", "PASSED"}
WARN = {"PASS_WITH_WARNINGS", "NEEDS_REVIEW", "NEEDS_DISCOVERY", "PARTIALLY_READY", "PROPOSED", "CONFIRMED",
        "PENDING_DECISION", "MINOR", "OBSERVATION", "MEDIUM", "ACKNOWLEDGED", "IN_RESOLUTION", "ACCEPTED_RISK",
        "DRAFT", "DECISION_REQUIRED", "DELEGATED", "NOT_READY", "STALE", "MITIGATING", "UNDER_ANALYSIS",
        "LIKELY", "ASSUMPTION", "DEFERRED", "FUTURE"}
BAD = {"FAIL", "BLOCKED", "REJECTED", "INVALID", "CRITICAL", "MAJOR", "BLOCKER", "HIGH", "FALSE",
       "SUPERSEDED", "DEPRECATED", "OUT_OF_SCOPE", "UNKNOWN", "OCCURRED"}

PROJECT_TABS = [("overview", "Overview"), ("requirements", "Requirements"), ("architecture", "Architecture"),
                ("backlog", "Backlog"), ("traceability", "Traceability"), ("review", "Spec review"),
                ("changes", "Changes"), ("decisions", "Decisions & risks"), ("handoff", "Handoff")]


def badge_class(value) -> str:
    key = re.sub(r"[\s-]+", "_", str(value).strip()).upper()
    if key in GOOD:
        return "good"
    if key in BAD:
        return "bad"
    if key in WARN:
        return "warn"
    return "muted"


def humanize(value) -> str:
    text = str(value if value not in (None, "") else "—")
    return text.replace("_", " ") if re.fullmatch(r"[a-z_]+|[A-Z_]+", text) else text


def create_app(registry: Registry) -> Flask:
    app = Flask(__name__)
    app.config["REGISTRY"] = registry

    # -- template helpers ---------------------------------------------------
    @app.template_filter("badge")
    def badge(value, label=None) -> Markup:
        shown = humanize(label if label is not None else value)
        return Markup(f'<span class="badge {badge_class(value)}">{escape(shown)}</span>')

    @app.template_filter("human")
    def human(value) -> str:
        return humanize(value)

    @app.template_filter("label")
    def label(key: str) -> str:
        return str(key)[:1].upper() + str(key)[1:]

    @app.template_global()
    def linkify(text, view: ProjectView | None = None) -> Markup:
        """Escape text, then turn known record IDs into links to their pages."""
        escaped = str(escape("" if text is None else text))
        if view is None:
            return Markup(escaped)

        def link(match: re.Match) -> str:
            identifier = match.group(0)
            kind = view.index.get(identifier)
            endpoint = {"requirement": "requirement", "adr": "adr", "task": "task"}.get(kind)
            if not endpoint:
                return identifier
            href = url_for(endpoint, slug=view.project.slug, item_id=identifier)
            title = escape(view.title_of(identifier))
            return f'<a class="rid" href="{href}" title="{title}">{identifier}</a>'

        return Markup(ID_RE.sub(link, escaped))

    @app.template_global()
    def ids(values, view: ProjectView | None = None) -> Markup:
        values = [v for v in (values or []) if v]
        if not values:
            return Markup('<span class="muted-text">—</span>')
        return Markup(" ".join(f'<span class="chip">{linkify(v, view)}</span>' for v in values))

    # -- helpers ------------------------------------------------------------
    def project_view(slug: str) -> ProjectView | ProjectError:
        project = registry.get(slug)
        if project is None:
            abort(404)
        return registry.load(project)

    def page(slug: str, tab: str, template: str, **context):
        view = project_view(slug)
        if isinstance(view, ProjectError):
            return render_template("project_error.html", error=view, tabs=PROJECT_TABS, tab=tab)
        return render_template(template, v=view, tabs=PROJECT_TABS, tab=tab, **context)

    def item_page(slug: str, tab: str, template: str, lookup: str, item_id: str):
        view = project_view(slug)
        if isinstance(view, ProjectError):
            return render_template("project_error.html", error=view, tabs=PROJECT_TABS, tab=tab)
        item = getattr(view, lookup)(item_id)
        if item is None:
            abort(404)
        return render_template(template, v=view, item=item, tabs=PROJECT_TABS, tab=tab)

    # -- method -------------------------------------------------------------
    @app.route("/")
    def home():
        cards = [(p, registry.load(p)) for p in registry.projects()]
        stages, _ = method.stages()
        wanted = request.args.get("project")
        views = [v for _, v in cards if isinstance(v, ProjectView)]
        if wanted == "none":
            view = None
        else:
            view = next((v for v in views if v.project.slug == wanted), None) or (views[0] if views else None)
        wmap = workflow_map.build(
            view,
            stage_href=lambda number: url_for("method_stage", number=number),
            project_href=(lambda gate: url_for("overview", slug=view.project.slug) + f"#gate-{gate}") if view else None,
        )
        return render_template("home.html", cards=cards, stage_count=len({s.number for s in stages}),
                               projects_dir=registry.projects_dir, view=view, wmap=wmap, tabs=PROJECT_TABS)

    @app.route("/method")
    def method_overview():
        stages, continuous = method.stages()
        return render_template("method.html", stages=stages, continuous=continuous, tools=method.tools())

    @app.route("/method/stages/<int:number>")
    def method_stage(number: int):
        section = method.stage_section(number)
        if section is None:
            abort(404)
        title, body = section
        stages, _ = method.stages()
        here = [s for s in stages if s.number == number]
        html = method.render_markdown(body, lambda name: url_for("method_template", name=name))
        return render_template("method_stage.html", title=title, html=html, stages=here, number=number,
                               last=max(s.number for s in stages))

    @app.route("/method/templates/<name>")
    def method_template(name: str):
        text = method.template_document(name)
        if text is None:
            abort(404)
        html = method.render_markdown(text, lambda n: url_for("method_template", name=n))
        return render_template("method_template.html", name=name, html=html, files=method.template_files())

    # -- projects -----------------------------------------------------------
    @app.route("/projects/<slug>")
    def overview(slug):
        return page(slug, "overview", "project/overview.html")

    @app.post("/projects/<slug>/refresh")
    def refresh(slug):
        if registry.get(slug) is None:
            abort(404)
        registry.forget(slug)
        return redirect(url_for("overview", slug=slug))

    @app.route("/projects/<slug>/requirements")
    def requirements(slug):
        return page(slug, "requirements", "project/requirements.html")

    @app.route("/projects/<slug>/requirements/<item_id>")
    def requirement(slug, item_id):
        return item_page(slug, "requirements", "project/requirement.html", "requirement", item_id)

    @app.route("/projects/<slug>/architecture")
    def architecture(slug):
        return page(slug, "architecture", "project/architecture.html")

    @app.route("/projects/<slug>/architecture/<item_id>")
    def adr(slug, item_id):
        return item_page(slug, "architecture", "project/adr.html", "adr", item_id)

    @app.route("/projects/<slug>/backlog")
    def backlog(slug):
        return page(slug, "backlog", "project/backlog.html")

    @app.route("/projects/<slug>/tasks/<item_id>")
    def task(slug, item_id):
        return item_page(slug, "backlog", "project/task.html", "task", item_id)

    @app.route("/projects/<slug>/traceability")
    def traceability(slug):
        return page(slug, "traceability", "project/traceability.html")

    @app.route("/projects/<slug>/review")
    def review(slug):
        return page(slug, "review", "project/review.html")

    @app.route("/projects/<slug>/changes")
    def changes(slug):
        return page(slug, "changes", "project/changes.html")

    @app.route("/projects/<slug>/decisions")
    def decisions(slug):
        return page(slug, "decisions", "project/decisions.html")

    @app.route("/projects/<slug>/handoff")
    def handoff(slug):
        return page(slug, "handoff", "project/handoff.html")

    @app.errorhandler(404)
    def not_found(_):
        return render_template("not_found.html"), 404

    @app.context_processor
    def globals_():
        return {"repo_name": REPO_ROOT.name}

    return app


def default_registry(projects_dir: Path | None = None, extra=None, sample: bool = False) -> Registry:
    return Registry(projects_dir if projects_dir is not None else REPO_ROOT / "projects", extra, sample)
