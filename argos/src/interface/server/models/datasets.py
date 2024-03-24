"""
This module contains the definition of models related to the datasets.
"""

from ...app import db


class Dataset(db.Model):
    """
    Definition of the Dataset model.
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    path = db.Column(db.String(250), unique=True, nullable=False)
    favourite = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Dataset {self.name}>"


__all__ = ["Dataset"]
