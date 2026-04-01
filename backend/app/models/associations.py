from ..extensions import db

ressource_categorie = db.Table(
    "ressource_categorie",
    db.Column(
        "ressource_id",
        db.Integer,
        db.ForeignKey("ressource.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "categorie_id",
        db.Integer,
        db.ForeignKey("categorie.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
