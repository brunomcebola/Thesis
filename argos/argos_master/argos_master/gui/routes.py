"""
This module contains the views for the GUI.
"""

from http import HTTPStatus
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

    response = current_app.test_client().get("/api/nodes/")

    if response.status_code == HTTPStatus.OK:
        content = [
            {
                "title": entry["name"],
                "description": entry["address"],
                "src": f"/api/nodes/{entry['id']}/image" if entry["has_image"] else None,
                "zoom": False,
                "redirect": f"/nodes/{entry['id']}",
            }
            for entry in response.get_json()
        ]
    else:
        content = []

    return render_template("views/nodes.jinja", content=content)


@blueprint.route("/nodes/<int:node_id>")
def node(node_id: int):
    """
    The node view
    """

    response = current_app.test_client().get(f"/api/nodes/{node_id}/cameras")

    if response.status_code == HTTPStatus.OK:
        content = [
            {
            "title": entry,
            "src": "/gui/static/images/realsense.png",
            "redirect": f"/nodes/{node_id}/cameras/{entry}",
            }
            for entry in response.get_json()
        ]
        return render_template("views/cameras.jinja", content=content)
    elif response.status_code == HTTPStatus.NOT_FOUND:
        return render_template("views/404.jinja"), 404
    else:
        return render_template("views/500.jinja"), 500

@blueprint.route("/nodes/<int:node_id>/cameras/<camera_id>")
def camera(node_id, camera_id):
    """
    The camera view
    """

    response = current_app.test_client().get(f"/api/nodes/{node_id}/cameras")

    if response.status_code == HTTPStatus.OK and camera_id in response.get_json():
        return render_template("views/camera.jinja")
    else:
        return render_template("views/404.jinja"), 404

@blueprint.route("/areas")
def areas():
    """
    The areas view
    """
    return render_template("views/areas.jinja")


@blueprint.route("/datasets/", defaults={"subpath": ""})
@blueprint.route("/datasets/<path:subpath>/")
def datasets(subpath):
    """
    The datasets view
    """

    response = current_app.test_client().get(f"/api/datasets/{subpath + '/' if subpath else ''}")

    if response.status_code == HTTPStatus.OK:
        content = response.get_json()
    else:
        content = []

    # dataset_data = {
    #     "name": json["name"],
    #     "images": [
    #         {
    #             "src": image,
    #             "description": f"{i + 1}/{len(json['images'])} - {image.split('/')[-1]}",
    #         }
    #         for i, image in enumerate(json["images"])
    #     ],
    # }

    return render_template("views/datasets.jinja", content=content)
