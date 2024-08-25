"""
Init file for the assets module.
"""

from flask_assets import Environment, Bundle

from .. import app


assets = Environment(app)

# Define SCSS bundle with minification and source maps in production
scss_bundle = Bundle(
    "../assets/scss/main.scss",  # Source SCSS file
    filters=["pyscss", "cssmin", "cssrewrite"],
    output="css/main.min.css",  # Minified CSS output
    extra={"rel": "stylesheet/scss"},
)

# Define JS bundle with minification and source maps in production
js_bundle = Bundle(
    "../assets/js/main.js",  # Source JavaScript file
    filters=["jsmin"],
    output="js/main.min.js",  # Minified JS output
    extra={"rel": "text/javascript"},
)

# Register the bundles
assets.register("scss_all", scss_bundle)
assets.register("js_all", js_bundle)
