"""
This module contains the views for the GUI.
"""

from http import HTTPStatus
from flask import Blueprint, render_template, current_app, request, redirect, url_for

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
    if request.path.endswith("/"):
        new_url = request.path.rstrip("/")

        # Create a MapAdapter for matching the new URL
        map_adapter = current_app.url_map.bind("", url_scheme=request.scheme)

        try:
            # Try to match the new URL (without the trailing slash) to a route
            map_adapter.match(new_url, method=request.method)
            # If it matches, redirect to the new URL
            return redirect(new_url, code=301)
        except Exception: # pylint: disable=broad-exception-caught
            # If no match, continue to handle as normal (possibly 404)
            pass

    return render_template("views/404.jinja"), 404


@blueprint.route("/")
def index():
    """
    The index view
    """
    return redirect(url_for("gui.nodes"))


#
# Nodes
#


@blueprint.route("/nodes")
def nodes():
    """
    The nodes view
    """

    response = current_app.test_client().get("/api/nodes/")

    if response.status_code == HTTPStatus.OK:
        content = [
            {
                "cardId": f"n{entry['id']}",
                "cardTitle": entry["name"],
                "cardDescription": entry["address"],
                "imgSrc": f"/api/nodes/{entry['id']}/image" if entry["has_image"] else "",
                "imgAlt": f"{entry['name']} node cover",
                "redirectURL": f"/nodes/{entry['id']}/cameras",
            }
            for entry in response.get_json()
        ]
    else:
        content = []

    return render_template("views/nodes.jinja", content=content)


@blueprint.route("/nodes/<int:node_id>")
def redirect_to_node_cameras(node_id: int):
    """
    Redirect to the nodo_cameras view
    """
    return redirect(url_for("gui.node_cameras", node_id=node_id))

@blueprint.route("/nodes/<int:node_id>/cameras")
def node_cameras(node_id: int):
    """
    The cameras view
    """

    response = current_app.test_client().get(f"/api/nodes/{node_id}/cameras")

    if response.status_code == HTTPStatus.OK:
        content = []
        for entry in response.get_json():
            if current_app.test_client().get(f"/api/nodes/{node_id}/cameras/{entry}/status").status_code == HTTPStatus.OK:
                entry_status = "Operational"
            else:
                entry_status = "Not operational"

            content.append({
                "cardId": f"c{entry}",
                "cardTitle": entry,
                "cardDescription": entry_status,
                "imgSrc": "/gui/static/images/realsense.png",
                "imgAlt": f"Camera {entry} cover",
                "redirectURL": f"/nodes/{node_id}/cameras/{entry}",
            })

        return render_template("views/cameras.jinja", content=content)
    elif response.status_code == HTTPStatus.NOT_FOUND:
        return render_template("views/404.jinja"), 404
    else:
        return render_template("views/500.jinja"), 500


@blueprint.route("/nodes/<int:node_id>/logs")
def node_logs(node_id: int):  # pylint: disable=unused-argument
    """
    The node logs view
    """
    return render_template("views/logs.jinja")


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


#
# Areas
#


@blueprint.route("/areas")
def areas():
    """
    The areas view
    """
    return render_template("views/areas.jinja")


#
# Datasets
#


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


#
# Logs
#


@blueprint.route("/logs")
def logs():
    """
    The logs view
    """
    return render_template("views/logs.jinja")
