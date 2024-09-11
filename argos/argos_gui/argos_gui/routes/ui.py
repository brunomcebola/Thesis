"""
This module contains the views for the
"""

from http import HTTPStatus
from flask import Blueprint, render_template, current_app, request, redirect, url_for

blueprint = Blueprint("ui", __name__)


@blueprint.route("/<path:subpath>")
def page_not_found(subpath):  # pylint: disable=unused-argument
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
            return redirect(new_url, code=302)
        except Exception:  # pylint: disable=broad-exception-caught
            # If no match, continue to handle as normal (possibly 404)
            pass

    return render_template("views/404.jinja"), 404


@blueprint.route("/")
def index():
    """
    The index view
    """
    return redirect(url_for("ui.nodes"))


#
# Nodes
#


@blueprint.route("/nodes")
def nodes():
    """
    The nodes view
    """

    response = current_app.test_client().get("/api/nodes")

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
    return redirect(url_for("ui.node_cameras", node_id=node_id))


@blueprint.route("/nodes/<int:node_id>/cameras")
def node_cameras(node_id: int):
    """
    The cameras view
    """

    response = current_app.test_client().get(f"/api/nodes/{node_id}/cameras")

    if response.status_code == HTTPStatus.OK:
        content = []
        for entry in response.get_json():
            if (
                current_app.test_client()
                .get(f"/api/nodes/{node_id}/cameras/{entry}/status")
                .status_code
                == HTTPStatus.OK
            ):
                entry_status = "Operational"
            else:
                entry_status = "Not operational"

            content.append(
                {
                    "cardId": f"c{entry}",
                    "cardTitle": entry,
                    "cardDescription": entry_status,
                    "imgSrc": "/static/images/realsense.png",
                    "imgAlt": f"Camera {entry} cover",
                    "redirectURL": f"/nodes/{node_id}/cameras/{entry}",
                }
            )

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


@blueprint.route("/datasets")
def datasets():
    """
    The datasets view
    """

    response = current_app.test_client().get("/api/datasets")

    if response.status_code == HTTPStatus.OK:
        content = [
            {
                "itemId": f"d{entry}",
                "itemTitle": entry,
                "itemRedirectURL": f"/datasets/{entry}",
            }
            for entry in response.get_json()
        ]
    else:
        content = []

    print(content)

    return render_template("views/datasets.jinja", content=content)


@blueprint.route("/datasets/<string:dataset_name>")
def dataset(dataset_name: str):
    """
    The dataset view
    """

    # set data argument to raw if it is not set
    if request.args.get("data") is None:
        request.args = request.args.copy()  # type: ignore
        request.args["data"] = "raw"

    # set type argument to color if it is not set
    if request.args.get("type") is None:
        request.args = request.args.copy()  # type: ignore
        request.args["type"] = "color"

    response = current_app.test_client().get(
        f"/api/datasets/{dataset_name}/{request.args['data']}_images?type={request.args['type']}"
    )

    if response.status_code == HTTPStatus.OK:
        response = response.get_json()
        total = len(response)

        content = [
            {
                "cardId": f"iraw{i}",
                "cardDescription": f"{i}/{total}: {entry}",
                "imgSrc": f"/api/datasets/{dataset_name}/raw_images/{entry}",
                "imgAlt": f"Image {entry} cover",
            }
            for i, entry in enumerate(response, 1)
        ]

    else:
        content = []

    print(content)

    return render_template("views/dataset.jinja", content=content)


# @blueprint.route("/datasets/", defaults={"subpath": ""})
# @blueprint.route("/datasets/<path:subpath>/")
# def datasets(subpath):
#     """
#     The datasets view
#     """

#     response = current_app.test_client().get(f"/api/datasets/{subpath + '/' if subpath else ''}")

#     if response.status_code == HTTPStatus.OK:
#         content = response.get_json()
#     else:
#         content = []

#     # dataset_data = {
#     #     "name": json["name"],
#     #     "images": [
#     #         {
#     #             "src": image,
#     #             "description": f"{i + 1}/{len(json['images'])} - {image.split('/')[-1]}",
#     #         }
#     #         for i, image in enumerate(json["images"])
#     #     ],
#     # }

#     return render_template("views/datasets.jinja", content=content)


#
# Logs
#


@blueprint.route("/logs")
def logs():
    """
    The logs view
    """
    return render_template("views/logs.jinja")
