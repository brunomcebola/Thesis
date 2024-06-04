"""
This module contains the views for the GUI.
"""

from flask import Blueprint, render_template, current_app

blueprint = Blueprint(
    "gui",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/gui/static",
)


@blueprint.app_errorhandler(404)
def page_not_found(_):
    """
    The 404 view
    """
    return render_template("views/404.jinja"), 404


@blueprint.route("/")
def index():
    """
    The index view
    """
    return render_template("views/index.jinja")


@blueprint.route("/nodes")
def nodes():
    """
    The nodes view
    """
    return render_template("views/nodes.jinja")


@blueprint.route("/areas")
def areas():
    """
    The areas view
    """
    return render_template("views/areas.jinja")


@blueprint.route("/datasets")
def datasets():
    """
    The datasets view
    """

    response = current_app.test_client().get("/api/datasets")

    datasets_list = response.get_json()

    return render_template("views/datasets.jinja", datasets=datasets_list)


@blueprint.route("/dataset/<dataset_name>")
def dataset(dataset_name: str):
    """
    The dataset view
    """

    response = current_app.test_client().get(f"/api/datasets/{dataset_name}")

    dataset_data = response.get_json()

    return render_template("views/dataset.jinja", dataset=dataset_data)
