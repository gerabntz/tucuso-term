"""Tucuso-term Flask app — scaffold (T1). Real routes arrive in T5/T6."""
from flask import Flask

app = Flask(
    __name__,
    template_folder="../web",
    static_folder="../web/static",
)


@app.get("/healthz")
def healthz():
    return {"ok": True}
